import pandas as pd
import os

LOG_PATH = "research/reports/Test_9G_Surgical_Flow/trade_log.csv"

if os.path.exists(LOG_PATH):
    df = pd.read_csv(LOG_PATH)
    print(f"Total Trades: {len(df)}")
    
    if 'direction' in df.columns:
        print("\n=== DIRECTION BREAKDOWN ===")
        print(df['direction'].value_counts())
        
        df['open_time'] = pd.to_datetime(df['open_time'])
        df['year'] = df['open_time'].dt.year
        
        print("\n=== YEARLY DIRECTION ===")
        print(df.groupby(['year', 'direction']).size())
    else:
        print("Column 'direction' not found!")
else:
    print(f"Log file not found: {LOG_PATH}")
