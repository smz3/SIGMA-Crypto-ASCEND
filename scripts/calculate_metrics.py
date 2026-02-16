
import pandas as pd
import numpy as np
import os

def calculate():
    equity_path = 'research/reports/equity_curve_serial.csv'
    trade_path = 'research/reports/trade_log_serial.csv'
    
    if not os.path.exists(equity_path) or not os.path.exists(trade_path):
        print("Error: Files not found.")
        return

    # Load Equity
    print(f"Reading {equity_path}...")
    df = pd.read_csv(equity_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    equity = df['equity']

    # Basic Metrics
    initial_equity = 10000 
    final_equity = equity.iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity * 100

    # Drawdown
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    max_dd = drawdown.min() * 100

    # Annualized Metrics (Resample to Daily)
    daily_equity = equity.resample('D').last().ffill()
    daily_returns = daily_equity.pct_change().dropna()
    
    ann_return = daily_returns.mean() * 365 * 100
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(365) if daily_returns.std() != 0 else 0

    # Sortino
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(365)
    sortino = (daily_returns.mean() * 365) / downside_std if downside_std != 0 else 0

    # Trade Metrics
    print(f"Reading {trade_path}...")
    trades = pd.read_csv(trade_path)
    total_trades = len(trades)
    
    # Use 'pnl' instead of 'pnl_money'
    wins = trades[trades['pnl'] > 0]
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    
    gross_profit = wins['pnl'].sum()
    losses = trades[trades['pnl'] <= 0]
    gross_loss = abs(losses['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
    avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 0
    expectancy_ratio = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)

    print("\n" + "="*40)
    print("📊 SIGMA 2020 PERFORMANCE BREAKDOWN")
    print("="*40)
    print(f"Initial Capital:   $10,000.00")
    print(f"Final Equity:      ${final_equity:,.2f}")
    print(f"Total Return:      {total_return:.2f}%")
    print(f"Max Drawdown:      {max_dd:.2f}%")
    print("-" * 40)
    print(f"Annualized Sharpe: {sharpe:.2f}")
    print(f"Annualized Sortino: {sortino:.2f}")
    print("-" * 40)
    print(f"Total Trades:      {total_trades}")
    print(f"Win Rate:          {win_rate:.2f}%")
    print(f"Profit Factor:     {profit_factor:.2f}")
    print(f"Avg Win:           ${avg_win:.2f}")
    print(f"Avg Loss:          -${avg_loss:.2f}")
    print(f"Expec. Per Trade:  ${expectancy_ratio:.2f}")
    print("="*40)

if __name__ == '__main__':
    calculate()
