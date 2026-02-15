"""
SIGMA B2B Zone Status Tracker
Port of B2BZoneStatus.mqh → Python.
Handles T1 (L1), T2 (50%), T3 (L2) touch tracking and structural invalidation.
"""
import numpy as np
import pandas as pd
from core.models.structures import B2BZoneInfo, SignalDirection

def update_zone_statuses(df: pd.DataFrame, zones: list[B2BZoneInfo]):
    """
    Optimized zone status updater using NumPy vectorization where possible.
    """
    if not zones:
        return

    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    times = df['time'].values
    n = len(df)

    for zone in zones:
        start_idx = zone.created_bar_index + 1
        if start_idx >= n:
            continue
            
        # Get slice of data from creation onwards
        h_slice = highs[start_idx:]
        l_slice = lows[start_idx:]
        c_slice = closes[start_idx:]
        t_slice = times[start_idx:]
        
        # 1. Find Invalidation Index (First close past L2)
        if zone.direction == SignalDirection.BEARISH:
            inv_hits = np.where(c_slice > zone.L2_price)[0]
        else:
            inv_hits = np.where(c_slice < zone.L2_price)[0]
            
        last_idx = len(c_slice)
        if len(inv_hits) > 0:
            last_idx = inv_hits[0]
            zone.is_invalidated = True
            zone.is_valid = False
            zone.invalidation_time = t_slice[last_idx]
            
        # 2. Process Touches strictly before invalidation
        h_valid = h_slice[:last_idx+1]
        l_valid = l_slice[:last_idx+1]
        t_valid = t_slice[:last_idx+1]
        
        if zone.direction == SignalDirection.BEARISH: # Sell Zone
            # T1: High >= L1
            t1_hits = np.where(h_valid >= zone.L1_price)[0]
            if len(t1_hits) > 0:
                zone.L1_touched = True
                zone.L1_touch_time = t_valid[t1_hits[0]]
                zone.touch_count = 1
                
                # T2: High >= 50% (after T1)
                t2_hits = np.where(h_valid[t1_hits[0]:] >= zone.fifty_percent)[0]
                if len(t2_hits) > 0:
                    zone.fifty_touched = True
                    zone.fifty_touch_time = t_valid[t1_hits[0] + t2_hits[0]]
                    zone.touch_count = 2
                    
                    # T3: High >= L2 (after T2)
                    t3_hits = np.where(h_valid[t1_hits[0] + t2_hits[0]:] >= zone.L2_price)[0]
                    if len(t3_hits) > 0:
                        zone.L2_touched = True
                        zone.L2_touch_time = t_valid[t1_hits[0] + t2_hits[0] + t3_hits[0]]
                        zone.touch_count = 3
        else: # Buy Zone
            # T1: Low <= L1
            t1_hits = np.where(l_valid <= zone.L1_price)[0]
            if len(t1_hits) > 0:
                zone.L1_touched = True
                zone.L1_touch_time = t_valid[t1_hits[0]]
                zone.touch_count = 1
                
                t2_hits = np.where(l_valid[t1_hits[0]:] <= zone.fifty_percent)[0]
                if len(t2_hits) > 0:
                    zone.fifty_touched = True
                    zone.fifty_touch_time = t_valid[t1_hits[0] + t2_hits[0]]
                    zone.touch_count = 2
                    
                    t3_hits = np.where(l_valid[t1_hits[0] + t2_hits[0]:] <= zone.L2_price)[0]
                    if len(t3_hits) > 0:
                        zone.L2_touched = True
                        zone.L2_touch_time = t_valid[t1_hits[0] + t2_hits[0] + t3_hits[0]]
                        zone.touch_count = 3

        # Zone Age Calculation
        zone.zone_age_bars = last_idx
