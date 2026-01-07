import itertools
import pandas as pd
import numpy as np
import os
from datetime import datetime
from functools import lru_cache
from universe import load_valid_symbols, fetch_prices_for_window, build_daily_universe
from portfolio import Portfolio
from agent import simulate_day
from metrics import summarize
from config import *


@lru_cache(maxsize=1)
def _valid_symbols_cached():
    return tuple(load_valid_symbols())


# Cache globali
_API_DF_CACHE = {}
_LOCAL_BASE_CACHE = {}
_LOCAL_WINDOW_CACHE = {}
_COMBINED_DF_CACHE = {}
_UNIVERSE_CACHE = {}     


def _fetch_api_cached(symbol, window):
    key = (symbol, window)
    if key in _API_DF_CACHE:
        return _API_DF_CACHE[key]
    try:
        df = fetch_prices_for_window(symbol, window)
    except Exception:
        df = None
    if df is not None and not df.empty:
        _API_DF_CACHE[key] = df
    else:
        _API_DF_CACHE[key] = None
    return _API_DF_CACHE[key]


def _load_local_base_df(symbol, data_dir):
    if symbol in _LOCAL_BASE_CACHE:
        return _LOCAL_BASE_CACHE[symbol]

    path = os.path.join(data_dir, f"{symbol}.csv")
    if not os.path.exists(path):
        _LOCAL_BASE_CACHE[symbol] = None
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        if first_line.startswith("Price,"):
            df = pd.read_csv(
                path,
                skiprows=3,
                names=["Date", "Adj Close", "Close", "High", "Low", "Open", "Volume"],
            )
        else:
            df = pd.read_csv(path)

        if "Date" not in df.columns:
            first_col = df.columns[0] if len(df.columns) else None
            if first_col is not None and str(first_col).startswith("Unnamed"):
                df = df.rename(columns={first_col: "Date"})
        if "Date" not in df.columns:
            _LOCAL_BASE_CACHE[symbol] = None
            return None

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df.rename(columns={
            "Open": "open_price",
            "High": "high",
            "Low": "low",
            "Close": "close_price",
            "Adj Close": "adj_close",
            "Volume": "volume",
        })

        required = ["open_price", "high", "low", "close_price", "adj_close", "volume"]
        if any(c not in df.columns for c in required):
            _LOCAL_BASE_CACHE[symbol] = None
            return None

        df = df.sort_values("Date")
        _LOCAL_BASE_CACHE[symbol] = df[["Date", *required]].copy()
        return _LOCAL_BASE_CACHE[symbol]
    except Exception:
        _LOCAL_BASE_CACHE[symbol] = None
        return None


def _load_local_window_df(symbol, window, data_dir):
    key = (symbol, window)
    if key in _LOCAL_WINDOW_CACHE:
        return _LOCAL_WINDOW_CACHE[key]

    base = _load_local_base_df(symbol, data_dir)
    if base is None or base.empty:
        _LOCAL_WINDOW_CACHE[key] = None
        return None

    df = base.copy()
    close = pd.to_numeric(df["close_price"], errors="coerce")
    close = close.where(close > 0)
    geom = np.exp(np.log(close).rolling(window=window, min_periods=1).mean())
    df[f"geom_mean_{window}"] = geom
    df[f"geom_mean_{window}"] = df[f"geom_mean_{window}"].where(
        ~df[f"geom_mean_{window}"].isna(), df["close_price"]
    )

    df = df.assign(symbol=symbol)
    df = df.rename(columns={"Date": "date"})
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    out = df[[
        "symbol",
        "date",
        "open_price",
        "high",
        "low",
        "close_price",
        "adj_close",
        "volume",
        f"geom_mean_{window}",
    ]]
    _LOCAL_WINDOW_CACHE[key] = out
    return out


def generate_param_grid():
    if TEST_MODE:
        return list(itertools.product(
            TEST_WINDOWS,
            TEST_LEVERS,
            TEST_TP,
            TEST_SL,
            TEST_DP,
            TEST_CAPITAL_PER_TRADE,
        ))
    else:
        return list(itertools.product(
            WINDOWS,
            LEVERS,
            TP_MULT,
            SL_PCT,
            DP_PCT,
            CAPITAL_PER_TRADE_CASES,
        ))


