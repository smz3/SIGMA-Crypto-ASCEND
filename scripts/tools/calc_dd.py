import pandas as pd
try:
    df = pd.read_csv('research/reports/3rd_IS_test/equity_curve.csv')
    df['equity'] = pd.to_numeric(df['equity'])
    peak = df['equity'].cummax()
    dd = (df['equity'] - peak) / peak
    print(f"Max Drawdown: {dd.min():.2%}")
except Exception as e:
    print(f"Error: {e}")
