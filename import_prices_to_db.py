import psycopg2
import pandas as pd
import os

conn = psycopg2.connect(
    dbname="nasdaq",
    user="postgres",
    password="password",
    host="localhost",
    port=5432
)
cur = conn.cursor()

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_SCRIPT_DIR, "..", "data")

files = os.listdir(DATA_DIR)

cur.execute("TRUNCATE TABLE prices RESTART IDENTITY CASCADE")
conn.commit()

for filename in files:
    if not filename.endswith(".csv"):
        continue
    symbol = filename.replace(".csv", "")
    path = os.path.join(DATA_DIR, filename)

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
        if "date" in df.columns:
            df = df.rename(columns={"date": "Date"})
        else:
            first_col = df.columns[0] if len(df.columns) else None
            if first_col is not None and (str(first_col).startswith("Unnamed") or str(first_col).lower() in {"index"}):
                df = df.rename(columns={first_col: "Date"})

    # rinomina le colonne correttamente
    df = df.rename(columns={
        "Open": "Open_price",
        "Close": "Close_price",
    })

    if "Adj Close" not in df.columns and "AdjClose" in df.columns:
        df = df.rename(columns={"AdjClose": "Adj Close"})

    # converti Date in datetime
    if "Date" not in df.columns:
        print(f"{symbol} skipped: missing Date column")
        continue
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    required_cols = ["Open_price", "High", "Low", "Close_price", "Adj Close", "Volume"]
    if any(c not in df.columns for c in required_cols):
        print(f"{symbol} skipped: missing columns {sorted([c for c in required_cols if c not in df.columns])}")
        continue

    if len(df) < 500:
        continue

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO prices
            (symbol, date, open_price, high, low, close_price, adj_close, volume)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            symbol,
            row["Date"],
            row["Open_price"],
            row["High"],
            row["Low"],
            row["Close_price"],
            row["Adj Close"],
            int(row["Volume"])
        ))

    conn.commit()
    print(f"{symbol} importato ({len(df)})")