def get_combined_df_and_universe(valid_symbols, window, data_dir):
    cache_key = (tuple(valid_symbols), window)
    
    if cache_key in _UNIVERSE_CACHE:
        return _UNIVERSE_CACHE[cache_key]
    
    all_data = []
    
    for symbol in valid_symbols:
        df = _fetch_api_cached(symbol, window)
        if df is not None and not df.empty:
            all_data.append(df)
        else:
            df = _load_local_window_df(symbol, window, data_dir)
            if df is not None and not df.empty:
                all_data.append(df)
    
    if not all_data:
        _UNIVERSE_CACHE[cache_key] = (None, None, None)
        return None, None, None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    universe = build_daily_universe(combined_df, valid_symbols, window)
    
    if not universe:
        _UNIVERSE_CACHE[cache_key] = (None, None, None)
        return None, None, None
    
    universe_by_date = {}
    for entry in universe:
        d = entry["date"]
        sym = entry["symbol"]
        universe_by_date.setdefault(d, {})[sym] = entry
    
    dates = sorted(universe_by_date.keys())
    
    _UNIVERSE_CACHE[cache_key] = (combined_df, universe_by_date, dates)
    return combined_df, universe_by_date, dates


def run_single(window, leverage, tp, sl, dp, capital_per_trade, valid_symbols=None, verbose=False):
    """Versione ultra-ottimizzata con cache aggressive"""
    
    if valid_symbols is None:
        valid_symbols = list(_valid_symbols_cached())

    if not valid_symbols:
        return _empty_result(window, leverage, tp, sl, dp, capital_per_trade)
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    combined_df, universe_by_date, dates = get_combined_df_and_universe(
        valid_symbols, window, data_dir
    )
    
    if combined_df is None or universe_by_date is None or not dates:
        return _empty_result(window, leverage, tp, sl, dp, capital_per_trade)

    params = {
        "window": window,
        "leverage": leverage,
        "tp": tp,
        "sl": sl,
        "dp": dp,
        "capital_per_trade": capital_per_trade,
    }

    portfolio = Portfolio(cash=INITIAL_CASH)
    last_date = dates[-1]
    
    for date in dates:
        prices = universe_by_date.get(date)
        if prices:
            simulate_day(date, prices, portfolio, params)
    
    if last_date in universe_by_date:
        prices = universe_by_date[last_date]
        for sym in list(portfolio.positions.keys()):
            if sym in prices:
                portfolio.sell(sym, float(prices[sym]["close"]), last_date, "EOD")

    metrics = summarize(portfolio.trades, INITIAL_CASH)
    profit = metrics["profit_total"]
    
    score = (
        0.5 * np.tanh(profit / INITIAL_CASH)
        + 0.4 * (profit / INITIAL_CASH)
        + 0.2 * metrics["sharpe"]
        - 0.1 * abs(metrics["max_drawdown"])
    )

    return {
        **params,
        **metrics,
        "score": score,
    }


def _empty_result(window, leverage, tp, sl, dp, capital_per_trade):
    """Helper per risultati vuoti"""
    return {
        "window": window,
        "leverage": leverage,
        "tp": tp,
        "sl": sl,
        "dp": dp,
        "capital_per_trade": capital_per_trade,
        "profit_total": 0,
        "max_drawdown": 0,
        "volatility": 0,
        "sharpe": 0,
        "profit_per_trade": 0,
        "num_trades": 0,
        "score": -1e9,
    }


def run():
    print(f"\n=== Starting simulation ===")
    
    valid_symbols = list(_valid_symbols_cached())
    
    results = []
    param_combinations = generate_param_grid()
    
    picks_window = {w: 0 for w in sorted(set(p[0] for p in param_combinations))}
    picks_leverage = {l: 0 for l in sorted(set(p[1] for p in param_combinations))}

    for i, (window, leverage, tp, sl, dp, capital_per_trade) in enumerate(param_combinations, 1):
        print(f"[{i}/{len(param_combinations)}] w={window} lev={leverage}x tp={tp}% sl={sl}% dp={dp}% cpt=${capital_per_trade}")
        results.append(run_single(window, leverage, tp, sl, dp, capital_per_trade, valid_symbols, verbose=False))

    df_results = pd.DataFrame(results)
    best = df_results.sort_values("score", ascending=False).groupby("window").first()
    best = best.reset_index()

    for _, row in best.iterrows():
        picks_window[row["window"]] += 1
        picks_leverage[row["leverage"]] += 1

    df_results.to_csv("simulation_results.csv", index=False)


if __name__ == "__main__":
    start_time = datetime.now()
    try:
        run()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
        raise
    finally:
        duration = datetime.now() - start_time
        print(f"\n=== Simulation completed in {duration} ===")