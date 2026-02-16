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
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["1d", "4h", "1h", "30m"] # 1m skipped for speed unless requested
START_YEAR = 2018
END_YEAR = 2022
DATA_DIR = Path("data/raw")

def get_base_url(year, timeframe):
    """Returns the correct base URL based on year (Hybrid Mode)."""
    if year < 2020:
        return f"https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/{timeframe}"
    else:
        return f"https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/{timeframe}"

def get_daily_base_url(year, timeframe):
    """Returns the correct daily base URL based on year (Hybrid Mode)."""
    if year < 2020:
        return f"https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/{timeframe}"
    else:
        return f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{timeframe}"

def fetch_file(url):
    """Helper to fetch and extract a single zip file."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    df = pd.read_csv(f, header=None)
                    df = df.iloc[:, :6]
                    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    return df
    except Exception:
        pass
    return None

def download_month(year, month, timeframe):
    """
    Attempts to download monthly file. 
    If missing, attempts to download all daily files for that month in parallel.
    """
    filename = f"{SYMBOL}-{timeframe}-{year}-{month:02d}.zip"
    base_url = get_base_url(year, timeframe)
    url = f"{base_url}/{filename}"
    
    # Try Monthly
    df = fetch_file(url)
    if df is not None:
        return [df]
    
    # Fallback to Daily
    print(f"    Missing Monthly {filename}, trying Daily...")
    daily_base_url = get_daily_base_url(year, timeframe)
    days_in_month = pd.Period(f"{year}-{month}").days_in_month
    
    daily_urls = []
    for day in range(1, days_in_month + 1):
        d_filename = f"{SYMBOL}-{timeframe}-{year}-{month:02d}-{day:02d}.zip"
        daily_urls.append(f"{daily_base_url}/{d_filename}")
        
    daily_dfs = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_file, u): u for u in daily_urls}
        for future in as_completed(futures):
            res = future.result()
            if res is not None:
                daily_dfs.append(res)
                
    if not daily_dfs:
        print(f"    ❌ Failed to find data for {year}-{month:02d}")
        
    return daily_dfs

def download_and_process(timeframe):
    print(f"⬇️ Processing {timeframe} ({START_YEAR}-{END_YEAR})...")
    all_dfs = []
    
    # We can also parallelize months if we want, but let's keep it simple: parallel days.
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"  Checking {year}...")
        for month in range(1, 13):
            # Future check
            if year == datetime.now().year and month > datetime.now().month: continue
            
            dfs = download_month(year, month, timeframe)
            all_dfs.extend(dfs)
            
    if all_dfs:
        final_df = pd.concat(all_dfs)
        for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        final_df = final_df.dropna(subset=['timestamp', 'close'])
        final_df = final_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        final_df['time'] = pd.to_datetime(final_df['timestamp'], unit='ms')
        
        # Mapping to SIGMA TF names
        tf_map = {'1d': 'D1', '4h': 'H4', '1h': 'H1', '30m': 'M30'}
        output_name = tf_map.get(timeframe, timeframe)
        
        parquet_path = DATA_DIR / f"BTCUSDT_{output_name}.parquet"
        final_df.to_parquet(parquet_path)
        print(f"✅ Saved {output_name} to {parquet_path} ({len(final_df)} bars)")
        
        # Synthesis Logic for D1 -> MN1, W1
        if timeframe == '1d':
             print("  Synthesizing MN1 & W1...")
             final_df.set_index('time', inplace=True)
             
             # MN1
             df_mn1 = final_df.resample('ME').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
             }).dropna().reset_index()
             df_mn1.to_parquet(DATA_DIR / "BTCUSDT_MN1.parquet")
             print(f"  ✅ Synthesized MN1")

             # W1
             df_w1 = final_df.resample('W-MON').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
             }).dropna().reset_index()
             df_w1.to_parquet(DATA_DIR / "BTCUSDT_W1.parquet")
             print(f"  ✅ Synthesized W1")
    else:
        print(f"❌ No data found for {timeframe}")

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch D1 (and synth MN1/W1)
    download_and_process("1d")
    
    # 2. Fetch Intraday
    for tf in ["4h", "1h", "30m"]:
        download_and_process(tf)

if __name__ == "__main__":
    main()
