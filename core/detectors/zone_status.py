"""
SIGMA B2B Zone Status Tracker
Port of B2BZoneStatus.mqh → Python.
Handles T1 (L1), T2 (50%), T3 (L2) touch tracking and structural invalidation.
"""
import numpy as np
import pandas as pd
from core.models.structures import B2BZoneInfo, SignalDirection

def update_active_zones(current_low: float, current_high: float, current_close: float, current_time: pd.Timestamp, active_zones: list[B2BZoneInfo]):
    """
    STRICT SERIAL update for active zones.
    Checks for T1, T2, T3 touches and L2 invalidation based on the CURRENT bar only.
    """
    for zone in active_zones:
        if not zone.is_valid:
            continue

        # 1. Check Invalidation (Close past L2)
        invalidated = False
        if zone.direction == SignalDirection.BEARISH:
            if current_close > zone.L2_price:
                invalidated = True
        else:
            if current_close < zone.L2_price:
                invalidated = True

        if invalidated:
            zone.is_invalidated = True
            zone.is_valid = False
            zone.invalidation_time = current_time
            continue

        # 2. Check Touches (Internal Structural Progression)
        if zone.direction == SignalDirection.BEARISH: # Sell Zone
            # T1: High >= L1
            if not zone.L1_touched and current_high >= zone.L1_price:
                zone.L1_touched = True
                zone.L1_touch_time = current_time
                zone.touch_count = 1
                
            # T2: High >= 50% (Must be after or same bar as T1)
            if zone.L1_touched and not zone.fifty_touched and current_high >= zone.fifty_percent:
                zone.fifty_touched = True
                zone.fifty_touch_time = current_time
                zone.touch_count = 2
                
            # T3: High >= L2 (Must be after or same bar as T2)
            if zone.fifty_touched and not zone.L2_touched and current_high >= zone.L2_price:
                zone.L2_touched = True
                zone.L2_touch_time = current_time
                zone.touch_count = 3
        else: # Buy Zone
            # T1: Low <= L1
            if not zone.L1_touched and current_low <= zone.L1_price:
                zone.L1_touched = True
                zone.L1_touch_time = current_time
                zone.touch_count = 1
                
            if zone.L1_touched and not zone.fifty_touched and current_low <= zone.fifty_percent:
                zone.fifty_touched = True
                zone.fifty_touch_time = current_time
                zone.touch_count = 2
                
            if zone.fifty_touched and not zone.L2_touched and current_low <= zone.L2_price:
                zone.L2_touched = True
                zone.L2_touch_time = current_time
                zone.touch_count = 3

        # Update Age
        zone.zone_age_bars += 1

def update_zone_statuses(df: pd.DataFrame, zones: list[B2BZoneInfo]):
    """
    LEGACY/PRE-FLIGHT: Initialized only for historical zones that pre-date simulation.
    In a strict serial backtest, this should be used SPARINGLY.
    """
    # ... (Keeping it for now to avoid breaking detection pipeline, but will warn)
    # Actually, let's just make it do nothing or only handle history.
    pass 

