"""
run_phase_4_simulation.py

The main entry point for Phase 4 of SIGMA-Crypto-ASCEND.
Runs the full multi-timeframe backtest and generates a structural tearsheet.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Ensure script can find the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models.structures import DetectionConfig
from core.filters.confluence import ContextOrchestrator
from simulation.engine.vectorized_backtester import BacktestEngine
from simulation.engine.reporting import ReportEngine

# Paths
DATA_DIR = Path("data/raw")

def run_simulation():
    # 1. Load Data
    print("🚀 Initializing SIGMA Phase 4 Research Lab...")
    timeframes = ['MN1', 'W1', 'D1', 'H4', 'H1', 'M30']
    data_dict = {}
    
    for tf in timeframes:
        path = DATA_DIR / f"BTCUSDT_{tf}.parquet"
        if path.exists():
            data_dict[tf] = pd.read_parquet(path)
        else:
            print(f"  Warning: {tf} parquet not found.")

    if not data_dict:
        print("❌ Error: No data found in data/raw. Run binance_vision_downloader.py first.")
        return

    # 2. Orchestration (Detection + Synchronization)
    orchestrator = ContextOrchestrator(data_dict)
    config = DetectionConfig() # Default institutional config
    orchestrator.process_all_timeframes(config)

    # 3. Backtesting (The Brain)
    engine = BacktestEngine(risk_per_trade=1.0)
    
    # We backtest M30 as the sniper timeframe
    if 'M30' in data_dict:
        print("\n🎯 Running Baseline Simulation on M30 (Sniper Layer)...")
        m30_df = data_dict['M30']
        m30_zones = orchestrator.structures.get('M30', [])
        
        # This is a RAW BASELINE (No HTF filtering yet to establish a control group)
        engine.run(m30_df, m30_zones, 'M30')
    else:
        print("Skipping M30 backtest (data missing).")

    # 4. Professional Reporting
    perf = engine.get_performance_summary()
    if "trades" in perf:
        reporter = ReportEngine(perf['trades'])
        reporter.print_report()
    else:
        print(perf.get("status", "No trades executed."))

if __name__ == "__main__":
    run_simulation()
