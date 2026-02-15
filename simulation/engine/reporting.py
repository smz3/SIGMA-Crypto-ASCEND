import pandas as pd
import numpy as np
import quantstats as qs
import os
import matplotlib.pyplot as plt

# Patching QuantStats to avoid display issues in some environments
qs.extend_pandas()

def generate_tearsheet(equity_path: str, output_path: str):
    """
    Generates a professional QuantStats tearsheet from an equity curve.
    """
    print(f"Generating Tearsheet from {equity_path}...")
    
    if not os.path.exists(equity_path):
        print(f"Error: Equity history not found at {equity_path}")
        return

    # 1. Load Equity
    df = pd.read_csv(equity_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # 2. Resample to Daily to avoid "High Frequency Noise" in some metrics
    df_daily = df['equity'].resample('D').last().dropna()
    
    # 3. Calculate Returns
    returns = df_daily.pct_change().dropna()
    
    # 4. Generate Report
    qs.reports.html(returns, output=output_path, title="SIGMA B2B Strategy - 2020 Smoke Test")
    print(f"QuantStats Report saved to {output_path}")

if __name__ == "__main__":
    generate_tearsheet("research/reports/equity_curve.csv", "research/reports/tearsheet_2020.html")
