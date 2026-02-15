from typing import List, Dict
import pandas as pd
from dataclasses import dataclass
from ..strategy.scanner import TradeSignal
from ..risk.sizing import RiskCalculator

@dataclass
class Position:
    ticket: int
    symbol: str
    direction: str
    entry_price: float
    sl: float
    tp: float
    size: float
    open_time: pd.Timestamp
    comment: str
    zone_id: int # Track which zone opened this

@dataclass
class ClosedTrade:
    ticket: int
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    open_time: pd.Timestamp
    close_time: pd.Timestamp
    reason: str

class TradeManager:
    """
    The HANDS.
    Replaces OrderManager.mqh & TrailingStopManager.mqh
    """
    
    def __init__(self, risk_calc: RiskCalculator):
        self.positions: List[Position] = []
        self.ledger: List[ClosedTrade] = []
        self._ticket_counter = 1
        self.risk = risk_calc
        self.account_balance = 10000.0 # Standard Smoke Test Balance
        self.equity_history: List[dict] = []
        
    def execute(self, signal: TradeSignal):
        """Simulate filling an order applying Risk Rules"""
        
        # 1. Calculate Risk Parameters (Size + Buffered SL)
        buffered_sl, size = self.risk.calculate_sl_and_size(
            signal.symbol, 
            signal.entry_price, 
            signal.structure_sl, 
            signal.direction.name, 
            self.account_balance
        )
        
        if size <= 0: return # Invalid trade
        
        # Avoid redundant trades on SAME ZONE if already open
        if any(p.zone_id == signal.zone_id for p in self.positions):
            return

        pos = Position(
            ticket=self._ticket_counter,
            symbol=signal.symbol,
            direction=signal.direction.name,
            entry_price=signal.entry_price,
            sl=buffered_sl,
            tp=signal.tp_price,
            size=size,
            open_time=signal.timestamp,
            comment=f"{signal.tf}#{signal.zone_id} {signal.reason}",
            zone_id=signal.zone_id
        )
        self.positions.append(pos)
        self._ticket_counter += 1
        
    def manage_positions(self, low: float, high: float, current_price: float, current_time: pd.Timestamp):
        """
        Check SL/TP and Trailing Stops using High/Low for triggers.
        """
        still_open = []
        for pos in self.positions:
            closed = False
            exit_price = 0.0
            reason = ""
            
            # Check SL (Bullish) - Hits Low?
            if pos.direction == 'BULLISH' and low <= pos.sl:
               exit_price = pos.sl
               reason = "Stop Loss"
               closed = True
            # Check SL (Bearish) - Hits High?
            elif pos.direction == 'BEARISH' and high >= pos.sl:
               exit_price = pos.sl
               reason = "Stop Loss"
               closed = True
               
            # Check TP (Bullish) - Hits High?
            elif pos.tp > 0:
                if pos.direction == 'BULLISH' and high >= pos.tp:
                   exit_price = pos.tp
                   reason = "Take Profit"
                   closed = True
                # Check TP (Bearish) - Hits Low?
                elif pos.direction == 'BEARISH' and low <= pos.tp:
                   exit_price = pos.tp
                   reason = "Take Profit"
                   closed = True
            
            if closed:
                # Calculate PnL
                if pos.direction == 'BULLISH':
                    trade_pnl = (exit_price - pos.entry_price) * pos.size
                else:
                    trade_pnl = (pos.entry_price - exit_price) * pos.size
                
                self.account_balance += trade_pnl
                
                self.ledger.append(ClosedTrade(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    direction=pos.direction,
                    entry_price=pos.entry_price,
                    exit_price=exit_price,
                    size=pos.size,
                    pnl=trade_pnl,
                    open_time=pos.open_time,
                    close_time=current_time,
                    reason=reason
                ))
            else:
                still_open.append(pos)
                
        self.positions = still_open
        
        # Calculate Floating PnL for MtM Equity
        floating_pnl = 0.0
        for pos in self.positions:
            if pos.direction == 'BULLISH':
                floating_pnl += (current_price - pos.entry_price) * pos.size
            else:
                floating_pnl += (pos.entry_price - current_price) * pos.size
        
        # Track Equity Point (Mark-to-Market)
        self.equity_history.append({
            'timestamp': current_time,
            'equity': self.account_balance + floating_pnl
        })

    def force_close_all(self, current_price: float, current_time: pd.Timestamp):
        """Force-close all open positions at current market price."""
        for pos in self.positions:
            if pos.direction == 'BULLISH':
                trade_pnl = (current_price - pos.entry_price) * pos.size
            else:
                trade_pnl = (pos.entry_price - current_price) * pos.size
            
            self.account_balance += trade_pnl
            self.ledger.append(ClosedTrade(
                ticket=pos.ticket,
                symbol=pos.symbol,
                direction=pos.direction,
                entry_price=pos.entry_price,
                exit_price=current_price,
                size=pos.size,
                pnl=trade_pnl,
                open_time=pos.open_time,
                close_time=current_time,
                reason="Forced Close (End of Sim)"
            ))
        self.positions = []
        # Update final equity
        self.equity_history.append({'timestamp': current_time, 'equity': self.account_balance})
