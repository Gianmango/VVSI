import random
from config import *

def simulate_day(date, prices, portfolio, params):
    leverage = params["leverage"]
    tp = params["tp"]
    sl = params["sl"]
    dp = params["dp"]

    # ====== SELL PHASE ======
    for symbol in list(portfolio.positions.keys()):
        if symbol not in prices:
            continue

        pos = portfolio.positions[symbol]
        high = prices[symbol]["high"]
        low = prices[symbol]["low"]

        # Take Profit
        if high >= pos["entry_price"] * tp:
            portfolio.sell(
                symbol,
                pos["entry_price"] * tp,
                date,
                "TP"
            )
            continue

        # Stop Loss
        if low <= pos["entry_price"] * (1 - sl):
            portfolio.sell(
                symbol,
                pos["entry_price"] * (1 - sl),
                date,
                "SL"
            )

    # ====== BUY PHASE ======
    buy_candidates = []

    for symbol, p in prices.items():
        if symbol in portfolio.positions:
            continue

        if p["open"] <= (1 - dp) * p["geom_mean"]:
            buy_candidates.append(symbol)

    if not buy_candidates:
        portfolio.apply_overnight_cost()
        return

    capital_per_trade = portfolio.cash * BASE_INVEST
    max_trades = int(portfolio.cash // capital_per_trade)

    for _ in range(max_trades):
        sym = random.choice(buy_candidates)

        if not portfolio.can_buy(capital_per_trade):
            break

        portfolio.buy(
            sym,
            prices[sym]["open"],
            date,
            leverage,
            capital_per_trade
        )

    # ====== OVERNIGHT COST ======
    portfolio.apply_overnight_cost()
