import psycopg2
import pandas as pd
import os
from psycopg2.extras import execute_batch


conn = psycopg2.connect(
    dbname="nasdaq",
    user="postgres",
    password="password",
    host="localhost",
    port=5432
)
cur = conn.cursor()

DATA_DIR = "../../data"

files = os.listdir(DATA_DIR)

for filename in files:
    symbol = filename.replace(".csv", "")
    path = os.path.join(DATA_DIR, filename)

    # leggi un CSV così com'è
    df = pd.read_csv("../data/MSFT.csv", skiprows=2)  # salta le prime due righe inutili
    
    # rinomina le colonne correttamente
    df.columns = ["Date", "Adj Close", "Close", "High", "Low", "Open", "Volume"]
    
    # converti Date in datetime
    df["Date"] = pd.to_datetime(df["Date"])

    if len(df) < 500:
        continue

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO prices
            (symbol, date, open, high, low, close, adj_close, volume)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            symbol,
            row["Date"],
            row["Open"],
            row["High"],
            row["Low"],
            row["Close"],
            row["Adj Close"],
            int(row["Volume"])
        ))

    conn.commit()
    print(f"{symbol} importato ({len(df)})")
