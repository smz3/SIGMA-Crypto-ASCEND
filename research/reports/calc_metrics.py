import pandas as pd
import numpy as np

def calculate_metrics(csv_path):
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Drawdown
    equity = df['equity'].values
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    max_dd = np.min(drawdown) * 100
    
    # Returns
    start_equity = equity[0]
    end_equity = equity[-1]
    total_return = (end_equity - start_equity) / start_equity
    
    # CAGR
    years = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days / 365.25
    cagr = ((end_equity / start_equity) ** (1/years) - 1) * 100
    
    return max_dd, total_return * 100, cagr

if __name__ == "__main__":
    path = r"c:\Users\User\Desktop\SIGMA System Anti Gravity\SIGMA-Crypto-ASCEND\research\reports\8th_IS_test\equity_curve.csv"
    max_dd, total_ret, cagr = calculate_metrics(path)
    print(f"Max Drawdown: {max_dd:.2f}%")
    print(f"Total Return: {total_ret:.2f}%")
    print(f"CAGR: {cagr:.2f}%")
