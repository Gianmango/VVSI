# Importa tutti i dati da yahoo finance per ogni simbolo presente nella lista del nasdaq (ammesso che sia valido)

import yfinance as yf
import time
import pandas as pd
import os
import random

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR, "data")
os.makedirs(_DATA_DIR, exist_ok=True)

# Copia dal file dei simboli tutti i simboli
df = pd.read_csv(os.path.join(_DATA_DIR, "nasdaq_symbols.csv"))
symbols = df["Symbol"].dropna().astype(str).unique().tolist()

start_date = pd.Timestamp("2000-01-01")
end_date = pd.Timestamp("2025-12-31")
end_download = "2026-01-01"

def _normalize_symbol(sym: str) -> str:
    return sym.strip().replace(".", "-")

def _is_full_range(hist: pd.DataFrame) -> bool:
    if hist is None or hist.empty:
        return False
    idx = pd.to_datetime(hist.index)
    if len(idx) == 0:
        return False
    first = pd.Timestamp(idx.min()).normalize()
    last = pd.Timestamp(idx.max()).normalize()
    return first.year == 2000 and last == end_date

def _download_with_retry(sym: str, retries: int = 5) -> pd.DataFrame:
    last_err = None
    for attempt in range(retries):
        try:
            hist = yf.download(
                sym,
                start=str(start_date.date()),
                end=end_download,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if hist is None or hist.empty:
                return pd.DataFrame()
            hist = hist.loc[str(start_date.date()): str(end_date.date())]
            return hist
        except Exception as e:
            last_err = e
            sleep_s = min(30.0, (2 ** attempt)) + random.random()
            time.sleep(sleep_s)
    raise last_err

saved = 0
rejected = 0
failed = 0

for raw_symbol in symbols:
    symbol = _normalize_symbol(raw_symbol)
    out_path = os.path.join(_DATA_DIR, f"{symbol}.csv")
    try:
        hist = _download_with_retry(symbol)
        if hist.empty:
            rejected += 1
            continue
        if not _is_full_range(hist):
            rejected += 1
            continue

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]
        hist.index.name = "Date"

        hist.to_csv(out_path)
        saved += 1
        time.sleep(0.5)
    except Exception as e:
        failed += 1
        print(f"Errore su {symbol}: {e}")

print(f"Simboli totali: {len(symbols)}")
print(f"CSV salvati: {saved}")
print(f"Scartati: {rejected}")
print(f"Falliti: {failed}")
