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

def main():
    # Configure logging
    logging.basicConfig(level=logging.ERROR) # Lower noise for production run
    
    # 1. Setup Configuration: 3-Year In-Sample (2020-2023)
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframes=["MN1", "W1", "D1", "H4", "H1", "M30"],
        start_date="2020-01-01",
        end_date="2023-12-31"
    )
    
    # 2. Initialize Backtester
    tester = VectorizedBacktester(config)
    
    # 3. Load Data
    print(f"🚀 Loading BTCUSDT Data ({config.start_date} to {config.end_date})...")
    tester.load_data()
    
    # 4. Run Detection (Strict Serial Prep)
    print("🔍 Detecting Structures...")
    tester.run_detection_pipeline()
    
    # 5. Execute Simulation
    print("🎯 Running In-Sample Validation Simulation (3-Year Block)...")
    tester.run_simulation()
    
    # 6. Report Results
    print("\n📈 Simulation Complete. Generating Reports...")
    ledger = tester.trade_manager.ledger
    equity = tester.trade_manager.equity_history
    
    if not ledger:
        print("❌ No trades executed.")
        return
        
    # Standard CSV Output for Analytics Engine
    reports_dir = Path("research/reports/in_sample")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    trade_df = pd.DataFrame([vars(t) for t in ledger])
    equity_df = pd.DataFrame(equity)
    
    trade_df.to_csv(reports_dir / "trade_log_is.csv", index=False)
    equity_df.to_csv(reports_dir / "equity_curve_is.csv", index=False)
    
    print(f"✅ Saved logs to: {reports_dir}")
    print(f"Total Trades: {len(ledger)}")
    
    # 7. Generate Tearsheet
    try:
        equity_path = str(reports_dir / "equity_curve_is.csv")
        output_path = str(reports_dir / "tearsheet_is_2020_2023.html")
        generate_tearsheet(equity_path, output_path)
        print(f"📄 Tearsheet generated: {output_path}")
    except Exception as e:
        print(f"Warning: Could not generate tearsheet: {e}")

if __name__ == "__main__":
    main()
