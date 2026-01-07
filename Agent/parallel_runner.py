import itertools
import multiprocessing as mp
import os
import pandas as pd
from datetime import datetime
import sys
import time

from config import *
from run_simulation import (
    run_single, 
    _valid_symbols_cached, 
    get_combined_df_and_universe,
    _UNIVERSE_CACHE
)


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


def preload_all_universes_sequentially(valid_symbols, windows, data_dir):

    print("\n" + "=" * 70)
    print("FASE 1: PRECARICAMENTO DATI (sequenziale, evita rate limits)")
    print("=" * 70)
    print(f"\nWindows da precaricare: {windows}")
    print("Questo richiederà ~30 min per window, ma viene fatto UNA SOLA VOLTA.\n")
    
    preload_start = datetime.now()
    
    for i, window in enumerate(windows, 1):
        print(f"[{i}/{len(windows)}] Scaricamento window={window}...", end=" ", flush=True)
        start = time.time()
        
        combined_df, universe_by_date, dates = get_combined_df_and_universe(
            valid_symbols, window, data_dir
        )
        
        elapsed = time.time() - start
        
        if combined_df is not None and universe_by_date is not None:
            print(f"  ({elapsed:.1f}s, {len(dates)} date)")
        else:
            print(f"  FALLITO ({elapsed:.1f}s)")
    
    preload_duration = datetime.now() - preload_start
    print(f"\n  Precaricamento completato in {preload_duration}")
    print(f"  Cache in memoria: {len(_UNIVERSE_CACHE)} universi pronti")
    print("=" * 70)
    
    return preload_duration


def worker(args):
    """
    Worker che usa dati GIÀ in cache.
    La cache _UNIVERSE_CACHE è già popolata dal processo padre.
    """
    params, valid_symbols = args
    window, leverage, tp, sl, dp, capital_per_trade = params
    
    try:
        return run_single(
            window, leverage, tp, sl, dp, capital_per_trade, 
            valid_symbols, verbose=False
        )
    except Exception as e:
        print(f"ERROR in worker (w={window}, lev={leverage}): {e}")
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


if __name__ == "__main__":
    start_time = datetime.now()
    
    print("=" * 70)
    print("=== SIMULAZIONE TRADING PARALLELA OTTIMIZZATA ===")
    print("=" * 70)
    
    # [1] Carica simboli
    print("\n[1/6] Caricamento simboli...")
    valid_symbols = list(_valid_symbols_cached())
    print(f"        {len(valid_symbols)} simboli")
    
    # [2] Genera griglia
    print("\n[2/6] Generazione griglia parametri...")
    grid = generate_param_grid()
    print(f"        {len(grid)} combinazioni")
    
    # Breakdown parametri
    windows = sorted(set(p[0] for p in grid))
    leverages = sorted(set(p[1] for p in grid))
    tps = sorted(set(p[2] for p in grid))
    sls = sorted(set(p[3] for p in grid))
    dps = sorted(set(p[4] for p in grid))
    capitals = sorted(set(p[5] for p in grid))
    
    print(f"      - Windows: {windows}")
    print(f"      - Leverages: {leverages}")
    print(f"      - Take Profits: {tps}")
    print(f"      - Stop Loss: {sls}")
    print(f"      - Drawdown Prot: {dps}")
    print(f"      - Capital per trade: {capitals}")
    
    # [3] Precarica dati da interfaccia rest per velocizzare le simulazioni (ma da all'agente solo ciò che richiede)
    print("\n[3/6] Precaricamento dati...")
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    preload_duration = preload_all_universes_sequentially(valid_symbols, windows, data_dir)    
    
    # [4] Esecuzione parallela  
    print("\n[4/5] Preparazione processi...")
    worker_args = [(params, valid_symbols) for params in grid]
    os.makedirs("results", exist_ok=True)
    print(f"        {pool_size} processi pronti")
    
    # [5] Esecuzione simulazioni parallele
    print("\n[5/5] Esecuzione simulazioni parallele...")
    print("=" * 70)
    
    sim_start = datetime.now()
    
    with mp.Pool(pool_size) as pool:
        results = []
        total = len(worker_args)
        
        last_percent = -1
        for i, result in enumerate(pool.imap_unordered(worker, worker_args), 1):
            results.append(result)
            
            percent = int((i / total) * 100)
            if percent != last_percent and percent % 5 == 0:
                elapsed = datetime.now() - sim_start
                print(f"[{percent:3d}%] {i}/{total} | Elapsed: {str(elapsed).split('.')[0]}")
                last_percent = percent
    
    sim_duration = datetime.now() - sim_start
    
    # Analisi risultati
    print("\n" + "=" * 70)
    print("=== ANALISI RISULTATI ===")
    print("=" * 70)
    
    df = pd.DataFrame(results)
    df.to_csv("results/raw_results.csv", index=False)
    print(f"\n  Risultati grezzi: results/raw_results.csv")
    
    # Best overall
    best_overall = df.sort_values("score", ascending=False).iloc[0]
    print("\nMIGLIORE CONFIGURAZIONE:")
    print(f"   Window: {int(best_overall['window'])}")
    print(f"   Leverage: {int(best_overall['leverage'])}x")
    print(f"   TP: {best_overall['tp']:.1f}%")
    print(f"   SL: {best_overall['sl']:.1f}%")
    print(f"   DP: {best_overall['dp']:.1f}%")
    print(f"   Capital: ${int(best_overall['capital_per_trade'])}")
    print(f"   ---")
    print(f"   Profit: ${best_overall['profit_total']:.2f}")
    print(f"   Sharpe: {best_overall['sharpe']:.2f}")
    print(f"   Max DD: {best_overall['max_drawdown']:.2f}%")
    print(f"   Score: {best_overall['score']:.4f}")
    print(f"   Trades: {int(best_overall['num_trades'])}")
    
    # Best per window
    best_per_window = df.sort_values("score", ascending=False).groupby("window").first().reset_index()
    best_per_window.to_csv("results/best_per_window.csv", index=False)
    
    print("\n📊 MIGLIORI PER WINDOW:")
    for _, row in best_per_window.iterrows():
        print(f"   Window {int(row['window']):3d}: Profit=${row['profit_total']:9.2f} | Sharpe={row['sharpe']:5.2f} | Score={row['score']:7.4f}")
    
    print(f"\n  Best per window: results/best_per_window.csv")
    
    # Statistiche
    print("\n📈 STATISTICHE:")
    print(f"   Profit medio: ${df['profit_total'].mean():.2f}")
    print(f"   Profit mediano: ${df['profit_total'].median():.2f}")
    print(f"   Config profittevoli: {(df['profit_total'] > 0).sum()}/{len(df)} ({(df['profit_total'] > 0).sum()/len(df)*100:.1f}%)")
    
    # Top 10
    top10 = df.sort_values("score", ascending=False).head(10)
    top10.to_csv("results/top10.csv", index=False)
    print(f"\n  Top 10: results/top10.csv")
    
    # Timing finale
    total_duration = datetime.now() - start_time
    print("\n" + "=" * 70)
    print(f"⏱️  TIMING:")
    print(f"   - Precaricamento: {preload_duration}")
    print(f"   - Simulazioni: {sim_duration}")
    print(f"   - TOTALE: {total_duration}")
    print(f"⚡ Velocità: {len(results) / sim_duration.total_seconds():.3f} sim/sec")
    print("=" * 70)