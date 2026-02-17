
import pandas as pd
import numpy as np

def calculate_metrics(equity_path):
    print(f"📊 Analyzing Metrics: {equity_path}")
    try:
        df = pd.read_csv(equity_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Calculate Drawdown
        df['peak'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['peak']) / df['peak']
        max_dd = df['drawdown'].min()
        
        # Calculate CAGR
        start_equity = df['equity'].iloc[0]
        end_equity = df['equity'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        cagr = (end_equity / start_equity) ** (1 / years) - 1
        
        # Calculate Sharpe (Assume Risk Free = 0 for simplicity in crypto)
        df['returns'] = df['equity'].pct_change()
        mean_return = df['returns'].mean()
        std_return = df['returns'].std()
        # Annualized Sharpe (assuming daily data? No, equity curve is per-trade or per-tick?)
        # VectorizedBacktester equity curve is updated per manage_positions call (per candle/tick).
        # So we should resample to Daily for standardized Sharpe.
        
        daily_df = df['equity'].resample('D').last().dropna()
        daily_returns = daily_df.pct_change()
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(365)
        
        print("\n=== PHASE 10-C RESULTS ===")
        print(f"Start Date: {df.index[0]}")
        print(f"End Date:   {df.index[-1]}")
        print(f"Start Equity: ${start_equity:,.2f}")
        print(f"End Equity:   ${end_equity:,.2f}")
        print("-" * 30)
        print(f"CAGR:       {cagr*100:.2f}%")
        print(f"Max DD:     {max_dd*100:.2f}%")
        print(f"Sharpe:     {sharpe:.2f}")
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error calculating metrics: {e}")

if __name__ == "__main__":
    path = "research/reports/4th_IS_test/equity_curve.csv"
    calculate_metrics(path)
