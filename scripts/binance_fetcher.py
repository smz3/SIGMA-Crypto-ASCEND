import ccxt
import pandas as pd
import yaml
import os
import time
from datetime import datetime

def load_config():
    with open('config/binance_config.yaml', 'r') as f:
        return yaml.safe_load(f)

def fetch_ohlcv(exchange, symbol, timeframe, limit=1000):
    print(f"Fetching {timeframe} data for {symbol}...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {timeframe}: {e}")
            time.sleep(2)
    return None

def main():
    config = load_config()
    exchange_id = config.get('exchange', 'binance')
    
    # Initialize exchange with optional proxy support
    exchange_params = {
        'enableRateLimit': True,
        # 'proxies': {'http': 'http://your-proxy', 'https': 'https://your-proxy'} 
    }
    
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class(exchange_params)
    
    symbol = config['symbol']
    timeframes = config['timeframes']
    raw_dir = config['storage']['raw_dir']
    fmt = config['storage']['format']
    
    os.makedirs(raw_dir, exist_ok=True)
    
    for tf in timeframes:
        df = fetch_ohlcv(exchange, symbol, tf, limit=config.get('fetch_limit', 1000))
        if df is not None:
            # Clean symbol for filename
            clean_symbol = symbol.replace('/', '_')
            filename = f"{clean_symbol}_{tf}.{fmt}"
            filepath = os.path.join(raw_dir, filename)
            
            if fmt == 'parquet':
                df.to_parquet(filepath, index=False)
            else:
                df.to_csv(filepath, index=False)
            
            print(f"Saved {len(df)} rows to {filepath}")
            # Respect rate limits
            time.sleep(exchange.rateLimit / 1000)

if __name__ == "__main__":
    main()
