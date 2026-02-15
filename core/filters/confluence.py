"""
confluence.py

The Multi-Timeframe (MTF) Orchestration Layer for SIGMA.
Integrates structural states across MN1, W1, D1, H4, H1, M30 to 
provide a unified 'Market Context' for signal authorization.
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from core.models.structures import (
    B2BZoneInfo, SwingPointInfo, RawBreakoutInfo, 
    DetectionConfig, SignalDirection
)
from core.detectors.swing_points import detect_swings
from core.detectors.breakouts import detect_breakouts
from core.detectors.b2b_engine import detect_b2b_zones
from core.detectors.zone_status import update_zone_statuses

@dataclass
class MarketState:
    """Snapshot of active structures at a specific moment."""
    timestamp: datetime
    active_origins: Dict[str, Optional[B2BZoneInfo]]  # TF -> Origin Zone
    active_magnets: Dict[str, Optional[B2BZoneInfo]]  # TF -> Magnet Zone
    overall_bias: SignalDirection = SignalDirection.NONE

class ContextOrchestrator:
    def __init__(self, data_dict: Dict[str, pd.DataFrame]):
        """
        data_dict: Map of timeframe name (e.g., 'MN1') to its OHLCV DataFrame.
        """
        self.data_dict = data_dict
        self.structures: Dict[str, List[B2BZoneInfo]] = {}
        self.timeframes = ['MN1', 'W1', 'D1', 'H4', 'H1', 'M30']

    def process_all_timeframes(self, config: DetectionConfig):
        """
        Runs the full detection pipeline across all timeframes.
        """
        for tf in self.timeframes:
            if tf not in self.data_dict:
                print(f"Warning: Data missing for {tf}. Skipping...")
                continue
            
            df = self.data_dict[tf]
            print(f"Orchestrating {tf} ({len(df)} bars)...")
            
            # 1. Swings
            swings = detect_swings(df, config)
            # 2. Breakouts/Labels (Used for filtering, though logic is inside b2b_engine)
            # 3. B2B Zones
            zones = detect_b2b_zones(df, swings, config)
            
            # Injection: Set timeframe on zones
            for z in zones:
                z.timeframe = tf
                
            # 4. Status Tracking (T1-T3 + Invalidation)
            update_zone_statuses(df, zones)
            
            self.structures[tf] = zones
        print("✅ MTF Context Synchronized.")

    def get_market_state(self, timestamp: datetime) -> MarketState:
        """
        Calculates the active structural state for all TFs at a given timestamp.
        Used for point-in-time signal filtering.
        """
        state = MarketState(timestamp=timestamp, active_origins={}, active_magnets={})
        
        for tf in self.timeframes:
            if tf not in self.structures:
                state.active_origins[tf] = None
                state.active_magnets[tf] = None
                continue
            
            zones = self.structures[tf]
            
            # Find the MOST RECENT valid zone created before this timestamp
            valid_zones = [z for z in zones if z.zone_created_time <= timestamp and (z.invalidation_time is None or z.invalidation_time > timestamp)]
            
            if not valid_zones:
                state.active_origins[tf] = None
                state.active_magnets[tf] = None
                continue
                
            # Origin is the latest zone
            latest_zone = valid_zones[-1]
            state.active_origins[tf] = latest_zone
            
            # Magnet is the nearest opposing zone
            opposing = [z for z in valid_zones if z.direction != latest_zone.direction]
            state.active_magnets[tf] = opposing[-1] if opposing else None
            
        return state

    def is_authorized(self, signal_zone: B2BZoneInfo, timestamp: datetime) -> bool:
        """
        The Master Gate: Core logic of 'Conscious Hierarchy'.
        Checks if a signal on one TF is authorized by the Parent timeframes.
        """
        state = self.get_market_state(timestamp)
        
        # 1. Higher TF Trend Alignment (MN1/W1)
        # Rule: M30/H1 signals must not fight the MN1/W1 Origin if both are active.
        for htf in ['MN1', 'W1']:
            parent = state.active_origins[htf]
            if parent:
                # If parent is a strong Sell Origin, we don't buy on M30
                if parent.direction != signal_zone.direction:
                    # Exception: If we are reacting at a HTF Outpost (L1-50%), we can take the reversal
                    pass # TODO: Implement reaction-gate exceptions
                    
        return True # Default to True for now during Phase 4 baseline
