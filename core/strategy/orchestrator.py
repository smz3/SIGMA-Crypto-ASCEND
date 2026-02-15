import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from ..models.structures import B2BZoneInfo, SignalDirection, FlowState
# from ..system.timeframe_state import TimeframeState # Avoid circular import if possible, or use TYPE_CHECKING

class StrategyOrchestrator:
    """
    The BRAIN of the SIGMA Strategy.
    Port of MQL5/Include/V5.0/Trading/StrategyOrchestrator.mqh
    """
    
    def __init__(self, tf_state=None):
        self.tf_state = tf_state
        # State containers for each timeframe
        self.states: Dict[str, FlowState] = {
            'MN1': FlowState(),
            'W1': FlowState(),
            'D1': FlowState(),
            'H4': FlowState(),
            'H1': FlowState(),
            'M30': FlowState()
        }
        
    def update_flow_state(self, tf_zones: Dict[str, List[B2BZoneInfo]]):
        """
        Main update method called by Backtester.
        Updates the Narrative Flow for all tiers based on visible zones.
        """
        # Update Hierarchy using pre-grouped zones from Backtester
        for tf in self.states.keys():
            self._update_flow(tf, tf_zones.get(tf, []))

    def _update_flow(self, tf: str, zones: List[B2BZoneInfo]):
        """
        Updates the FlowState for a specific timeframe.
        Simplified Logic for Panic/Smoke Test:
        - Origin = The most recent valid zone.
        """
        state = self.states[tf]
        
        # 1. Reset State? 
        # In a continuous system, we persist. But here we re-evaluate from snapshot.
        # Actually, to be robust, we should find the LATEST created zone that is NOT invalidated.
        
        if not zones:
            return 
            
        # Optimization: Zones are already sorted by time in Backtester
        # latest_valid is the last one in the list that isn't invalidated
        latest_valid = None
        for i in range(len(zones)-1, -1, -1):
            z = zones[i]
            if not z.is_invalidated:
                latest_valid = z
                break
                
        if latest_valid:
            state.origin_id = 1 # Dummy ID
            state.origin_dir = latest_valid.direction
            state.origin_touch_time = latest_valid.zone_created_time # Using creation as partial proxy
            state.is_valid = True
            
            # Check for Magnet (Nearest Opposing Zone)
            # Find nearest opposing zone created AFTER or BEFORE? 
            # Usually Magnet is the structure we are targeting.
            # Simplified: Find nearest opposing zone in future? No, we only see past.
            # Find nearest opposing zone that exists.
            
            # Filter opposing (also from end of list for most recent)
            opposing_zone = None
            for i in range(len(zones)-1, -1, -1):
                z = zones[i]
                if z.direction != state.origin_dir and not z.is_invalidated:
                    opposing_zone = z
                    break
            
            if opposing_zone:
                magnet = opposing_zone
                # Usually nearest by Price.
                # Let's trust the most recent one is the "Response".
                state.magnet_id = 1
                state.details_magnet_L2 = magnet.L2_price
                state.magnet_fifty_touched = magnet.fifty_touched
                state.magnet_L2_touched = magnet.L2_touched
        else:
            state.is_valid = False

    def is_trade_allowed(self, signal_tf: str, direction: SignalDirection, 
                        zone: B2BZoneInfo, entry_price: float, sl_price: float) -> tuple[bool, str, float]:
        """
        The DECISION ENGINE.
        Returns: (Authorized?, Reason, TargetPrice)
        """
        mn1 = self.states['MN1']
        w1 = self.states['W1']
        d1 = self.states['D1']
        
        # === V5.5 GLOBAL SIEGE GUARD ===
        if mn1.is_siege_active and direction != mn1.origin_dir: return False, "Blocked by MN1 Siege", 0.0
        
        # === AUTHORITY CHECK ===
        
        # Helper to calculate 2:1 target if no magnet
        def get_default_target(entry, sl):
            risk = abs(entry - sl)
            if direction == SignalDirection.BULLISH:
                return entry + (risk * 2.0)
            return entry - (risk * 2.0)

        if mn1.is_valid:
            if mn1.origin_dir == direction:
                target = mn1.details_magnet_L2 if mn1.details_magnet_L2 > 0 else get_default_target(entry_price, sl_price)
                return True, "MN1 Flow", target

        # 2. W1 (The Wave)
        if w1.is_valid:
            if w1.origin_dir == direction:
                target = w1.details_magnet_L2 if w1.details_magnet_L2 > 0 else get_default_target(entry_price, sl_price)
                return True, "W1 Flow", target
                     
        # 3. D1 (The Path)
        if d1.is_valid:
            if d1.origin_dir == direction:
                target = d1.details_magnet_L2 if d1.details_magnet_L2 > 0 else get_default_target(entry_price, sl_price)
                return True, "D1 Flow", target
                    
        return False, "No Authority", 0.0
