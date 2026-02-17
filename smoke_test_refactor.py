import os
import sys
import pandas as pd
from datetime import datetime

# Root path
root = os.path.abspath(os.path.join(os.getcwd()))
if root not in sys.path:
    sys.path.append(root)

try:
    from core.strategy.orchestrator import StrategyOrchestrator
    from core.models.structures import SignalDirection
    
    print("Testing Orchestrator instantiation...")
    orch = StrategyOrchestrator()
    print("SUCCESS: Orchestrator instantiated.")
    
    print(f"Initial MN1 Latch: {orch.states['MN1'].latch_dir}")
    orch.states['MN1'].latch_dir = SignalDirection.BEARISH
    print(f"Updated MN1 Latch: {orch.states['MN1'].latch_dir}")
    
    print("Refactor appears stable.")
    
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
