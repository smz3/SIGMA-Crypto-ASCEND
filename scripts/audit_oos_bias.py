import pandas as pd

def audit_bias():
    df = pd.read_csv(r'research\reports\Test_13A_OOS_AlphaSentinel\trade_log.csv')
    df['open_time'] = pd.to_datetime(df['open_time'])
    df['month'] = df['open_time'].dt.to_period('M')
    
    bias = df.groupby(['month', 'direction']).size().unstack(fill_value=0)
    bias['Total'] = bias.sum(axis=1)
    bias['Bullish %'] = (bias['BULLISH'] / bias['Total'] * 100).round(2)
    bias['Bearish %'] = (bias['BEARISH'] / bias['Total'] * 100).round(2)
    
    print("--- DIRECTIONAL BIAS AUDIT (2023-2025) ---")
    print(bias[['BULLISH', 'BEARISH', 'Bullish %', 'Bearish %']].head(24))

if __name__ == "__main__":
    audit_bias()
