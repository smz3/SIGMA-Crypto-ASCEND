import pandas as pd
from core.visualization.plotly_visualizer import ChartVisualizer
import os

def generate_enhanced_audit():
    print("Generating Enhanced Visual Audit...")
    
    # 1. Load M30 Data
    data_path = "data/raw/BTCUSDT_M30.parquet"
    if not os.path.exists(data_path):
        print(f"Error: Data not found at {data_path}")
        return
    
    df = pd.read_parquet(data_path)
    df = pd.read_parquet(data_path)
    
    # Force search for any time column and convert to index
    time_cols = [c for c in df.columns if 'time' in c.lower()]
    if time_cols:
        df.set_index(pd.to_datetime(df[time_cols[0]]), inplace=True)
    elif not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except:
            print("Warning: Could not convert index to datetime.")
    
    # Standardize columns for PlotlyVisualizer
    df.columns = [c.lower() for c in df.columns]

    # Slice to 2020 for performance (Now with DatetimeIndex)
    df_2020 = df['2020-01-01':'2020-12-31']
    
    # 2. Initialize Visualizer
    viz = ChartVisualizer(df_2020)
    
    # 3. Plot Candles
    viz.plot_candles()
    
    # 4. Plot Trades (Entries + Exits)
    # This will now use the updated logic with circles/X for exits
    viz.plot_trades("research/reports/trade_log.csv")
    
    # 5. Save
    viz.save_html("research/reports/strategy_audit_2020_v2.html")
    print("Enhanced Audit saved to research/reports/strategy_audit_2020_v2.html")

if __name__ == "__main__":
    generate_enhanced_audit()
