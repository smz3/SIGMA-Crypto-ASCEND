import pandas as pd
import numpy as np

def analyze_performance(file_path):
    df = pd.read_csv(file_path)
    df['open_time'] = pd.to_datetime(df['open_time'])
    df['year'] = df['open_time'].dt.year
    
    # Yearly Aggregation
    yearly = df.groupby('year').agg(
        trades=('pnl', 'count'),
        total_pnl=('pnl', 'sum'),
        avg_pnl=('pnl', 'mean'),
        win_rate=('pnl', lambda x: (x > 0).mean() * 100)
    ).reset_index()
    
    return yearly

if __name__ == "__main__":
    report_dir = "research/reports/Test_9G_Surgical_Flow"
    trades = analyze_performance(f"{report_dir}/trade_log.csv")
    print("\n=== YEARLY PERFORMANCE (TEST 9) ===")
    print(trades)
    
    # Analyze 2022 specifically
    df = pd.read_csv(f"{report_dir}/trade_log.csv")
    df['open_time'] = pd.to_datetime(df['open_time'])
    df_2022 = df[df['open_time'].dt.year == 2022]
    
    print("\n=== 2022 DETAILED AUDIT ===")
    if not df_2022.empty:
        print(df_2022.groupby('reason').agg(
            trades=('pnl', 'count'),
            win_rate=('pnl', lambda x: (x > 0).mean() * 100),
            sum_pnl=('pnl', 'sum')
        ))
    else:
        print("No trades in 2022.")
