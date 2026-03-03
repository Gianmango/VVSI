import numpy as np
import pandas as pd

def _holding_days(trades):
    days = []
    for t in trades:
        entry = t.get("entry_date")
        exit_ = t.get("exit_date")
        if entry is None or exit_ is None:
            continue
        try:
            d0 = pd.to_datetime(entry)
            d1 = pd.to_datetime(exit_)
            delta = (d1 - d0).days
            if delta >= 0:
                days.append(delta)
        except Exception:
            continue
    return days

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

    final_cash = float(equity[-1]) if len(equity) else float(initial_cash)
    yield_pct = (final_cash - float(initial_cash)) / float(initial_cash) * 100.0
    holding_days = _holding_days(trades)
    avg_holding_days = float(np.mean(holding_days)) if holding_days else 0.0

    return {
        "initial_cash": float(initial_cash),
        "final_cash": final_cash,
        "yield_pct": yield_pct,
        "profit_total": equity[-1] - initial_cash,
        "max_drawdown": max_drawdown(equity),
        "volatility": volatility(equity),
        "sharpe": sharpe_ratio(equity),
        "profit_per_trade": profit_per_trade(trades),
        "num_trades": len(trades),
        "avg_holding_days": avg_holding_days,
    }
