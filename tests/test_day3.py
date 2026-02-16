import unittest
from datetime import datetime
import pandas as pd
from core.models.structures import B2BZoneInfo, SignalDirection, FlowState
from core.strategy.orchestrator import StrategyOrchestrator

class TestStrategyOrchestratorV59(unittest.TestCase):

    def setUp(self):
        self.orch = StrategyOrchestrator()
        # Mock MN1 State for tests
        self.mn1_origin = B2BZoneInfo(
            zone_id="MN1_ORIGIN", timeframe="MN1", direction=SignalDirection.BULLISH,
            L1_price=1000.0, L2_price=900.0, zone_created_time=pd.Timestamp("2023-01-01"),
            L1_touch_time=pd.Timestamp("2023-01-02"), L1_touched=True
        )
        self.mn1_magnet = B2BZoneInfo(
            zone_id="MN1_MAGNET", timeframe="MN1", direction=SignalDirection.BEARISH,
            L1_price=1200.0, L2_price=1250.0, zone_created_time=pd.Timestamp("2023-01-01"),
            L1_touch_time=pd.Timestamp("2023-01-05"), L1_touched=True, L2_touched=False, fifty_touched=True
        )

    def test_bulldozer_mode(self):
        """V5.9: Siege active should ignore opposing magnet."""
        # Setup Siege
        self.orch.states['MN1'].origin_id = "MN1_ORIGIN"
        self.orch.states['MN1'].origin_dir = SignalDirection.BULLISH
        self.orch.states['MN1'].magnet_id = "MN1_MAGNET"
        self.orch.states['MN1'].is_siege_active = True
        self.orch.states['MN1'].is_valid = True

        # Signal inside MN1 Magnet
        signal_zone = B2BZoneInfo(
            zone_id="SIG_1", timeframe="H4", direction=SignalDirection.BULLISH,
            L1_price=1210.0, L2_price=1205.0, zone_created_time=pd.Timestamp("2023-01-10")
        )

        # Check Roadblock logic directly
        zones = [self.mn1_magnet]
        blocker = self.orch._is_inside_opposing_zone(
            "H4", SignalDirection.BULLISH, 1220.0, zones, global_check=True, siege_magnet_id="MN1_MAGNET"
        )
        
        self.assertEqual(blocker, "", "Bulldozer Mode failed: Should ignore siege magnet")

        # Disable Siege -> Should block
        blocker_no_siege = self.orch._is_inside_opposing_zone(
            "H4", SignalDirection.BULLISH, 1220.0, zones, global_check=True, siege_magnet_id=""
        )
        self.assertEqual(blocker_no_siege, "MN1_MAGNET", "Normal Mode failed: Should block")

    def test_magnet_fade_w1(self):
        """V5.8: W1 Magnet Fade Logic."""
        # MN1 valid, W1 valid, Price at W1 Magnet Core
        self.orch.states['MN1'].is_valid = True
        self.orch.states['MN1'].origin_dir = SignalDirection.BULLISH
        
        w1_magnet = B2BZoneInfo(
            zone_id="W1_MAGNET", timeframe="W1", direction=SignalDirection.BEARISH,
            L1_price=1100.0, L2_price=1150.0, fifty_touched=True, L2_touched=True,
            zone_created_time=pd.Timestamp("2023-01-05")
        )
        self.orch.states['W1'].is_valid = True
        self.orch.states['W1'].origin_dir = SignalDirection.BULLISH
        self.orch.states['W1'].magnet_id = "W1_MAGNET"
        self.orch.states['W1'].details_magnet_price = 1100.0
        self.orch.states['W1'].details_magnet_L2 = 1150.0
        self.orch.states['W1'].magnet_fifty_touched = True
        
        # Signal: Bearish Fade at 1140 (Inside Core)
        signal_zone = B2BZoneInfo(
            zone_id="SIG_FADE", timeframe="H4", direction=SignalDirection.BEARISH,
            L1_price=1140.0, L2_price=1145.0, zone_created_time=pd.Timestamp("2023-01-10")
        )
        
        allowed, reason, target = self.orch.is_trade_allowed("H4", SignalDirection.BEARISH, signal_zone, 1140.0)
        self.assertTrue(allowed, f"Magnet Fade failed: {reason}")
        self.assertIn("W1 Magnet Fade", reason)

if __name__ == '__main__':
    unittest.main()
