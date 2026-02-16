
import pandas as pd
import numpy as np
import os
from pathlib import Path

def calculate_structural_alpha():
    print("📊 SIGMA Structural Alpha & Confluence Lift Engine")
    print("="*50)
    
    trade_log_path = 'research/reports/in_sample/trade_log_is.csv'
    if not os.path.exists(trade_log_path):
        # Fallback to smoke test for dev testing
        trade_log_path = 'research/reports/trade_log_serial.csv'
    
    if not os.path.exists(trade_log_path):
        print("❌ Error: Trade log not found. Run backtest first.")
        return

    df = pd.read_csv(trade_log_path)
    
    # Join with the correct column name
    if 'entry_comment' not in df.columns:
        print("⚠️ 'entry_comment' missing. Check TradeManager.")
        print(f"Columns: {df.columns.tolist()}")
        return

    def get_tier(comment):
        if not isinstance(comment, str): return 'None'
        if 'MN1' in comment: return 'MN1'
        if 'W1' in comment: return 'W1'
        if 'D1' in comment: return 'D1'
        return 'None'

    df['authority_tier'] = df['entry_comment'].apply(get_tier)
    
    tier_stats = []
    for tier in ['MN1', 'W1', 'D1']:
        tier_df = df[df['authority_tier'] == tier]
        if len(tier_df) > 0:
            tier_wins = tier_df[tier_df['pnl'] > 0]
            tier_wr = len(tier_wins) / len(tier_df) * 100
            tier_stats.append({
                'Tier': tier,
                'Count': len(tier_df),
                'WinRate': tier_wr
            })
    
    # Baseline for Comparison
    total_trades = len(df)
    wins = df[df['pnl'] > 0]
    overall_wr = len(wins) / total_trades * 100
    avg_rr = df[df['pnl'] > 0]['pnl'].mean() / abs(df[df['pnl'] < 0]['pnl'].mean()) if len(df[df['pnl'] < 0]) > 0 else 0
    
    print(f"Total Trades: {total_trades}")
    print(f"Overall Win Rate: {overall_wr:.2f}%")
    print(f"Achieved RR: {avg_rr:.2f}:1")
    print("-" * 50)
    
    print("🧠 CONFLUENCE LIFT ANALYSIS")
    print(f"{'Tier':<10} | {'Count':<6} | {'Win Rate':<10} | {'Alpha Lift':<10}")
    print("-" * 45)
    for s in tier_stats:
        lift = s['WinRate'] - overall_wr
        print(f"{s['Tier']:<10} | {s['Count']:<6} | {s['WinRate']:>8.2f}% | {lift:>+8.2f}%")
    print("-" * 50)

    # 3. Discovery vs Flow Efficiency
    flow_df = df[df['entry_comment'].str.contains('Flow', na=False)]
    disco_df = df[df['entry_comment'].str.contains('Discovery', na=False)]
    
    if len(flow_df) > 0:
        flow_wr = len(flow_df[flow_df['pnl'] > 0]) / len(flow_df) * 100
        print(f"Magnet Flow Trades:   {len(flow_df):<5} | Win Rate: {flow_wr:.2f}%")
    
    if len(disco_df) > 0:
        disco_wr = len(disco_df[disco_df['pnl'] > 0]) / len(disco_df) * 100
        print(f"Discovery (Sky) Trades: {len(disco_df):<5} | Win Rate: {disco_wr:.2f}%")
    
    print("="*50)

if __name__ == "__main__":
    calculate_structural_alpha()
