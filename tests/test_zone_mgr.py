import unittest
from datetime import datetime, timedelta
from core.models.structures import B2BZoneInfo, DetectionContext, SignalDirection
from core.detectors.zone_manager import ZoneManager

class MockContext:
    def __init__(self):
        self.zones = {'H1': []}
        self.config = type('Config', (), {'max_zone_age_bars': 100})()
    
    def get_zones(self, tf):
        if tf not in self.zones: self.zones[tf] = []
        return self.zones[tf]

class TestZoneManager(unittest.TestCase):
    def setUp(self):
        self.ctx = MockContext()
        self.mgr = ZoneManager(self.ctx)
        self.zone1 = B2BZoneInfo(
            zone_id="Z1", timeframe="H1", direction=SignalDirection.BULLISH,
            L1_price=100.0, L2_price=90.0, zone_created_time=datetime(2023, 1, 1)
        )

    def test_deduplication(self):
        """Verify newly ingested zones are deduplicated."""
        self.mgr.update([self.zone1], datetime(2023, 1, 2))
        self.assertEqual(len(self.mgr.active_zones), 1)
        
        # Ingest again
        self.mgr.update([self.zone1], datetime(2023, 1, 2))
        self.assertEqual(len(self.mgr.active_zones), 1, "Duplicate ingestion failed")

    def test_pruning_invalidation(self):
        """Verify invalidated zones are pruned."""
        self.mgr.update([self.zone1], datetime(2023, 1, 1))
        
        # Mark Invalid
        self.zone1.is_invalidated = True
        self.mgr.update([], datetime(2023, 1, 2))
        
        self.assertEqual(len(self.mgr.active_zones), 0, "Pruning failed")

if __name__ == '__main__':
    unittest.main()
