import pandas as pd
import os
from pathlib import Path

DATA_DIR = Path("data/raw")
TIMEFRAMES = ["MN1", "W1", "D1", "H4", "H1", "M30"]
SYMBOL = "BTCUSDT"

def verify_data():
    print(f"Checking Data for {SYMBOL} (2020-2022 Target)...")
    all_ok = True
    
    for tf in TIMEFRAMES:
        path = DATA_DIR / f"{SYMBOL}_{tf}.parquet"
        if not path.exists():
            print(f"❌ {tf}: File Missing!")
            all_ok = False
            continue
            
        try:
            df = pd.read_parquet(path)
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
            
            start = df.index.min()
            end = df.index.max()
            
            # Check coverage
            start_req = pd.Timestamp("2020-01-01")
            end_req = pd.Timestamp("2022-12-31")
            
            status = "✅"
            if start > start_req: 
                status = "⚠️ MISSING START"
                all_ok = False
            if end < end_req: 
                status = "⚠️ MISSING END"
                all_ok = False
                
            print(f"{status} {tf}: {start.date()} -> {end.date()} (Rows: {len(df)})")
            
        except Exception as e:
            print(f"❌ {tf}: Error reading file: {e}")
            all_ok = False
            
    if all_ok:
        print("\n✅ DATA VERIFICATION COMPLETE: Ready for 2020-2022 Backtest.")
    else:
        print("\n❌ DATA GAPS DETECTED: Download required.")

if __name__ == "__main__":
    verify_data()
