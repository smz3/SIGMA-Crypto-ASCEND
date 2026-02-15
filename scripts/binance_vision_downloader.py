"""
binance_vision_downloader.py

Bypasses API blocks by downloading historical OHLCV data directly from 
Binance Public Data (S3) archives.

Architecture:
1. Download monthly/daily zip files from data.binance.vision
2. Extract CSV, rename columns to SIGMA format
3. Merge and save to Parquet
"""

import requests
import zipfile
import pandas as pd
import io
import os
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Configuration
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["1m", "30m", "1h", "4h", "1d", "1w"]
START_YEAR = 2020
END_YEAR = 2026
DATA_DIR = Path("data/raw")

def download_and_process(timeframe):
    """
    Downloads and merges all monthly/daily klines for a timeframe.
    """
    all_dfs = []
    
    # Base URL for Monthly Klines (Futures UM)
    base_url = f"https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/{timeframe}"
    
    now = datetime.now()
    
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            # Skip future months
            if year == now.year and month > now.month:
                continue
            if year > now.year:
                continue
                
            filename = f"{SYMBOL}-{timeframe}-{year}-{month:02d}.zip"
            url_monthly = f"{base_url}/{filename}"
            
            # Check Monthly first
            try:
                response = requests.get(url_monthly, timeout=5)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        csv_name = z.namelist()[0]
                        with z.open(csv_name) as f:
                            df = pd.read_csv(f, header=None)
                            df = df.iloc[:, :6]
                            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                            all_dfs.append(df)
                            print(f"  Success (Monthly): {filename}")
                            continue # Skip Daily if Monthly found
                
                # Check Daily as Fallback (Check first 5 days only to avoid massive overhead for now)
                # Actually, better to fetch all days of the month
                print(f"  Monthly missing, checking Daily for {year}-{month:02d}...")
                daily_base_url = f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{timeframe}"
                for day in range(1, 32):
                    daily_filename = f"{SYMBOL}-{timeframe}-{year}-{month:02d}-{day:02d}.zip"
                    daily_url = f"{daily_base_url}/{daily_filename}"
                    d_response = requests.get(daily_url, timeout=5)
                    if d_response.status_code == 200:
                        with zipfile.ZipFile(io.BytesIO(d_response.content)) as z:
                            csv_name = z.namelist()[0]
                            with z.open(csv_name) as f:
                                df = pd.read_csv(f, header=None)
                                df = df.iloc[:, :6]
                                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                                all_dfs.append(df)
                                # print(f"    Added Daily: {daily_filename}")
            except Exception as e:
                print(f"  Error on {year}-{month:02d}: {e}")
            except Exception as e:
                print(f"  Failed: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs)
        
        # Total Type Hardening
        for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        final_df = final_df.dropna(subset=['timestamp', 'close'])
        final_df = final_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        final_df['time'] = pd.to_datetime(final_df['timestamp'], unit='ms')
        
        # Mapping to our TF names
        tf_map = {'1d': 'D1', '4h': 'H4', '1h': 'H1', '30m': 'M30'}
        output_name = tf_map.get(timeframe, timeframe)
        
        parquet_path = DATA_DIR / f"BTCUSDT_{output_name}.parquet"
        final_df.to_parquet(parquet_path)
        print(f"✅ Saved global {output_name} history to {parquet_path} ({len(final_df)} bars)")
        
        # Synthesis: If we just finished D1, create MN1 and W1
        if timeframe == '1d':
             print("Synthesizing HTF Contexts (MN1, W1) from D1...")
             final_df.set_index('time', inplace=True)
             
             # 1. Monthly (MN1)
             df_mn1 = final_df.resample('ME').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
             }).dropna().reset_index()
             mn1_path = DATA_DIR / "BTCUSDT_MN1.parquet"
             df_mn1.to_parquet(mn1_path)
             print(f"✅ Saved synthesized MN1 to {mn1_path}")

             # 2. Weekly (W1)
             df_w1 = final_df.resample('W-MON').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
             }).dropna().reset_index()
             w1_path = DATA_DIR / "BTCUSDT_W1.parquet"
             df_w1.to_parquet(w1_path)
             print(f"✅ Saved synthesized W1 to {w1_path}")
    else:
        print(f"❌ No data found for {timeframe}")

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # 1. Fetch D1 first (Anchor for W1/MN1 synthesis)
    download_and_process("1d")
    
    # 2. Resample W1 from D1
    print("Synthesizing W1 from D1...")
    d1_path = DATA_DIR / "BTCUSDT_D1.parquet"
    if d1_path.exists():
        df_d1 = pd.read_parquet(d1_path)
        df_d1.set_index('time', inplace=True)
        df_w1 = df_d1.resample('W-MON').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'timestamp': 'first'
        }).dropna().reset_index()
        df_w1.to_parquet(DATA_DIR / "BTCUSDT_W1.parquet")
        print(f"✅ Saved synthesized W1 ({len(df_w1)} weeks)")

    # 3. Fetch Intra-day
    for tf in ["4h", "1h", "30m"]:
        download_and_process(tf)

if __name__ == "__main__":
    main()
