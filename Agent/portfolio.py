import random

class Portfolio:
    def __init__(self, cash):
        self.cash = cash
        self.positions = {}   # symbol -> position dict
        self.trades = []

    def can_buy(self, amount):
        return self.cash >= amount

    def buy(self, symbol, price, date, leverage, capital):
        borrowed = capital * leverage

        self.cash -= capital

        self.positions[symbol] = {
            "entry_price": price,
            "date": date,
            "capital": capital,
            "borrowed": borrowed,
            "leverage": leverage
        }

    def sell(self, symbol, price, date, reason):
        pos = self.positions.pop(symbol)

        pnl = (price - pos["entry_price"]) * pos["leverage"]

        self.cash += pos["capital"] + pnl

        self.trades.append({
            "symbol": symbol,
            "entry_date": pos["date"],
            "exit_date": date,
            "entry_price": pos["entry_price"],
            "exit_price": price,
            "leverage": pos["leverage"],
            "pnl": pnl,
            "reason": reason
        })

    def apply_overnight_cost(self):
        for pos in self.positions.values():
            interest = pos["borrowed"] * 0.00033
            self.cash -= interest
