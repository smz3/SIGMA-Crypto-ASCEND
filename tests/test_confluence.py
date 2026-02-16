import unittest
from core.models.structures import B2BZoneInfo, SignalDirection, TF_RANK
from core.detectors.confluence import are_zones_nested, detect_confluence

class TestConfluence(unittest.TestCase):
    def setUp(self):
        # Parent: D1 Bullish
        self.d1_parent = B2BZoneInfo(
            zone_id="D1_PARENT", timeframe="D1", direction=SignalDirection.BULLISH,
            L1_price=2000.0, L2_price=1900.0, tf_rank=TF_RANK['D1']
        )
        # Child: H1 Bullish (Inside)
        self.h1_child = B2BZoneInfo(
            zone_id="H1_CHILD", timeframe="H1", direction=SignalDirection.BULLISH,
            L1_price=1980.0, L2_price=1950.0, tf_rank=TF_RANK['H1']
        )
        # Sibling: D1 (Same Rank)
        self.d1_sibling = B2BZoneInfo(
            zone_id="D1_SIBLING", timeframe="D1", direction=SignalDirection.BULLISH,
            L1_price=1980.0, L2_price=1950.0, tf_rank=TF_RANK['D1']
        )
        # Overlap: H1 Partial Overlap (Should Fail)
        self.h1_overlap = B2BZoneInfo(
            zone_id="H1_OVERLAP", timeframe="H1", direction=SignalDirection.BULLISH,
            L1_price=2050.0, L2_price=1950.0, tf_rank=TF_RANK['H1']
        )

    def test_spatial_nesting(self):
        """Verify strict spatial containment."""
        self.assertTrue(are_zones_nested(self.d1_parent, self.h1_child), "Strict nesting failed")
        self.assertFalse(are_zones_nested(self.d1_parent, self.h1_overlap), "Partial overlap should return False")

    def test_rank_hierarchy(self):
        """Verify TF rank logic."""
        # Same rank cannot be parent
        self.assertFalse(are_zones_nested(self.d1_parent, self.d1_sibling), "Same rank should not nest")
        # Child cannot parent Parent
        self.assertFalse(are_zones_nested(self.h1_child, self.d1_parent), "Lower TF cannot parent Higher TF")

    def test_detect_confluence(self):
        """Verify batch processing."""
        zones = [self.h1_child, self.d1_parent]
        processed = detect_confluence(zones)
        
        child_res = next(z for z in processed if z.zone_id == "H1_CHILD")
        self.assertTrue(child_res.is_inside_parent, "Failed to detect parent")
        self.assertEqual(child_res.parent_zone_id, "D1_PARENT")

if __name__ == '__main__':
    unittest.main()
