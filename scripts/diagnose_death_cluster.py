import pandas as pd
from simulation.engine.vectorized_backtester import VectorizedBacktester, BacktestConfig
from core.models.structures import SignalDirection

def diagnose_nov_2020():
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframes=["MN1", "W1", "D1", "H4", "H1", "M30"],
        start_date="2020-10-25",
        end_date="2020-11-10",
        initial_balance=100000.0
    )
    
    tester = VectorizedBacktester(config)
    tester.load_data()
    tester.init_modules()
    tester.run_detection_pipeline()
    
    # We want to see the heartbeat precisely around the cluster
    tester.orchestrator._print_heartbeat = lambda t: print(f"[{t}] MN1:{tester.orchestrator.states['MN1'].origin_dir} (Mag:{tester.orchestrator.states['MN1'].magnet_id}) | W1:{tester.orchestrator.states['W1'].origin_dir} | D1:{tester.orchestrator.states['D1'].origin_dir}")
    
    tester.run_simulation()
    
    # Count trades in this window
    trades = tester.trade_manager.ledger
    print(f"\nSimulation for Nov 2020 Complete. Total Trades: {len(trades)}")
    
    # Check for clusters
    df = pd.DataFrame([vars(t) for t in trades])
    if not df.empty:
        df['open_time'] = pd.to_datetime(df['open_time'])
        cluster = df.groupby('open_time').size().sort_values(ascending=False).head(10)
        print("\nTop Entry Clusters:")
        print(cluster)

if __name__ == "__main__":
    diagnose_nov_2020()
