import os
import sys
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Ensure script can find the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.engine.vectorized_backtester import VectorizedBacktester, BacktestConfig

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # 1. OOS Configuration (2023-2025)
    # We use 2022 as a warmup year to establish the structural narrative.
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframes=["MN1", "W1", "D1", "H4", "H1", "M30"], 
        start_date="2022-01-01", # WARMUP YEAR
        end_date="2025-12-31",   # OOS END
        initial_balance=10000.0,
        max_open_positions=10 
    )
    
    # 2. Initialize Backtester
    tester = VectorizedBacktester(config)
    
    # 3. Load Data
    print(f"🚀 Loading OOS Data ({config.start_date} to {config.end_date})...")
    tester.load_data()
    
    # 4. Run Detection
    print("🔍 Detecting Structures (OOS Regime)...")
    tester.run_detection_pipeline()
    
    # 5. Execute Simulation
    print("🎯 Running V6.8 Alpha Sentinel OOS Backtest...")
    tester.run_simulation()
    
    # 6. Report Results
    print("\n📈 OOS Simulation Complete. Generating Quant Reports...")
    ledger = tester.trade_manager.ledger
    equity = tester.trade_manager.equity_history
    
    # OOS Filter: Report from 2023-01-01 ONLY
    report_start_dt = pd.Timestamp("2023-01-01")
    ledger = [t for t in ledger if t.open_time >= report_start_dt]
    equity = [e for e in equity if pd.Timestamp(e['timestamp']) >= report_start_dt]

    print(f"OOS Results Period (2023-2025). Trades: {len(ledger)}")
    
    if not ledger:
        print("❌ No trades executed in OOS period.")
        return
        
    reports_dir = Path("research/reports/Test_13A_OOS_AlphaSentinel")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    trade_df = pd.DataFrame([vars(t) for t in ledger])
    equity_df = pd.DataFrame(equity)
    
    trade_df.to_csv(reports_dir / "trade_log.csv", index=False)
    equity_df.to_csv(reports_dir / "equity_curve.csv", index=False)
    
    print(f"✅ Saved OOS logs to: {reports_dir}")
    
    # 7. Advanced Reporting
    try:
        from simulation.engine.reporting import generate_tearsheet, calculate_fractal_metrics, plot_trade_overlay
        
        # A. QuantStats
        equity_path = str(reports_dir / "equity_curve.csv")
        output_path = str(reports_dir / "tearsheet_OOS_Validation.html")
        generate_tearsheet(equity_path, output_path)
        
        # B. Fractal Metrics
        b2b_metrics = calculate_fractal_metrics(ledger)
        print("\n=== OOS FRACTAL EDGE METRICS ===")
        print(b2b_metrics.T)
        b2b_metrics.to_csv(reports_dir / "b2b_stats.csv", index=False)
        
        # C. Visual Verification
        if "H4" in tester.data:
            visual_path = str(reports_dir / "trade_overlay.html")
            plot_trade_overlay(tester.data["H4"], ledger, visual_path)
            
    except Exception as e:
        print(f"Warning: Reporting Error: {e}")

if __name__ == "__main__":
    main()
