from typing import List, Optional
from dataclasses import dataclass
import pandas as pd
from ..models.structures import B2BZoneInfo, SignalDirection
from .orchestrator import StrategyOrchestrator

@dataclass
class TradeSignal:
    zone_id: int
    tf: str
    symbol: str
    direction: SignalDirection
    entry_price: float
    structure_sl: float # RAW L2 (No Buffer)
    tp_price: float
    reason: str
    timestamp: pd.Timestamp

class SignalScanner:
    """
    The EYES of the Strategy.
    Replaces TradeSignalGenerator.mqh
    
    Now PURE: Reports Structural Levels Only.
    """
    
    def __init__(self, orchestrator: StrategyOrchestrator):
        self.brain = orchestrator
        
    def scan(self, symbol: str, zones: List[B2BZoneInfo], current_price: float, current_time: pd.Timestamp, active_zone_ids: set) -> List[TradeSignal]:
        signals = []
        
        # We only look at FRESH zones that just triggered T1/T2/T3
        # In a vectorized backtest, we might iterate through all valid zones
        
        # Optimization: Only scan zones that are within price proximity
        # or relevant for the current price action.
        # For a smoke test, we can filter for zones where price is 'near' L1.
        
        for z in zones:
            if not z.is_valid: continue
            
            # Intersection Filter: Does this bar's range touch the L1 Price?
            # Also require a small buffer or "Proximity" if we allow limit orders.
            # For now, let's use actual touch of the bar range.
            # row is not available here, we need to pass low/high to scan or use current_price.
            # Let's use a VERY tight proximity to current_price (e.g. 0.1%) 
            # to simulate 'price interacting with zone'.
            if abs(current_price - z.L1_price) / current_price > 0.002: # 0.2% buffer
                continue

            # NEW: Prevent redundant trades on the same zone if it's already open
            if z.zone_id in active_zone_ids:
                continue

            # 2. Ask Brain
            allowed, reason, target = self.brain.is_trade_allowed(
                z.timeframe, z.direction, z, z.L1_price, z.L2_price
            )
            
            if allowed:
                sig = TradeSignal(
                    zone_id=z.zone_id,
                    tf=z.timeframe,
                    symbol=symbol,
                    direction=z.direction,
                    entry_price=z.L1_price,
                    structure_sl=z.L2_price,
                    tp_price=target,
                    reason=reason,
                    timestamp=current_time
                )
                signals.append(sig)
                
        return signals
