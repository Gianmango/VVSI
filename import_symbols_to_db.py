import psycopg2
import pandas as pd
import os

conn = psycopg2.connect(
    dbname="nasdaq",
    user="postgres",
    password="pistone",
    host="localhost",
    port=5432
)
cur = conn.cursor()

cur.execute("TRUNCATE TABLE symbols RESTART IDENTITY CASCADE")
conn.commit()

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(_SCRIPT_DIR, "data")
df = pd.read_csv(os.path.join(data_dir, "nasdaq_symbols.csv"))
existing = set()
if os.path.isdir(data_dir):
    for f in os.listdir(data_dir):
        if f.endswith(".csv"):
            existing.add(f.replace(".csv", ""))
df = df.dropna(subset=["Symbol"])
df["Symbol"] = df["Symbol"].astype(str)

for _, row in df.iterrows():
    symbol = row["Symbol"].replace(".", "-")

    if symbol not in existing:
        continue

    cur.execute("""
        INSERT INTO symbols (symbol, name, sector, industry, country)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, (
        symbol,
        row.get("Name"),
        row.get("Sector"),
        row.get("Industry"),
        row.get("Country")
    ))

conn.commit()
cur.close()
conn.close()

print("Tabella symbols popolata correttamente.")
