import pandas as pd
import numpy as np
import os
from pathlib import Path

def calculate_metrics(equity_path, trade_path):
    if not os.path.exists(equity_path):
        return None
    
    # 1. Equity Metrics
    eq_df = pd.read_csv(equity_path)
    eq_df['timestamp'] = pd.to_datetime(eq_df['timestamp'])
    eq_df = eq_df.set_index('timestamp')
    
    # CAGR
    total_days = (eq_df.index[-1] - eq_df.index[0]).days
    years = total_days / 365.25
    initial_val = 10000.0 # Standard for these tests
    final_val = eq_df['equity'].iloc[-1]
    cagr = (final_val / initial_val) ** (1/years) - 1
    
    # Max Drawdown
    rolling_max = eq_df['equity'].cummax()
    drawdown = (eq_df['equity'] - rolling_max) / rolling_max
    max_dd = drawdown.min()
    
    # Calmar
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0
    
    # Sharpe (approx daily)
    returns = eq_df['equity'].pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 48) # 30m bars approx
    
    # 2. Trade Metrics
    tr_df = pd.read_csv(trade_path)
    trades = len(tr_df)
    win_rate = (tr_df['pnl'] > 0).mean()
    
    # Profit Factor
    gross_profit = tr_df[tr_df['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(tr_df[tr_df['pnl'] < 0]['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
    
    return {
        "Trades": trades,
        "CAGR": f"{cagr:.1%}",
        "Max DD": f"{max_dd:.1%}",
        "Calmar": f"{calmar:.2f}",
        "Win Rate": f"{win_rate:.1%}",
        "Profit Factor": f"{profit_factor:.2f}"
    }

tests = {
    "Test 9G": ("research/reports/Test_9G_Surgical_Flow/equity_curve.csv", "research/reports/Test_9G_Surgical_Flow/trade_log.csv"),
    "Test 10D (Combined)": ("research/reports/Test_10D_Phase12D_StructuralIntegrity/equity_curve.csv", "research/reports/Test_10D_Phase12D_StructuralIntegrity/trade_log.csv"),
    "Test 10E (Memory Only)": ("research/reports/Test_10E_Phase12D_StructuralMemoryOnly/equity_curve.csv", "research/reports/Test_10E_Phase12D_StructuralMemoryOnly/trade_log.csv")
}

results = {}
for name, paths in tests.items():
    res = calculate_metrics(paths[0], paths[1])
    if res:
        results[name] = res

print(pd.DataFrame(results).T.to_markdown())
