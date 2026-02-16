import pandas as pd
import numpy as np
from pathlib import Path

def analyze_drawdown():
    trade_log_path = Path("research/reports/3rd_IS_test/trade_log.csv")
    if not trade_log_path.exists():
        print("Error: trade_log.csv not found.")
        return

    df = pd.read_csv(trade_log_path)
    df['open_time'] = pd.to_datetime(df['open_time'])
    df['close_time'] = pd.to_datetime(df['close_time'])

    # 1. Identify Overlapping Trades
    # We want to know how many trades were open at the same time.
    # Create a timeline of events
    events = []
    for _, row in df.iterrows():
        events.append((row['open_time'], 1))
        events.append((row['close_time'], -1))
    
    events_df = pd.DataFrame(events, columns=['time', 'delta'])
    events_df = events_df.sort_values(by='time')
    events_df['concurrent_trades'] = events_df['delta'].cumsum()

    print(f"Max Concurrent Trades: {events_df['concurrent_trades'].max()}")
    
    # 2. Analyze the Drawdown Period (Aug 2020 - Sep 2021)
    mask = (events_df['time'] >= '2020-08-01') & (events_df['time'] <= '2021-10-01')
    dd_events = events_df[mask]
    
    if not dd_events.empty:
        print(f"Max Concurrent Trades in DD Period: {dd_events['concurrent_trades'].max()}")
        avg_concurrent = dd_events['concurrent_trades'].mean()
        print(f"Average Concurrent Trades in DD Period: {avg_concurrent:.2f}")

    # 3. Identify the "Death Cluster"
    death_cluster = events_df.sort_values(by='concurrent_trades', ascending=False).head(20)
    print("\nTop 20 Concurrent Trade Events:")
    print(death_cluster)

    # 4. Correlation Check: How many trades on the same timeframe?
    print("\nTrade Count by Timeframe Area:")
    df['tf_tag'] = df['entry_reason'].str.split('#').str[0]
    print(df['tf_tag'].value_counts())

if __name__ == "__main__":
    analyze_drawdown()
