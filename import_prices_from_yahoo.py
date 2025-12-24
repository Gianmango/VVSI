# Importa tutti i dati da yahoo finance per ogni simbolo presente nella lista del nasdaq (ammesso che sia valido)

import yfinance as yf
import time
import pandas as pd
import os

# Crea cartella dove mettere i file
os.makedirs("data", exist_ok=True)

# Copia dal file dei simboli tutti i simboli
df = pd.read_csv("nasdaq_symbols.csv")
symbols = df["Symbol"].dropna().unique().tolist()

# Download dal 2000 a oggi
#for symbol in symbols:
#    try:
#        df = yf.download(
#            symbol,
#            start="2000-01-01",
#            end="2025-01-01",
#            auto_adjust=False,
#            progress=False
#        )
#
#        if df.empty:
#            continue
#
#        df.to_csv(f"data/{symbol}.csv")
#        time.sleep(0.5)
#
#    except Exception as e:
#        print(f"Errore su {symbol}: {e}")


print(f"Simboli totali: {len(symbols)}")
print(f"CSV salvati: {len(os.listdir('data'))}")
