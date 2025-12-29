import pandas as pd
import numpy as np

INPUT_FILE = "metrics/metrics_summary.csv"
OUTPUT_BEST_PER_SYMBOL = "metrics/best_per_symbol.csv"
OUTPUT_GLOBAL_STATS = "metrics/global_stats.csv"

# =============================
# Caricamento risultati
# =============================

df = pd.read_csv(INPUT_FILE)

# Rimuoviamo simulazioni non valide
df = df.dropna(subset=["sharpe_ratio", "max_drawdown"])

# =============================
# Funzione di scoring
# =============================

def compute_score(row):
    return row["profit_total"] / abs(row["max_drawdown"])

df["score"] = df.apply(compute_score, axis=1)

# =============================
# Migliore configurazione per simbolo
# =============================

best_per_symbol = (
    df.sort_values("score", ascending=False)
      .groupby("symbol")
      .first()
      .reset_index()
)

best_per_symbol = best_per_symbol[
    [
        "symbol",
        "profit_total",
        "max_drawdown",
        "volatility",
        "sharpe_ratio",
        "profit_per_trade",
        "window",
        "leverage",
        "score"
    ]
]

best_per_symbol.to_csv(OUTPUT_BEST_PER_SYMBOL, index=False)

print("Migliore configurazione per simbolo salvata.")

# =============================
# Statistiche globali
# =============================

window_picks = best_per_symbol["window"].value_counts().sort_index()
leverage_picks = best_per_symbol["leverage"].value_counts().sort_index()

global_stats = pd.DataFrame({
    "window_picks": window_picks,
    "leverage_picks": leverage_picks
}).fillna(0)

global_stats.to_csv(OUTPUT_GLOBAL_STATS)

print("Statistiche globali salvate.")

# =============================
# Output leggibile a terminale
# =============================

print("\n--- Window selection ---")
for w, c in window_picks.items():
    print(f"window {w} = {c} pick")

print("\n--- Leverage selection ---")
for l, c in leverage_picks.items():
    print(f"leverage {l} = {c} pick")
