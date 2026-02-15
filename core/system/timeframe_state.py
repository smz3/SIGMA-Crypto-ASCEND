from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
from ..models.structures import DetectionContext

@dataclass
class TimeframeInfo:
    """Historical context for a specific timeframe."""
    name: str  # 'MN1', 'W1', 'D1', etc.
    index: int # Rank (MN1=0, M1=8)
    current_bar_time: datetime
    is_new_bar: bool
    df: pd.DataFrame
    
    # Cache for efficient lookups
    last_processed_idx: int = -1

class TimeframeState:
    """
    The Heartbeat of the Strategy.
    Keeps all timeframes in sync during vectorized backtesting.
    Replaces MQL5's TimeFrameManager.mqh with state-aware logic.
    """
    
    def __init__(self, data_map: Dict[str, pd.DataFrame]):
        """
        Initialize with a dictionary of DataFrames (e.g., {'D1': df_d1, 'H4': df_h4}).
        DataFrames must be indexed by datetime or have a 'time' column.
        """
        self.tfs: Dict[str, TimeframeInfo] = {}
        
        # Rank definitions (matches MQL5)
        self.ranks = {
            'MN1': 0, 'W1': 1, 'D1': 2, 
            'H4': 3, 'H1': 4, 'M30': 5, 
            'M15': 6, 'M5': 7, 'M1': 8
        }
        
        for name, df in data_map.items():
            if name not in self.ranks:
                continue
                
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                    df.set_index('time', inplace=True)
            
            self.tfs[name] = TimeframeInfo(
                name=name,
                index=self.ranks[name],
                current_bar_time=pd.Timestamp.min,
                is_new_bar=True,
                df=df.sort_index()
            )
            
    def sync_to(self, current_time: datetime):
        """
        Fast-forward all timeframes to the current simulation time.
        Updates 'is_new_bar' flags.
        """
        for name, info in self.tfs.items():
            # Find the bar that supposedly closed just before or at current_time
            # In backtesting, we usually peek at the OPENING of the bar or the CLOSE.
            # Here we assume we are iterating through the finest timeframe (e.g. M30).
            
            # Efficient lookup: fast-forward from last known index
            # This avoids O(N) searching every tick
            if info.last_processed_idx == -1:
                start_search = 0
            else:
                start_search = info.last_processed_idx
                
            # Get data slice
            # We want the latest bar that has CLOSED or STARTED by current_time
            # For signal generation, we usually look at COMPLETED bars.
            # So we look for bar_time <= current_time
            
            # Note: Pandas 'asof' is great but slow in loops. 
            # We use direct index access if possible or efficient search.
            
            # For now, let's trust the Caller to provide aligned data or use direct lookup
            # if we are iterating row-by-row in the finest TF.
            
            # Optimization: If we are running on M30 loop, we check higher TFs using index
            try:
                # Find index of current_time or nearest previous
                idx = info.df.index.searchsorted(current_time, side='right') - 1
                
                if idx >= 0:
                    bar_time = info.df.index[idx]
                    if bar_time > info.current_bar_time:
                        info.is_new_bar = True
                        info.current_bar_time = bar_time
                    else:
                        info.is_new_bar = False
                    
                    info.last_processed_idx = idx
                else:
                    info.is_new_bar = False
                    
            except KeyError:
                info.is_new_bar = False

    def get_context(self, tf: str) -> Optional[pd.Series]:
        """Returns the current bar for a specific timeframe."""
        if tf not in self.tfs: return None
        idx = self.tfs[tf].last_processed_idx
        if idx >= 0:
            return self.tfs[tf].df.iloc[idx]
        return None

    def is_new_bar(self, tf: str) -> bool:
        """Did this timeframe just open a new candle?"""
        if tf in self.tfs:
            return self.tfs[tf].is_new_bar
        return False
