import pandas as pd
import numpy as np
import os # Added import
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from core.models.structures import B2BZoneInfo, SignalDirection, DetectionConfig
from core.detectors.swing_points import detect_swings
from core.detectors.breakouts import detect_breakouts
from core.detectors.b2b_engine import detect_b2b_zones
from core.detectors.zone_status import update_active_zones
from core.system.timeframe_mgr import TimeframeState
from core.strategy.orchestrator import StrategyOrchestrator
from core.strategy.scanner import SignalScanner, TradeSignal
from core.execution.trade_manager import TradeManager, Position
from core.risk.sizing import RiskCalculator, RiskConfig

@dataclass
class BacktestConfig:
    symbol: str = "BTCUSDT"
    timeframes: List[str] = ("MN1", "W1", "D1", "H4", "H1", "M30")
    start_date: str = "2020-01-01"
    end_date: str = "2020-12-31" # Smoke Test: 1 Year (2020)
    initial_balance: float = 100000.0
    max_open_positions: int = 100 # V6.0 Risk Governor (Default: High Cap)

class VectorizedBacktester:
    """
    The SIMULATION ENGINE.
    Runs the full SIGMA pipeline over historical data.
    """
    
    def __init__(self, config: BacktestConfig):
        self.cfg = config
        self.data: Dict[str, pd.DataFrame] = {}
        self.zones: Dict[str, List[B2BZoneInfo]] = {}
        
        # Components (Deferred Initialization)
        self.tf_state: Optional[TimeframeState] = None
        self.orchestrator: Optional[StrategyOrchestrator] = None
        self.scanner: Optional[SignalScanner] = None
        
        # Execution & Risk (Can be init immediately)
        self.risk_calc = RiskCalculator(RiskConfig(base_risk_pct=0.01))
        self.trade_manager = TradeManager(self.risk_calc)
        
        self.logger = logging.getLogger("Backtester")
        
    def load_data(self):
        """Loads parquet files for all timeframes."""
        for tf in self.cfg.timeframes:
            # Assuming standard naming convention
            path = f"data/processed/{self.cfg.symbol}_{tf}.parquet" 
            # Fallback to raw if processed not found
            if not os.path.exists(path): 
                path = f"data/raw/{self.cfg.symbol}_{tf}.parquet"
            
            try:
                if not os.path.exists(path):
                    print(f"File not found: {path}")
                    continue
                    
                df = pd.read_parquet(path)
                # Ensure datetime index
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                    df.set_index('time', inplace=True)
                
                # Store FULL data for structural detection context
                self.data[tf] = df
                print(f"Loaded {tf}: {len(df)} bars")
            except Exception as e:
                print(f"Error loading {tf}: {e}")
                
    def init_modules(self):
        """Initialize components that depend on data."""
        if not self.data:
            print("WARNING: No data loaded. Cannot initialize modules.")
            return

        print("Initializing Logic Modules...")
        self.tf_state = TimeframeState(self.data)
        self.orchestrator = StrategyOrchestrator(self.tf_state)
        self.scanner = SignalScanner(self.orchestrator)
        
    def run_detection_pipeline(self):
        """Pre-calculates all structures (Swings, BO, Zones) for efficiency."""
        det_cfg = DetectionConfig() # Default config
        
        print("\n--- Running Detection Pipeline ---")
        for tf, df in self.data.items():
            df_reset = df.reset_index()
            
            swings = detect_swings(df_reset, det_cfg)
            # breakouts = detect_breakouts(df_reset, swings, det_cfg) # Redundant: B2B engine handles this
            zones = detect_b2b_zones(df_reset, swings, tf=tf, config=det_cfg)
            
            # update_zone_statuses(df_reset, zones) # DELETED: Now handled incrementally in simulation loop
            
            self.zones[tf] = zones
            print(f"[{tf}] Detected {len(zones)} zones")
            
    def run_simulation(self):
        """
        The Main Event Loop.
        Iterates over the lowest timeframe (e.g. M30) as the heartbeat.
        OPTIMIZED: Uses stateful zone tracking (pointers).
        """
        if not self.tf_state or not self.orchestrator or not self.scanner:
            self.init_modules()
            
        print("\n--- Starting Simulation ---")
        
        driver_tf = self.cfg.timeframes[-1] 
        driver_data = self.data.get(driver_tf)
        
        if driver_data is None:
            print("Driver Data missing!")
            return
            
        # Optimization: Stateful Zone Tracking
        # Pointer to the next potential new zone for each TF
        pointers = {tf: 0 for tf in self.zones}
        active_zones = {tf: [] for tf in self.zones}
        
        # Slice only the time period specified for the simulation
        sim_data = driver_data[self.cfg.start_date:self.cfg.end_date]
        total_bars = len(sim_data)
        
        # Optimization: use itertuples for 10x speed over iterrows
        for i, row in enumerate(sim_data.itertuples()):
            current_time = row.Index
            if i % 1000 == 0: 
                print(f"Processing... {i}/{total_bars}")
                # print(f"Active Zones: {sum(len(z) for z in active_zones.values())}")
            
            current_price = row.close
            
            # 1. Update Timeframe State
            self.tf_state.sync_to(current_time)
            
            # 2. Update Active Zones (Strict Serial)
            for tf, zones in self.zones.items():
                # A. Add New Zones (Point of Confirmation)
                while pointers[tf] < len(zones):
                    candidate = zones[pointers[tf]]
                    if candidate.zone_created_time <= current_time:
                        active_zones[tf].append(candidate)
                        pointers[tf] += 1
                    else:
                        break 
                
            # B. Update Status based on CURRENT prices (No Lookahead)
            all_active = [z for tf_list in active_zones.values() for z in tf_list]
            update_active_zones(row.low, row.high, row.close, current_time, all_active)

            # C. Prune Invalidated Zones
            for tf in active_zones:
                active_zones[tf] = [z for z in active_zones[tf] if z.is_valid]
                
            simulation_snapshot = [z for tf_list in active_zones.values() for z in tf_list]
            
            # 3. Feed the Orchestrator (Using pre-grouped dict)
            self.orchestrator.update_flow_state(active_zones, current_price, current_time)
            
            # Create a flat snapshot for the scanner (which still needs a list)
            simulation_snapshot = [z for zones in active_zones.values() for z in zones]
            
            # 4. Scan for Signals
            active_ids = {pos.zone_id for pos in self.trade_manager.positions}
            signals = self.scanner.scan(
                self.cfg.symbol, 
                simulation_snapshot, 
                row.low, 
                row.high,
                current_price, 
                current_time,
                active_ids
            )
            
            # 5. Execute Signals
            for sig in signals:
                self.trade_manager.execute(sig)
                
            # 6. Manage Open Positions
            self.trade_manager.manage_positions(
                row.low, 
                row.high, 
                current_price, 
                current_time
            )
            
        print("Simulation Complete. Force-closing remaining positions...")
        self.trade_manager.force_close_all(current_price, current_time)
        print("Simulation Complete.")
        
    def generate_report(self):
        """Outputs the Trade Log and Metrics."""
        trades = self.trade_manager.ledger
        history = self.trade_manager.equity_history
        
        print(f"\nTotal Trades: {len(trades)}")
        
        # 1. Save Closed Trades Ledger
        if trades:
            df_trades = pd.DataFrame([vars(t) for t in trades])
            df_trades.to_csv("research/reports/trade_log.csv", index=False)
            print("Trade Log saved to research/reports/trade_log.csv")
            
        # 2. Save Equity Curve
        if history:
            df_equity = pd.DataFrame(history)
            df_equity.to_csv("research/reports/equity_curve.csv", index=False)
            print("Equity Curve saved to research/reports/equity_curve.csv")

if __name__ == "__main__":
    # Smoke Test
    print("Initializing Backtester...")
    config = BacktestConfig()
    bt = VectorizedBacktester(config)
    
    print("1. Loading Data...")
    bt.load_data()
    
    print("2. Running Detection Pipeline...")
    bt.run_detection_pipeline()
    
    print("3. Running Simulation...")
    bt.run_simulation()
    
    print("4. Generating Report...")
    bt.generate_report()
    
    print("Backtest Complete.")
