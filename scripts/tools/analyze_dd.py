import pandas as pd
import numpy as np

def run_analysis():
    path = r'research\reports\Phase12A_TierGating\trade_log.csv'
    df = pd.read_csv(path)
    df['open_time'] = pd.to_datetime(df['open_time'])
    
    windows = [
        ('2022-07-13', '2022-12-31', 'DD1: 2022 Late Stagnation (-62.86%)'),
        ('2021-11-15', '2022-05-08', 'DD2: 2021/22 Top Reversal (-58.69%)'),
        ('2021-01-16', '2021-02-28', 'DD3: 2021 Parabolic Exhaustion (-52.85%)'),
        ('2020-02-15', '2020-04-05', 'DD4: 2020 Black Swan / Recovery (-43.69%)')
    ]
    
    for start, end, label in windows:
        v = df[(df['open_time'] >= start) & (df['open_time'] <= end)].copy()
        if len(v) == 0:
            print(f"No trades found for {label}")
            continue
            
        print(f"\n==========================================")
        print(f"ANALYSIS: {label}")
        print(f"==========================================")
        print(f"Total Trades: {len(v)}")
        
        winners = v[v['pnl'] > 0]
        losers = v[v['pnl'] <= 0]
        
        wr = len(winners) / len(v)
        total_pnl = v['pnl'].sum()
        avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl'].mean() if len(losers) > 0 else 0
        
        print(f"Win Rate: {wr:.2%}")
        # print(f"Total PnL: {total_pnl:.2f}") # PnL is non-normalized in compounding mode
        print(f"Avg Win: {avg_win:.2f} | Avg Loss: {avg_loss:.2f}")
        print(f"Reward:Risk: {abs(avg_win/avg_loss) if avg_loss != 0 else np.inf:.2f}")
        
        print("\nTOP ENTRY REASONS:")
        print(v['entry_reason'].value_counts().head(3))
        
        print("\nDIRECTION DISTRIBUTION:")
        print(v['direction'].value_counts())
        
        # Reload Risk Detection
        v['time_diff'] = v['open_time'].diff().dt.total_seconds() / 3600
        rapid_fire = v[v['time_diff'] < 4] # Changed to 4 hours for meaningful cluster detection
        print(f"\nReload Clusters (<4h apart): {len(rapid_fire)}")

if __name__ == "__main__":
    run_analysis()
