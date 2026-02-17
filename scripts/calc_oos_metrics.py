import pandas as pd
import numpy as np

def calculate_oos_metrics():
    path = r'research\reports\Test_13A_OOS_AlphaSentinel\equity_curve.csv'
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter for OOS period only
    report_start = pd.Timestamp("2023-01-01")
    df = df[df['timestamp'] >= report_start].copy()
    
    # Drawdown calculation
    df['cum_max'] = df['equity'].cummax()
    df['drawdown'] = (df['equity'] - df['cum_max']) / df['cum_max']
    max_dd = df['drawdown'].min()
    
    # CAGR calculation
    start_equity = df['equity'].iloc[0]
    end_equity = df['equity'].iloc[-1]
    days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days
    years = days / 365.25
    cagr = (end_equity / start_equity) ** (1/years) - 1
    
    print(f"--- OOS METRICS (2023-2025) ---")
    print(f"Start Equity: {start_equity:.2f}")
    print(f"End Equity:   {end_equity:.2f}")
    print(f"OOS CAGR:     {cagr*100:.2f}%")
    print(f"OOS Max DD:   {max_dd*100:.2f}%")
    print(f"Mar Ratio:    {abs(cagr/max_dd):.2f}")

if __name__ == "__main__":
    calculate_oos_metrics()
