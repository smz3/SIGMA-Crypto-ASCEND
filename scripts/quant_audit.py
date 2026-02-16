import pandas as pd
import numpy as np

def analyze():
    # Load data
    try:
        trades = pd.read_csv('research/reports/trade_log.csv')
        equity = pd.read_csv('research/reports/equity_curve.csv', names=['ts', 'equity'], header=0)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    # 1. Trade Calculation
    wr = len(trades[trades['pnl'] > 0]) / len(trades)
    pf = trades[trades['pnl'] > 0].pnl.sum() / abs(trades[trades['pnl'] < 0].pnl.sum())
    avg_win = trades[trades['pnl'] > 0].pnl.mean()
    avg_loss = abs(trades[trades['pnl'] < 0].pnl.mean())
    expectancy = (wr * avg_win) - ((1-wr) * avg_loss)
    
    # 2. Equity Calculation
    max_eq = equity.equity.max()
    min_eq = equity.equity.min()
    current_eq = equity.equity.iloc[-1]
    
    equity['drawdown'] = (equity.equity.cummax() - equity.equity) / equity.equity.cummax()
    max_dd = equity.drawdown.max()
    
    # 3. Correlation Audit (Simultaneous Trades)
    trades['open_time'] = pd.to_datetime(trades['open_time'])
    trades['close_time'] = pd.to_datetime(trades['close_time'])
    
    # Simple check for overlapping trades
    max_overlap = 0
    for idx, row in trades.sample(min(100, len(trades))).iterrows(): # Sample to avoid O(N^2)
        overlap = len(trades[(trades.open_time <= row.close_time) & (trades.close_time >= row.open_time)])
        max_overlap = max(max_overlap, overlap)

    print(f"--- QUANT AUDIT ---")
    print(f"Win Rate: {wr:.2%}")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Expectancy ($ per trade): {expectancy:.2f}")
    print(f"Average Win: ${avg_win:.2f} | Average Loss: ${avg_loss:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Peak Equity: ${max_eq:.2f} | Final Equity: ${current_eq:.2f}")
    print(f"Max Sampled Overlap (Correlated Risk): {max_overlap} positions")
    print(f"-------------------")

if __name__ == '__main__':
    analyze()
