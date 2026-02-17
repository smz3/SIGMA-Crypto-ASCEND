
import pandas as pd
import sys
from pathlib import Path

def audit_redundancy(log_path):
    print(f"🔍 Auditing Redundancy Logic: {log_path}")
    if not Path(log_path).exists():
        print("❌ Log file not found.")
        return

    df = pd.read_csv(log_path)
    df['open_time'] = pd.to_datetime(df['open_time'])
    
    # Sort by time
    df = df.sort_values('open_time')
    
    # Group by Origin + TF
    violation_count = 0
    clean_count = 0
    
    # 1. Group by OriginID and Timeframe
    grouped = df.groupby(['origin_id', 'tf'])
    
    for (origin_tf), group in grouped:
        origin_id, tf = origin_tf
        
        if pd.isna(origin_id) or origin_id == "": continue
        
        trades = group.sort_values('open_time').to_dict('records')
        
        # Logic: Finds first loss. Any trade opened AFTER that loss (and before reset) is a violation.
        # Note: Our blacklist logic is "forever" until Origin dies/updates.
        # But Origin ID changes only when updated. If same Origin ID persists, blacklist persists.
        
        blacklisted_at = None
        
        for t in trades:
            if blacklisted_at and t['open_time'] > blacklisted_at:
                print(f"❌ VIOLATION: Origin {origin_id} ({tf}) traded at {t['open_time']} AFTER being blacklisted at {blacklisted_at}!")
                violation_count += 1
            
            if t['pnl'] < 0 and not blacklisted_at:
                blacklisted_at = t['close_time'] # Trade closes, blacklist starts.
                # Actually, wait. Blacklist is updated on CLOSE.
                # So subsequent trades OPENED after this CLOSE are blocked.
                blacklisted_at = pd.to_datetime(t['close_time'])

    if violation_count == 0:
        print("✅ PASSED: No Redundancy Violations found.")
    else:
        print(f"❌ FAILED: Found {violation_count} Redundancy Violations.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="research/reports/4th_IS_test/trade_log.csv")
    args = parser.parse_args()
    
    audit_redundancy(args.log)
