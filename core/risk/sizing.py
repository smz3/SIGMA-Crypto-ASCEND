from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass
class RiskConfig:
    base_risk_pct: float = 0.01
    max_open_positions: int = 200
    min_margin_level: float = 1.5

@dataclass
class SymbolParams:
    sl_buffer: float       # Absolute price distance (e.g. 200.0 for BTC, 4.0 for Gold)
    min_rr: float = 2.0    # Minimum Risk:Reward required
    
    # Trade Management (BTCUSDT Futures Logic)
    be_activation: float = 0.0 # Points profit to trigger BE
    be_lockin: float = 0.0     # Points profit to lock in
    trail_activation: float = 0.0 # Points profit to start trailing
    trail_distance: float = 0.0   # Distance to trail behind price

class RiskCalculator:
    """
    The SHIELD.
    Replaces RiskManager.mqh
    
    Now handles:
    1. Position Sizing
    2. Structural Buffer Management (Stop Loss Sizing)
    3. Trade Management Parameters
    """
    
    def __init__(self, config: RiskConfig):
        self.cfg = config
        # Symbol Specific definitions (Centralized Risk Parameters)
        self.symbols: Dict[str, SymbolParams] = {
            'BTCUSDT': SymbolParams(
                sl_buffer=200.0,
                be_activation=1500.0,
                be_lockin=150.0,
                trail_activation=2500.0,
                trail_distance=1200.0
            ), 
            'XAUUSD': SymbolParams(sl_buffer=4.0),    
        }
        
    def calculate_sl_and_size(self, symbol: str, entry: float, structure_l2: float, direction: str, account_balance: float) -> Tuple[float, float]:
        """
        Returns: (Buffered_SL_Price, Lot_Size)
        """
        params = self.symbols.get(symbol, SymbolParams(sl_buffer=0.0))
        
        # 1. Calculate Buffered Stop Loss
        if direction == 'BULLISH':
            buffered_sl = structure_l2 - params.sl_buffer
            # Sanity: SL must be below entry for Buy
            if buffered_sl >= entry: buffered_sl = entry - params.sl_buffer
        else: # BEARISH
            buffered_sl = structure_l2 + params.sl_buffer
            # Sanity: SL must be above entry for Sell
            if buffered_sl <= entry: buffered_sl = entry + params.sl_buffer
            
        # 2. Calculate Size
        size = self.calculate_lot_size(account_balance, entry, buffered_sl)
        
        return buffered_sl, size

    def calculate_lot_size(self, account_balance: float, entry: float, sl: float) -> float:
        """
        Calculate position size based on risk % and stop loss distance.
        """
        if entry == sl: return 0.0
        
        risk_amount = account_balance * self.cfg.base_risk_pct
        price_diff = abs(entry - sl)
        
        # Crypto sizing: usually in units of the asset (BTC)
        # Loss = Size * PriceDiff
        # Size = Risk / PriceDiff
        
        if price_diff == 0: return 0.0
        size = risk_amount / price_diff
        return size

    def check_exposure(self, current_trades: list, daily_pnl_pct: float = 0.0) -> bool:
        """
        V6.0 RISK GOVERNOR: The Shield.
        Returns False if risk limits are exceeded.
        """
        # 1. Hard Cap (Concurrency)
        # V5.9.1 Diagnosis revealed 123 concurrent trades caused -99% DD.
        # We cap at 10 to prevent "Consensus Overload".
        MAX_CONCURRENT_TRADES = 10 
        
        if len(current_trades) >= MAX_CONCURRENT_TRADES:
            return False
            
        # 2. Daily Circuit Breaker (Future expansion)
        # if daily_pnl_pct <= -0.06: return False
        
        return True
