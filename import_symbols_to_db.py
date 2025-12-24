import psycopg2
import pandas as pd

conn = psycopg2.connect(
    dbname="nasdaq",
    user="postgres",
    password="TUA_PASSWORD",
    host="localhost",
    port=5432
)
cur = conn.cursor()

df = pd.read_csv("nasdaq_symbols.csv")
df = df.dropna(subset=["Symbol"])
df["Symbol"] = df["Symbol"].astype(str)

for _, row in df.iterrows():
    symbol = row["Symbol"].replace(".", "-")

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
