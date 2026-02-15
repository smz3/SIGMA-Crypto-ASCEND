
"""
scripts/validate_headless.py

Professional detection validation runner.
Loads data -> Runs pipeline -> Prints extensive diagnostic report.
This is the "Black Box Auditor".
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from core.models.structures import DetectionConfig, DetectionContext, SignalDirection, SwingType
from core.detectors.swing_points import detect_swings
from core.detectors.breakouts import detect_breakouts
from core.detectors.b2b_engine import detect_b2b_zones
from core.detectors.zone_status import update_zone_status

def validate_timeframe(tf_name):
    data_path = f'data/raw/BTCUSDT_{tf_name}.parquet'
    if not os.path.exists(data_path):
        print(f"Skipping {tf_name}: Data file not found.")
        return

    print(f"\n=== VALIDATING {tf_name} ===")
    df = pd.read_parquet(data_path)
    print(f"Loaded {len(df)} bars. Range: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")

    # CONFIG
    config = DetectionConfig(
        swing_window=5,      # MT5 Default
        min_age_bars=5       # Filter noise
    )
    
    # 1. SWINGS
    swings = detect_swings(df, config)
    highs = [s for s in swings if s.type == SwingType.HIGH]
    lows = [s for s in swings if s.type == SwingType.LOW]
    print(f"Swings Detected: {len(swings)} (Highs: {len(highs)}, Lows: {len(lows)})")
    
    if len(swings) > 0:
        last_s = swings[-1]
        print(f"Last Swing: Type={last_s.type}, Price={last_s.price:.2f}, Time={df.iloc[last_s.bar_index]['time']}")
    else:
        print("CRITICAL: No swings detected!")

    # 2. BREAKOUTS
    breakouts = detect_breakouts(df, swings, config)
    bull_bos = [b for b in breakouts if b.direction == SignalDirection.BULLISH]
    bear_bos = [b for b in breakouts if b.direction == SignalDirection.BEARISH]
    print(f"Breakouts Detected: {len(breakouts)} (Bull: {len(bull_bos)}, Bear: {len(bear_bos)})")

    # 3. ZONES
    zones = detect_b2b_zones(df, swings, [], config)
    print(f"Zones Formed: {len(zones)}")
    
    # 4. STATUS UPDATE
    # Simulate full tick replay for accurate status
    active_zones = 0
    invalidated_zones = 0
    full_touches = 0
    partial_touches = 0
    
    print("Running Zone Lifecycle Simulation...")
    # Pre-convert times for speed
    bar_times = df['time'].values
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    for i in range(len(df)):
        update_zone_status(
            zones,
            closes[i], highs[i], lows[i], bar_times[i]
        )

    # Analyze Results
    buy_zones = [z for z in zones if z.direction == SignalDirection.BULLISH]
    sell_zones = [z for z in zones if z.direction == SignalDirection.BEARISH]
    
    print(f"  Total BUY Zones: {len(buy_zones)}")
    print(f"  Total SELL Zones: {len(sell_zones)}")
    
    # Check integrity
    bad_zones = []
    for z in zones:
        if z.direction == SignalDirection.BULLISH:
            if z.L1_price >= z.L2_price: bad_zones.append(z)
        else:
            if z.L1_price <= z.L2_price: bad_zones.append(z)
            
    if bad_zones:
        print(f"CRITICAL: {len(bad_zones)} zones have inverted L1/L2 logic!")
        print(f"Example Bad Zone: {bad_zones[0]}")
    else:
        print("PASS: All zones have correct L1/L2 logic.")

    # Check touches
    touched_l1 = [z for z in zones if z.L1_touched]
    touched_l2 = [z for z in zones if z.L2_touched]
    invalidated = [z for z in zones if z.is_invalidated]
    
    print(f"  Zones Touched L1: {len(touched_l1)} ({len(touched_l1)/len(zones)*100:.1f}%)")
    print(f"  Zones Touched L2: {len(touched_l2)}")
    print(f"  Zones Invalidated: {len(invalidated)} ({len(invalidated)/len(zones)*100:.1f}%)")
    
    # Show last 3 zones
    print("\nRecent 3 Zones:")
    for z in zones[-3:]:
        status = "INV" if z.is_invalidated else "ACTIVE"
        dir_str = "BUY" if z.direction == SignalDirection.BULLISH else "SELL"
        print(f"  [{status}] {dir_str} ID={z.zone_id} | Created: {z.zone_created_time} | L1: {z.L1_price:.2f} | L2: {z.L2_price:.2f}")

if __name__ == "__main__":
    validate_timeframe('1d')
    # validate_timeframe('4h') # Uncomment if data ready
