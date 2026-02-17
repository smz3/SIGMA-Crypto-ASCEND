import os
import sys
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Ensure script can find the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.engine.vectorized_backtester import VectorizedBacktester, BacktestConfig
from simulation.engine.reporting import generate_tearsheet

import argparse

def main():
    parser = argparse.ArgumentParser(description="Run SIGMA Backtest")
    parser.add_argument("--test-id", type=str, default="debug_run", help="ID for the test run (folder name)")
    args = parser.parse_args()
    
    test_id = args.test_id
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # 1. Setup Configuration (Phase 10-C: Redundancy Filter)
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframes=["MN1", "W1", "D1", "H4", "H1", "M30"], # Full Alpha + Governor + Redundancy
        start_date="2018-01-01", # Warmup
        end_date="2022-12-31", # 3 Year In-Sample
        initial_balance=10000.0,
        max_open_positions=10 # HARD CAP: Governor Active
    )
    
    # 2. Initialize Backtester
    tester = VectorizedBacktester(config)
    
    # 3. Load Data
    print(f"🚀 Loading {config.symbol} Data ({config.start_date} to {config.end_date})...")
    tester.load_data()
    
    # 4. Run Detection (Strict Serial Prep)
    print("🔍 Detecting Structures (Fractal Geometry)...")
    tester.run_detection_pipeline()
    
    # 5. Execute Simulation
    print("🎯 Running Strict Serial Backtest (Phase 10-C: Redundancy Filter)...")
    tester.run_simulation()
    
    # 6. Report Results
    print("\n📈 Simulation Complete. Generating Quant Reports...")
    ledger = tester.trade_manager.ledger
    equity = tester.trade_manager.equity_history
    
    # V5.9 Verification: Filter Results (2020-2022)
    # We ran from 2018 for warmup, but only report from 2020.
    report_start_dt = pd.Timestamp("2020-01-01")
    ledger = [t for t in ledger if t.open_time >= report_start_dt]
    equity = [e for e in equity if pd.Timestamp(e['timestamp']) >= report_start_dt]

    print(f"Filtered Results for Report Period (2020-2022). Trades: {len(ledger)}")
    
    if not ledger:
        print("❌ No trades executed.")
        return
        
    # Standard CSV Output for QuantStats
    reports_dir = Path(f"research/reports/{test_id}") # ISOLATED OUTPUT
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    trade_df = pd.DataFrame([vars(t) for t in ledger])
    equity_df = pd.DataFrame(equity)
    
    trade_df.to_csv(reports_dir / "trade_log.csv", index=False)
    equity_df.to_csv(reports_dir / "equity_curve.csv", index=False)
    
    print(f"✅ Saved logs to: {reports_dir}")
    print(f"Total Trades: {len(ledger)}")
    
    # 7. Advanced Reporting
    try:
        from simulation.engine.reporting import generate_tearsheet, calculate_fractal_metrics, plot_trade_overlay
        
        # A. QuantStats
        equity_path = str(reports_dir / "equity_curve.csv")
        output_path = str(reports_dir / "tearsheet_Phase10C_Redundancy.html")
        generate_tearsheet(equity_path, output_path)
        
        # B. Fractal Metrics (B2B Edge)
        b2b_metrics = calculate_fractal_metrics(ledger)
        print("\n=== FRACTAL EDGE METRICS ===")
        print(b2b_metrics.T)
        b2b_metrics.to_csv(reports_dir / "b2b_stats.csv", index=False)
        
        # C. Visual Verification (Overlay)
        # We need price data for the chart. Let's use H4 data from the tester.
        if "H4" in tester.data:
            visual_path = str(reports_dir / "trade_overlay.html")
            plot_trade_overlay(tester.data["H4"], ledger, visual_path)
            
    except Exception as e:
        print(f"Warning: Reporting Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
