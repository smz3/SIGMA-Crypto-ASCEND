import pandas as pd
from simulation.engine.vectorized_backtester import VectorizedBacktester, BacktestConfig
from core.models.structures import SignalDirection

def diagnose():
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframes=["MN1", "W1", "D1", "H4", "H1", "M30"],
        start_date="2022-01-01",
        end_date="2022-03-01",
        initial_balance=100000.0
    )
    
    tester = VectorizedBacktester(config)
    tester.load_data()
    tester.init_modules()
    
    # Run native detection
    tester.run_detection_pipeline()
    
    # Inject a print in the orchestrator to see why it rejects
    orig_allowed = tester.orchestrator.is_trade_allowed
    
    def wrapped_allowed(tf, direction, zone, current_price, probe_price=None):
        allowed, reason, target = orig_allowed(tf, direction, zone, current_price, probe_price=probe_price)
        if direction == SignalDirection.BEARISH and tf == 'H4' and not allowed:
             if "No Authority" not in reason or True: # Force print for research
                 mn1 = tester.orchestrator.states['MN1']
                 w1 = tester.orchestrator.states['W1']
                 d1 = tester.orchestrator.states['D1']
                 print(f"DEBUG: [BEARISH H4] Price: {current_price:.2f} | Probe: {probe_price:.2f} | Allowed: {allowed} | Reason: {reason}")
                 if d1.is_valid and d1.magnet_id != "":
                     mag_fifty = d1.details_magnet_price + (d1.details_magnet_L2 - d1.details_magnet_price) * 0.5
                     print(f"      D1 Magnet: {d1.magnet_id} | Core: {min(d1.details_magnet_L2, mag_fifty):.2f}-{max(d1.details_magnet_L2, mag_fifty):.2f}")
                 if w1.is_valid and w1.magnet_id != "":
                     mag_fifty = w1.details_magnet_price + (w1.details_magnet_L2 - w1.details_magnet_price) * 0.5
                     print(f"      W1 Magnet: {w1.magnet_id} | Core: {min(w1.details_magnet_L2, mag_fifty):.2f}-{max(w1.details_magnet_L2, mag_fifty):.2f}")
        return allowed, reason, target
        
    tester.orchestrator.is_trade_allowed = wrapped_allowed
    
    tester.run_simulation()
    
    # Count bearish trades
    bearish_trades = [t for t in tester.trade_manager.ledger if t.direction == 'BEARISH']
    print(f"\nVerification Complete. Total Bearish Trades: {len(bearish_trades)}")
    for t in bearish_trades[:10]:
        print(f" - {t.open_time} | {t.entry_reason}: Entry {t.entry_price:.2f} | PnL {t.pnl:.2f}")

if __name__ == "__main__":
    diagnose()
