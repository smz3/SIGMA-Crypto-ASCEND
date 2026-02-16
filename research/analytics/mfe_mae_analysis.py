
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

def analyze_efficiency():
    print("📉 SIGMA MFE/MAE Efficiency Audit")
    print("="*50)
    
    trade_log_path = 'research/reports/in_sample/trade_log_is.csv'
    if not os.path.exists(trade_log_path):
        trade_log_path = 'research/reports/trade_log_serial.csv'
    
    if not os.path.exists(trade_log_path):
        print("❌ Error: Trade log not found.")
        return

    df = pd.read_csv(trade_log_path)
    
    # 1. SL Buffer Efficiency (MAE)
    # Note: max_adverse_excursion and max_favorable_excursion need to be tracked 
    # per tick/bar in the trade_manager during simulation.
    # If they are 0.0, it means we only have the final PnL.
    
    if 'max_adverse_excursion' not in df.columns or df['max_adverse_excursion'].sum() == 0:
        print("⚠️ High-fidelity MFE/MAE data missing from log. Estimating from PnL outcomes.")
        df['max_favorable_excursion'] = df['pnl'].clip(lower=0)
        df['max_adverse_excursion'] = df['pnl'].clip(upper=0).abs()

    avg_mae = df['max_adverse_excursion'].mean()
    max_mae = df['max_adverse_excursion'].max()
    print(f"Average Adverse Excursion: ${avg_mae:.2f}")
    print(f"Maximum Adverse Excursion: ${max_mae:.2f}")
    print("-" * 50)

    # 2. TP Optimization (MFE)
    wins = df[df['pnl'] > 0]
    if len(wins) > 0:
        avg_mfe = wins['max_favorable_excursion'].mean()
        print(f"Average Favorable Excursion (Wins): ${avg_mfe:.2f}")
    
    # 3. Distribution Analysis
    print("🚀 EXPECTANCY DISTRIBUTION")
    print(f"{'RR Level':<10} | {'Probability':<12}")
    print("-" * 25)
    
    # Use $100 as 1.0R baseline (1% risk on $10k)
    r_baseline = 100.0
    for r in [1, 2, 3]:
        count = len(df[df['pnl'] >= (r * r_baseline)])
        prob = count / len(df) * 100
        print(f"Hit {r}R+     | {prob:>8.2f}%")
    
    print("="*50)

if __name__ == "__main__":
    analyze_efficiency()
