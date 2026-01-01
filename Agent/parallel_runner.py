import itertools
import multiprocessing as mp
import pandas as pd

from config import *
from run_simulation import run


def generate_param_grid():
    if TEST_MODE:
        return list(itertools.product(
            TEST_WINDOWS,
            TEST_LEVERS,
            TEST_TP,
            TEST_SL,
            TEST_DP
        ))
    else:
        return list(itertools.product(
            WINDOWS,
            LEVERS,
            TP_MULT,
            SL_PCT,
            DP_PCT
        ))


def worker(params):
    # Unpack parameters
    window, leverage, tp, sl, dp = params
    
    # Update global config with current parameters
    global WINDOWS, LEVERS, TP_MULT, SL_PCT, DP_PCT
    WINDOWS = [window]
    LEVERS = [leverage]
    TP_MULT = [tp]
    SL_PCT = [sl]
    DP_PCT = [dp]
    
    # Run the simulation with current parameters
    return run()


if __name__ == "__main__":
    grid = generate_param_grid()
    print(f"Simulazioni totali: {len(grid)}")

    with mp.Pool(mp.cpu_count() - 1) as pool:
        results = pool.map(worker, grid)

    df = pd.DataFrame(results)
    df.to_csv("results/raw_results.csv", index=False)

    print("Simulazioni completate.")
