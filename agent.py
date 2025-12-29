import requests
import pandas as pd
import numpy as np
import os

BASE_URL = "http://localhost:3001"

LEVES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
WINDOWS = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
DAILY_LEVERAGE_COST = 0.0001
TRANSACTION_COST = 0.0005
BUY_THRESHOLD = 0.98
SELL_THRESHOLD = 1.05

os.makedirs("metrics", exist_ok=True)

# =============================
# Funzioni di supporto
# =============================

def load_available_symbols(data_dir="../data"):
    return [
        f.replace(".csv", "")
        for f in os.listdir(data_dir)
        if f.endswith(".csv")
    ]

def fetch_prices(symbol, window):
    url = f"{BASE_URL}/v_geom_mean_30?symbol=eq.{symbol}&order=date.asc"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Errore REST per {symbol}: {response.status_code}")
        return pd.DataFrame()
    data = response.json()
    if not data:
        print(f"Nessun dato per {symbol}")
        return pd.DataFrame()
    return pd.DataFrame(data)

def update_portfolio(portfolio, action, price, leverage):
    if action == "BUY" and portfolio["position"] == 0:
        portfolio["position"] = 1
        portfolio["entry_price"] = price
    elif action == "SELL" and portfolio["position"] == 1:
        pnl = (price - portfolio["entry_price"]) * leverage
        portfolio["cash"] += pnl
        portfolio["position"] = 0
        portfolio["entry_price"] = 0
        portfolio["cash"] -= price * TRANSACTION_COST
    if portfolio["position"] == 1:
        portfolio["cash"] -= price * DAILY_LEVERAGE_COST
    return portfolio

def trading_agent(df, leverage):
    portfolio = {"cash": 10000, "position": 0, "entry_price": 0}
    history = []

    for _, row in df.iterrows():
        price = float(row["price"])
        geom_mean = float(row["geom_mean_30"])
        action = "HOLD"
        if price < geom_mean * BUY_THRESHOLD and portfolio["position"] == 0:
            action = "BUY"
        elif price > geom_mean * SELL_THRESHOLD and portfolio["position"] == 1:
            action = "SELL"
        portfolio = update_portfolio(portfolio, action, price, leverage)
        history.append({**portfolio, "price": price, "date": row["date"], "action": action})
    return pd.DataFrame(history)

def calculate_metrics(history_df):
    if history_df.empty:
        return {}
    profit_total = history_df["cash"].iloc[-1] - 10000
    history_df["daily_return"] = history_df["cash"].diff().fillna(0)
    history_df["cummax"] = history_df["cash"].cummax()
    history_df["drawdown"] = history_df["cash"] - history_df["cummax"]
    max_drawdown = history_df["drawdown"].min()
    volatility = history_df["daily_return"].std()
    sharpe_ratio = (history_df["daily_return"].mean() / volatility * np.sqrt(252)) if volatility != 0 else np.nan
    num_trades = history_df[history_df["action"].isin(["BUY","SELL"])].shape[0]
    percent_in_position = (history_df["position"] == 1).mean()
    profit_per_trade = profit_total / num_trades if num_trades > 0 else 0
    return {
        "profit_total": profit_total,
        "max_drawdown": max_drawdown,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
        "num_trades": num_trades,
        "percent_in_position": percent_in_position,
        "profit_per_trade": profit_per_trade
    }

# =============================
# Lettura simboli
# =============================

symbols_list = load_available_symbols()

# =============================
# Ciclo completo su simboli, leva e finestre
# =============================

all_metrics = []
n = 0

# Rimuovi n è solo per testare
for symbol in symbols_list:
    if n==10: break
    n += 1
    print(f"\n=== Simulazione per {symbol} ===")
    df_prices = fetch_prices(symbol, WINDOWS[0])
    if df_prices.empty:
        continue
    for window in WINDOWS:
        for leverage in LEVES:
            result = trading_agent(df_prices, leverage)
            metrics = calculate_metrics(result)
            metrics.update({"symbol": symbol, "window": window, "leverage": leverage})
            all_metrics.append(metrics)

# =============================
# Salvataggio risultati
# =============================

metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv("metrics/metrics_summary.csv", index=False)
print(metrics_df.head())
print("\nSimulazione completata! Metriche salvate in metrics/metrics_summary.csv")
