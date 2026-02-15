import ccxt
import pandas as pd

def test_bybit():
    print("Testing Bybit connectivity...")
    exchange = ccxt.bybit()
    try:
        markets = exchange.load_markets()
        print(f"Success! Loaded {len(markets)} markets from Bybit.")
        return True
    except Exception as e:
        print(f"Bybit failed: {e}")
        return False

def test_binance():
    print("Testing Binance connectivity...")
    exchange = ccxt.binance()
    try:
        markets = exchange.load_markets()
        print(f"Success! Loaded {len(markets)} markets from Binance.")
        return True
    except Exception as e:
        print(f"Binance failed: {e}")
        return False

if __name__ == "__main__":
    b_res = test_binance()
    if not b_res:
        test_bybit()
