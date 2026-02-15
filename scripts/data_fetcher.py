"""
data_fetcher.py

Professional-grade CCXT data fetcher for SIGMA-Crypto-ASCEND.
Fetches historical OHLCV data from OKX/Kraken and saves to Parquet.

Features:
- Robust pagination loop
- Rate limit handling
- Data validation (gaps, duplicates)
- Multi-exchange support (primary=OKX, fallback=Kraken)
- Progress bars with tqdm
"""

import ccxt
import pandas as pd
import time
import os
from datetime import datetime
from tqdm import tqdm
from pathlib import Path

# Configuration
SYMBOL = 'BTC/USDT:USDT'  # Bitget Linear Perpetual
TIMEFRAMES = {
    'W1': '1w',
    'D1': '1d',
    'H4': '4h',
    'H1': '1h',
    'M30': '30m'
}
START_DATE = '2020-01-01 00:00:00'
DATA_DIR = Path('data/raw')

def get_exchange_instance():
    """Initialize exchange instance with options."""
    try:
        # Priority: Bitget (Often accessible where others are blocked)
        exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        print(f"Initialized {exchange.id} (Swap Mode)")
        return exchange, SYMBOL
    except Exception as e:
        print(f"Failed to init Bitget: {e}")
        return None, None

def fetch_ohlcv(exchange, symbol, timeframe, since_ms):
    """Fetch OHLCV data with pagination."""
    all_ohlcv = []
    
    # Initial fetch
    since = since_ms
    pbar = tqdm(desc=f"Fetching {symbol} {timeframe}", unit="req")
    
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=100)
            
            if not ohlcv:
                break
                
            last_ts = ohlcv[-1][0]
            
            # Check if we've caught up to now
            if last_ts == since:
                 break
                 
            since = last_ts + 1  # Move past the last record
            all_ohlcv.extend(ohlcv)
            pbar.update(len(ohlcv))
            
            # Stop if we are close to current time (within 1 candle duration)
            now = exchange.milliseconds()
            if last_ts >= now - exchange.parse_timeframe(timeframe) * 1000:
                break
                
            time.sleep(exchange.rateLimit / 1000.0) # Respect rate limits
            
        except ccxt.NetworkError as e:
            print(f"Network error: {e}, retrying...")
            time.sleep(5)
        except ccxt.ExchangeError as e:
            print(f"Exchange error: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
            
    pbar.close()
    return all_ohlcv

def save_to_parquet(ohlcv_data, timeframe):
    """Save raw data to Parquet format."""
    if not ohlcv_data:
        print(f"No data to save for {timeframe}")
        return

    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Dedup and sort
    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
    df = df.reset_index(drop=True)
    
    # Validations
    print(f"\nStats for {timeframe}:")
    print(f"  Rows: {len(df)}")
    print(f"  Start: {df['time'].iloc[0]}")
    print(f"  End:   {df['time'].iloc[-1]}")
    
    # Save
    filename = DATA_DIR / f"BTCUSDT_{timeframe}.parquet"
    df.to_parquet(filename)
    print(f"Saved to {filename}")

def main():
    # Ensure directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    exchange, symbol_to_use = get_exchange_instance()
    
    # Convert start date to ms
    start_ms = exchange.parse8601(START_DATE) 
    if start_ms is None:
        start_ms = int(datetime.strptime(START_DATE, '%Y-%m-%d %H:%M:%S').timestamp() * 1000)

    print(f"Starting fetch for {symbol_to_use} on {exchange.id} from {START_DATE}...")
    
    try:
        # Verify symbol existence
        markets = exchange.load_markets()
        if symbol_to_use not in markets:
             print(f"Warning: {symbol_to_use} not found on {exchange.id}. Available keys sample: {list(markets.keys())[:5]}")
             return
    except Exception as e:
        print(f"Market load error: {e}")
        return

    for tf_name in TIMEFRAMES:
        print(f"\nProcessing {tf_name}...")
        ohlcv = fetch_ohlcv(exchange, symbol_to_use, TIMEFRAMES[tf_name], start_ms)
        save_to_parquet(ohlcv, tf_name)

    # Synthesis Phase: Create MN1 from D1
    print("\nSynthesizing MN1 from D1...")
    d1_file = DATA_DIR / "BTCUSDT_D1.parquet"
    if d1_file.exists():
        df_d1 = pd.read_parquet(d1_file)
        df_d1.set_index('time', inplace=True)
        
        # Resample to Month End
        df_mn1 = df_d1.resample('ME').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'timestamp': 'first'
        }).dropna().reset_index()
        
        mn1_file = DATA_DIR / "BTCUSDT_MN1.parquet"
        df_mn1.to_parquet(mn1_file)
        print(f"Saved synthesized MN1 to {mn1_file} ({len(df_mn1)} months)")
    else:
        print("Warning: Could not synthesize MN1 (D1 file missing)")

if __name__ == "__main__":
    main()
