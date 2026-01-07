import requests
import pandas as pd
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_SCRIPT_DIR, "..", "..", "data")
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


def fetch_prices_for_window(symbol, window):
    url = f"{BASE_URL}/v_geom_mean_{window}?symbol=eq.{symbol}&order=date.asc"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data)


def build_daily_universe(df, symbols, window):
    universe = []
    geom_col = f"geom_mean_{window}"

    for _, row in df.iterrows():
        universe.append({
            "symbol": row["symbol"],
            "date": row["date"],
            "open": row["open_price"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close_price"],
            "adj_close": row["adj_close"],
            "volume": row["volume"],
            "geom_mean": row[geom_col] if geom_col in row else row["close_price"]
        })
    return universe

