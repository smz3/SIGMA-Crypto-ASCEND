import pandas as pd
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from core.visualization.plotly_visualizer import ChartVisualizer

def run():
    print("Generating Visualization...")
    
    # 1. Load Data (Driver TF)
    # We use M30 data for the chart background
    data_path = "data/processed/BTCUSDT_M30.parquet"
    if not os.path.exists(data_path):
        data_path = "data/raw/BTCUSDT_M30.parquet"
        
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return
        
    df = pd.read_parquet(data_path)
    
    # Ensure Index is Datetime for slicing
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    # Filter 2020 for Smoke Test Range
    df = df.loc["2020-01-01":"2020-12-31"]
    
    # 2. Init Visualizer
    viz = ChartVisualizer(df)
    viz.plot_candles()
    
    # 3. Add Trades
    trade_log = "research/reports/trade_log.csv"
    if os.path.exists(trade_log):
        viz.plot_trades(trade_log)
    else:
        print(f"Warning: Trade log not found at {trade_log}")
        
    # 4. Save
    output_file = "research/reports/strategy_audit_2020.html"
    viz.save_html(output_file)
    print(f"Done! Open {output_file} to view results.")

if __name__ == "__main__":
    run()
