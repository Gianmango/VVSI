from config import DAILY_LEVER_COST

class Portfolio:
    def __init__(self, cash):
        self.cash = cash
        self.positions = {}
        self.trades = []      # Solo vendite
        self.all_actions = [] # Tutti gli acquisti e vendite


    def can_buy(self, amount):
        return self.cash >= amount

    def buy(self, symbol, price, date, leverage, capital):
        equity = float(capital)
        notional = equity * float(leverage)
        qty = notional / float(price)
        borrowed = notional - equity

        self.cash -= equity

        self.positions[symbol] = {
            "entry_price": float(price),
            "date": date,
            "equity": equity,
            "notional": notional,
            "qty": qty,
            "borrowed": borrowed,
            "leverage": leverage,
        }

        self.all_actions.append({
            "date": date,
            "action": "BUY",
            "symbol": symbol,
            "price": float(price),
            "qty": qty,
            "equity": equity,
            "notional": notional,
        })

    # Calcola tutto il valore del portfolio
    def get_total_value(self, current_prices=None):
        total = self.cash
        
        if current_prices is not None:
            for symbol, pos in self.positions.items():
                if symbol not in current_prices:
                    total += pos["equity"]
                    continue
                current_price = float(current_prices[symbol])
                position_equity = pos["qty"] * current_price - pos["borrowed"]
                total += position_equity
        
        return total

    def sell(self, symbol, price, date, reason):
        pos = self.positions.pop(symbol)

        exit_price = float(price)
        proceeds = pos["qty"] * exit_price
        position_equity = proceeds - pos["borrowed"]
        pnl = position_equity - pos["equity"]

        self.cash += position_equity

        self.all_actions.append({
            "date": date,
            "action": "SELL",
            "symbol": symbol,
            "price": exit_price,
            "qty": pos["qty"],
            "pnl": pnl,
            "reason": reason,
        })

        self.trades.append({
            "symbol": symbol,
            "entry_date": pos["date"],
            "exit_date": date,
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "leverage": pos["leverage"],
            "pnl": pnl,
            "reason": reason
        })

    def apply_overnight_cost(self):
        for pos in self.positions.values():
            interest = pos["borrowed"] * DAILY_LEVER_COST
            self.cash -= interest
