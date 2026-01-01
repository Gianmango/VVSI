import itertools
import pandas as pd
from datetime import datetime
from universe import load_valid_symbols, fetch_prices_for_window, build_daily_universe
from portfolio import Portfolio
from agent import simulate_day
from metrics import summarize
from config import *

def run():
    print(f"\n=== Starting simulation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    valid_symbols = load_valid_symbols()
    results = []
    picks_window = {w: 0 for w in WINDOWS}
    picks_leverage = {l: 0 for l in LEVERS}
    
    # Print configuration
    print("\n=== Simulation Configuration ===")
    print(f"Windows: {WINDOWS}")
    print(f"Leverage: {LEVERS}")
    print(f"Take Profit Multipliers: {TP_MULT}")
    print(f"Stop Loss Percentages: {SL_PCT}")
    print(f"Daily Position Percentages: {DP_PCT}")
    print(f"Base Investment: {BASE_INVEST}")

    for window in WINDOWS:
        print(f"\n--- WINDOW {window} ---")
        df = fetch_prices_for_window(window)
        print(f"Loaded {len(df)} rows for window {window}")
        universe = build_daily_universe(df, valid_symbols)
        print(f"Built universe with {len(universe)} dates")
        dates = sorted(universe.keys())
        print(f"Processing {len(dates)} dates")

        for leverage, tp, sl, dp in itertools.product(LEVERS, TP_MULT, SL_PCT, DP_PCT):

            params = {
                "window": window,
                "leverage": leverage,
                "tp": tp,
                "sl": sl,
                "dp": dp
            }

            OPERATIVE_CAPITAL = BASE_INVEST * params["leverage"]
            
            print(f"\n--- Starting simulation with parameters ---")
            print(f"Window: {window}, Leverage: {leverage}x, TP: {tp}, SL: {sl}%, DP: {dp}%")
            print(f"Operative Capital: ${OPERATIVE_CAPITAL:,.2f}")
            
            portfolio = Portfolio(cash=OPERATIVE_CAPITAL)
            last_print_day = None


            total_days = len(dates)
            for idx, date in enumerate(dates, 1):
                # Print progress every 30 days or on first/last day
                current_date = datetime.strptime(date, '%Y-%m-%d')
                if (last_print_day is None or 
                    (current_date - last_print_day).days >= 30 or 
                    idx == 1 or idx == total_days):
                    print(f"\n[{date}] Processing day {idx}/{total_days} ({(idx/total_days)*100:.1f}%)")
                    print(f"  Current portfolio value: ${portfolio.get_total_value():,.2f}")
                    print(f"  Active positions: {len(portfolio.positions)}")
                    last_print_day = current_date
                
                prices = universe[date]
                simulate_day(date, prices, portfolio, params)
                
                # Print any trades that occurred today
                if portfolio.trades and portfolio.trades[-1]['date'] == date:
                    last_trade = portfolio.trades[-1]
                    action = "BOUGHT" if last_trade['action'] == 'buy' else "SOLD"
                    pct_change = ((last_trade['exit_price'] / last_trade['entry_price'] - 1) * 100) if 'exit_price' in last_trade else 0
                    print(f"  {action} {last_trade['symbol']} "
                          f"at ${last_trade.get('entry_price', last_trade.get('exit_price', 0)):.2f} "
                          f"(P/L: {pct_change:+.2f}%)")

            metrics = summarize(portfolio.trades, INITIAL_CASH)
            
            print(f"\n=== Simulation completed for window {window}, leverage {leverage}x ===")
            print(f"Total Trades: {metrics['total_trades']}")
            print(f"Profit: ${metrics['profit_total']:,.2f} ({metrics['profit_pct']:.2f}%)")
            print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"Win Rate: {metrics['win_rate']:.1f}%")
            print(f"Sharpe Ratio: {metrics['sharpe']:.2f}")

            score = (
                0.6 * metrics["sharpe"]
                + 0.3 * np.tanh(metrics["profit_total"] / INITIAL_CASH)
                - 0.1 * abs(metrics["max_drawdown"])
            )

            results.append({
                **params,
                **metrics,
                "score": score
            })

    df_results = pd.DataFrame(results)
    best = df_results.sort_values("score", ascending=False).groupby("window").first()

    for _, row in best.iterrows():
        picks_window[row["window"]] += 1
        picks_leverage[row["leverage"]] += 1

    print("\n=== BEST CONFIG PER WINDOW ===")
    print(best[[
        "profit_total",
        "max_drawdown",
        "volatility",
        "sharpe",
        "profit_per_trade",
        "window",
        "leverage"
    ]])

    print("\n=== WINDOW PICKS ===")
    for w, c in picks_window.items():
        print(f"window {w}: {c}")

    print("\n=== LEVERAGE PICKS ===")
    for l, c in picks_leverage.items():
        print(f"leverage {l}: {c}")

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
