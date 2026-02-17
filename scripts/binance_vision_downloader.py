"""
binance_vision_downloader.py

Bypasses API blocks by downloading historical OHLCV data directly from 
Binance Public Data (S3) archives.

Architecture:
1. Hybrid Source: Uses SPOT data for 2018-2019 and FUTURES data for 2020-2026.
2. Parallelism: Uses ThreadPoolExecutor for fast daily fallback checks.
3. Processing: Extracts CSV, renames columns, merges, and saves to Parquet.
"""

import requests
import zipfile
import pandas as pd
import io
import os
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["1d", "4h", "1h", "30m"]
START_YEAR = 2018
END_YEAR = 2025
DATA_DIR = Path("data/raw")

def get_base_url(year, timeframe):
    if year < 2020:
        return f"https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/{timeframe}"
    else:
        return f"https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/{timeframe}"

def get_daily_base_url(year, timeframe):
    if year < 2020:
        return f"https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/{timeframe}"
    else:
        return f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{timeframe}"

def fetch_file(url):
    try:
        # User-Agent to avoid potential blocks and verify SSL
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=15, headers=headers, verify=True)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    df = pd.read_csv(f, header=None)
                    df = df.iloc[:, :6]
                    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    return df
    except Exception as e:
        # Silent fail for missing files (expected in fallback)
        pass
    return None

def download_month(year, month, timeframe):
    filename = f"{SYMBOL}-{timeframe}-{year}-{month:02d}.zip"
    base_url = get_base_url(year, timeframe)
    url = f"{base_url}/{filename}"
    
    print(f"  [Attempting Monthly] {filename}...")
    df = fetch_file(url)
    if df is not None:
        return [df]
    
    # Fallback to Daily
    print(f"    Monthly missing. Attempting Daily fallback for {year}-{month:02d}...")
    daily_base_url = get_daily_base_url(year, timeframe)
    try:
        days_in_month = pd.Period(f"{year}-{month}").days_in_month
    except:
        return []
    
    daily_urls = []
    for day in range(1, days_in_month + 1):
        d_filename = f"{SYMBOL}-{timeframe}-{year}-{month:02d}-{day:02d}.zip"
        daily_urls.append(f"{daily_base_url}/{d_filename}")
        
    daily_dfs = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_file, u): u for u in daily_urls}
        for future in as_completed(futures):
            res = future.result()
            if res is not None:
                daily_dfs.append(res)
                
    return daily_dfs

def download_and_process(timeframe):
    print(f"\n⬇️ STARTING: {timeframe} ({START_YEAR}-{END_YEAR})")
    all_dfs = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            # Skip future dates
            if year == datetime.now().year and month > datetime.now().month: continue
            
            dfs = download_month(year, month, timeframe)
            if dfs:
                all_dfs.extend(dfs)
                print(f"    ✅ Captured {year}-{month:02d}")
            else:
                print(f"    ❌ NO DATA for {year}-{month:02d}")
            
    if all_dfs:
        print(f"Merging {len(all_dfs)} data blocks...")
        final_df = pd.concat(all_dfs)
        for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        final_df = final_df.dropna(subset=['timestamp', 'close'])
        final_df = final_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        final_df['time'] = pd.to_datetime(final_df['timestamp'], unit='ms')
        
        tf_map = {'1d': 'D1', '4h': 'H4', '1h': 'H1', '30m': 'M30'}
        output_name = tf_map.get(timeframe, timeframe)
        
        parquet_path = DATA_DIR / f"BTCUSDT_{output_name}.parquet"
        final_df.to_parquet(parquet_path)
        print(f"🏆 SAVED: {output_name} to {parquet_path} ({len(final_df)} bars)")
        
        if timeframe == '1d':
             print("🧬 Synthesizing MN1 & W1...")
             final_df.set_index('time', inplace=True)
             df_mn1 = final_df.resample('ME').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
             }).dropna().reset_index()
             df_mn1.to_parquet(DATA_DIR / "BTCUSDT_MN1.parquet")
             
             df_w1 = final_df.resample('W-MON').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
             }).dropna().reset_index()
             df_w1.to_parquet(DATA_DIR / "BTCUSDT_W1.parquet")
             print(f"✅ Synthesis Complete.")
    else:
        print(f"❌ CRITICAL ERROR: No data found for {timeframe}")

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. D1 first (for MN1/W1)
    download_and_process("1d")
    
    # 2. Intraday
    for tf in ["4h", "1h", "30m"]:
        download_and_process(tf)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process Interrupted by User.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n🔥 Fatal Error: {e}")
        sys.exit(1)
