"""
Script per unire i risultati di multiple run (una per window) 
e produrre un'analisi finale completa.
"""
import pandas as pd
import os


def merge_results(result_files):
    """Unisce multiple file CSV di risultati"""
    all_dfs = []
    
    print("=" * 70)
    print("=== MERGE RISULTATI SIMULAZIONI ===")
    print("=" * 70)
    
    for i, file_path in enumerate(result_files, 1):
        if not os.path.exists(file_path):
            print(f"\nFile non trovato: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        print(f"\n[{i}/{len(result_files)}] {file_path}")
        print(f"      - Righe: {len(df)}")
        print(f"      - Windows: {sorted(df['window'].unique())}")
        print(f"      - Leverage: {sorted(df['leverage'].unique())}")
        
        all_dfs.append(df)
    
    if not all_dfs:
        print("\nNessun file trovato!")
        return None
    
    # Unisci tutti i dataframe
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Rimuovi eventuali duplicati
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(
        subset=['window', 'leverage', 'tp', 'sl', 'dp', 'capital_per_trade'],
        keep='first'
    )
    after_dedup = len(merged_df)
    
    if before_dedup > after_dedup:
        print(f"\n⚠️  Rimossi {before_dedup - after_dedup} duplicati")
    
    print(f"\n  Dataset finale: {len(merged_df)} configurazioni uniche")
    print(f"  Windows totali: {sorted(merged_df['window'].unique())}")
    
    return merged_df


def analyze_results(df):
    """Analisi completa dei risultati"""
    
    print("\n" + "=" * 70)
    print("=== ANALISI COMPLETA ===")
    print("=" * 70)
    
    # 1. MIGLIORE ASSOLUTA
    best_overall = df.sort_values("score", ascending=False).iloc[0]
    

    print("CONFIGURAZIONE VINCENTE (ASSOLUTA)")
    print(" " * 35)
    print(f"\nPARAMETRI:")
    print(f"   Window:           {int(best_overall['window'])}")
    print(f"   Leverage:         {int(best_overall['leverage'])}x")
    print(f"   Take Profit:      {best_overall['tp']:.1f}%")
    print(f"   Stop Loss:        {best_overall['sl']:.1f}%")
    print(f"   Drawdown Prot:    {best_overall['dp']:.1f}%")
    print(f"   Capital per trade: ${int(best_overall['capital_per_trade'])}")
    
    print(f"\nPERFORMANCE:")
    print(f"   Profit totale:    ${best_overall['profit_total']:,.2f}")
    print(f"   Profit per trade: ${best_overall['profit_per_trade']:,.2f}")
    print(f"   Numero trades:    {int(best_overall['num_trades'])}")
    
    print(f"\nMETRICHE:")
    print(f"   Sharpe Ratio:     {best_overall['sharpe']:.3f}")
    print(f"   Max Drawdown:     {best_overall['max_drawdown']:.2f}%")
    print(f"   Volatility:       {best_overall['volatility']:.2f}")
    print(f"   Score finale:     {best_overall['score']:.4f}")
    
    # 2. MIGLIORI PER WINDOW
    print("\n" + "=" * 70)
    print("CONFRONTO PER WINDOW")
    print("=" * 70)
    
    best_per_window = df.sort_values("score", ascending=False).groupby("window").first().reset_index()
    best_per_window = best_per_window.sort_values("window")
    
    print("\n{:<10} {:<10} {:<10} {:<12} {:<10} {:<10}".format(
        "Window", "Leverage", "TP%", "Profit", "Sharpe", "Score"
    ))
    print("-" * 70)
    
    for _, row in best_per_window.iterrows():
        print("{:<10} {:<10} {:<10.1f} ${:<11,.0f} {:<10.2f} {:<10.4f}".format(
            int(row['window']),
            f"{int(row['leverage'])}x",
            row['tp'],
            row['profit_total'],
            row['sharpe'],
            row['score']
        ))
    
    # 3. TOP 10 CONFIGURAZIONI
    print("\n" + "=" * 70)
    print("TOP 10 CONFIGURAZIONI")
    print("=" * 70)
    
    top10 = df.sort_values("score", ascending=False).head(10)
    
    print("\n{:<5} {:<8} {:<8} {:<6} {:<6} {:<6} {:<12} {:<10}".format(
        "Rank", "Window", "Lev", "TP%", "SL%", "DP%", "Profit", "Score"
    ))
    print("-" * 70)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        print("{:<5} {:<8} {:<8} {:<6.1f} {:<6.1f} {:<6.1f} ${:<11,.0f} {:<10.4f}".format(
            rank,
            int(row['window']),
            f"{int(row['leverage'])}x",
            row['tp'],
            row['sl'],
            row['dp'],
            row['profit_total'],
            row['score']
        ))
    
    # 4. STATISTICHE GENERALI
    print("\n" + "=" * 70)
    print("STATISTICHE GENERALI")
    print("=" * 70)
    
    profitable = (df['profit_total'] > 0).sum()
    total = len(df)
    
    print(f"\n   Configurazioni totali:     {total}")
    print(f"   Configurazioni profittevoli: {profitable} ({profitable/total*100:.1f}%)")
    print(f"   Configurazioni in perdita:   {total - profitable} ({(total-profitable)/total*100:.1f}%)")
    print(f"\n   Profit medio:              ${df['profit_total'].mean():,.2f}")
    print(f"   Profit mediano:            ${df['profit_total'].median():,.2f}")
    print(f"   Profit massimo:            ${df['profit_total'].max():,.2f}")
    print(f"   Profit minimo:             ${df['profit_total'].min():,.2f}")
    print(f"   Deviazione standard:       ${df['profit_total'].std():,.2f}")
    print(f"\n   Sharpe medio:              {df['sharpe'].mean():.3f}")
    print(f"   Max drawdown medio:        {df['max_drawdown'].mean():.2f}%")
    
    # 5. ANALISI PARAMETRI
    print("\n" + "=" * 70)
    print("DISTRIBUZIONE PARAMETRI NEL TOP 10%")
    print("=" * 70)
    
    top_10_percent = df.nlargest(int(len(df) * 0.1), 'score')
    
    print("\nWindow più frequenti:")
    window_counts = top_10_percent['window'].value_counts()
    for window, count in window_counts.items():
        print(f"   Window {int(window):3d}: {count:3d} occorrenze ({count/len(top_10_percent)*100:.1f}%)")
    
    print("\nLeverage più frequenti:")
    leverage_counts = top_10_percent['leverage'].value_counts()
    for lev, count in leverage_counts.items():
        print(f"   Leverage {int(lev):2d}x: {count:3d} occorrenze ({count/len(top_10_percent)*100:.1f}%)")
    
    return best_overall, best_per_window, top10


def save_final_results(merged_df, best_overall, best_per_window, top10):
    """Salva tutti i risultati finali"""
    
    print("\n" + "=" * 70)
    print("SALVATAGGIO RISULTATI")
    print("=" * 70)
    
    output_dir = "results/final"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Dataset completo merged
    merged_df.to_csv(f"{output_dir}/all_results_merged.csv", index=False)
    
    # 2. Best per window
    best_per_window.to_csv(f"{output_dir}/best_per_window.csv", index=False)
    
    # 3. Top 10
    top10.to_csv(f"{output_dir}/top10.csv", index=False)
    
    # 4. Best overall
    best_df = pd.DataFrame([best_overall])
    best_df.to_csv(f"{output_dir}/best_overall.csv", index=False)
    
    print(f"\n{'=' * 70}")
    print(f"Tutti i risultati salvati in: {output_dir}/")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    print("\nAvvio merge e analisi risultati...\n")
    
    # Specifica i file da unire
    # OPZIONE 1: Specifica manualmente i file
    result_files = [
        "results/raw_results_w50.csv",  # Window 50
        "results/raw_results_w100.csv",  # Window 100 (rinomina se necessario)
        "results/raw_results_w200.csv",  # Window 200 (rinomina se necessario)
    ]
    
    # OPZIONE 2: Cerca automaticamente tutti i file CSV in results/
    # result_files = [
    #     os.path.join("results", f) 
    #     for f in os.listdir("results") 
    #     if f.endswith(".csv") and "raw_results" in f
    # ]
    
    print("File da processare:")
    for f in result_files:
        exists = "si" if os.path.exists(f) else "no"
        print(f"  {exists} {f}")
    
    # Merge
    merged_df = merge_results(result_files)
    
    if merged_df is None:
        print("\nMerge fallito. Verifica i percorsi dei file.")
        exit(1)
    
    # Analisi
    best_overall, best_per_window, top10 = analyze_results(merged_df)
    
    # Salva
    save_final_results(merged_df, best_overall, best_per_window, top10)
    
    print("\nAnalisi completata con successo!\n")