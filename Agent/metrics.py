import numpy as np
import pandas as pd

def compute_equity_curve(trades, initial_cash):
    equity = [initial_cash]
    cash = initial_cash

    for t in trades:
        cash += t["pnl"]
        equity.append(cash)

    return np.array(equity)


def max_drawdown(equity):
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    return dd.min()


def volatility(equity):
    returns = np.diff(equity) / equity[:-1]
    return np.std(returns) * np.sqrt(252)


def sharpe_ratio(equity, risk_free=0.0):
    returns = np.diff(equity) / equity[:-1]
    if returns.std() == 0:
        return 0
    return (returns.mean() - risk_free) / returns.std() * np.sqrt(252)


def profit_per_trade(trades):
    if len(trades) == 0:
        return 0
    return np.mean([t["pnl"] for t in trades])


def summarize(trades, initial_cash):
    equity = compute_equity_curve(trades, initial_cash)

    return {
        "profit_total": equity[-1] - initial_cash,
        "max_drawdown": max_drawdown(equity),
        "volatility": volatility(equity),
        "sharpe": sharpe_ratio(equity),
        "profit_per_trade": profit_per_trade(trades),
        "num_trades": len(trades)
    }
