import requests
import functools
import pandas as pd
import os

DATA_DIR = "../../data"  # cartella con i csv scaricati
BASE_URL = "http://localhost:3001"

def load_valid_symbols():
    """
    Usa SOLO i simboli per cui esiste un csv locale
    """
    symbols = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            symbols.append(file.replace(".csv", ""))
    return sorted(symbols)


@functools.lru_cache(maxsize=1)
def _fetch_all_prices():
    """Fetch all prices once and cache the result"""
    print("Fetching price data from API...")
    url = f"{BASE_URL}/v_geom_mean_30?order=date.asc"
    r = requests.get(url)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["date"] = pd.to_datetime(df["date"])
    print(f"Loaded {len(df)} price records")
    return df
def fetch_prices_for_window(window):
    """
    Get prices from cache and filter by window if needed.
    The window parameter is kept for backward compatibility but not used.
    """
    return _fetch_all_prices()


def build_daily_universe(df, valid_symbols):
    """
    Trasforma il dataframe in:
    date -> { symbol -> price_row }
    """
    universe = {}

    for _, row in df.iterrows():
        sym = row["symbol"]
        if sym not in valid_symbols:
            continue

        date = row["date"]
        universe.setdefault(date, {})[sym] = {
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "geom_mean": row["geom_mean"]
        }

    return universe
