import random
from config import *

def simulate_day(date, prices, portfolio, params):
    leverage = params["leverage"]
    tp = params["tp"]
    sl = params["sl"]
    dp = params["dp"]

    # Pre-calcola per evitare accessi ripetuti
    tp_mult = 1 + tp / 100
    sl_mult = 1 - sl / 100
    dp_mult = 1 - dp / 100

    # ====== SELL PHASE ======
    positions_to_check = list(portfolio.positions.keys())
    
    for symbol in positions_to_check:
        # Check rapido se il simbolo è nei prezzi
        price_data = prices.get(symbol)
        if price_data is None:
            continue

        pos = portfolio.positions[symbol]
        
        # Holding minimo di 1 giorno
        if pos["date"] == date:
            continue
        
        high = price_data["high"]
        low = price_data["low"]
        entry = pos["entry_price"]

        # Take Profit - calcolo ottimizzato
        tp_price = entry * tp_mult
        if high >= tp_price:
            portfolio.sell(symbol, tp_price, date, "TP")
            continue

        # Stop Loss - calcolo ottimizzato
        sl_price = entry * sl_mult
        if low <= sl_price:
            portfolio.sell(symbol, sl_price, date, "SL")

    # ====== BUY PHASE ======
    default_cpt = CAPITAL_PER_TRADE_CASES[0] if "CAPITAL_PER_TRADE_CASES" in globals() and CAPITAL_PER_TRADE_CASES else 1000
    capital_per_trade = params.get("capital_per_trade", default_cpt)
    
    # Check rapido se abbiamo abbastanza cash
    if portfolio.cash < capital_per_trade:
        portfolio.apply_overnight_cost()
        return
    
    max_trades = int(portfolio.cash // capital_per_trade)
    if max_trades == 0:
        portfolio.apply_overnight_cost()
        return

    # Pre-filtra candidati
    buy_candidates = []
    current_positions = portfolio.positions
    
    for symbol, p in prices.items():
        if symbol in current_positions:
            continue

        geom = p.get("geom_mean")
        if geom is None or geom == 0:
            continue

        threshold = dp_mult * geom
        if p["open"] <= threshold:
            buy_candidates.append(symbol)

    # Se non ci sono candidati, esci subito
    if not buy_candidates:
        portfolio.apply_overnight_cost()
        return

    # Se abbiamo pochi candidati, compriamoli tutti
    if len(buy_candidates) <= max_trades:
        for sym in buy_candidates:
            if not portfolio.can_buy(capital_per_trade):
                break
            portfolio.buy(sym, prices[sym]["open"], date, leverage, capital_per_trade)
    else:
        to_buy = random.sample(buy_candidates, min(max_trades, len(buy_candidates)))
        for sym in to_buy:
            if not portfolio.can_buy(capital_per_trade):
                break
            portfolio.buy(sym, prices[sym]["open"], date, leverage, capital_per_trade)

    # ====== OVERNIGHT COST ======
    portfolio.apply_overnight_cost()