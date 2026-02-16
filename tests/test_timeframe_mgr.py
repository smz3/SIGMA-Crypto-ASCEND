import unittest
import pandas as pd
from datetime import datetime, timedelta
from core.system.timeframe_mgr import TimeframeState

class TestTimeframeManager(unittest.TestCase):
    def setUp(self):
        # Create dummy dataframes
        dates_h1 = pd.date_range(start="2023-01-01", periods=10, freq="1h")
        df_h1 = pd.DataFrame({'close': [100]*10}, index=dates_h1)
        
        dates_d1 = pd.date_range(start="2023-01-01", periods=2, freq="1d")
        df_d1 = pd.DataFrame({'close': [100]*2}, index=dates_d1)
        
        self.data_map = {'H1': df_h1, 'D1': df_d1}
        self.mgr = TimeframeState(self.data_map)

    def test_sync_logic(self):
        """Verify sync_to correctly updates pointers."""
        # Move to 02:30 (Should catch 02:00 candle)
        target_time = datetime(2023, 1, 1, 2, 30)
        self.mgr.sync_to(target_time)
        
        h1_ctx = self.mgr.tfs['H1']
        self.assertEqual(h1_ctx.current_bar_time, datetime(2023, 1, 1, 2, 0))
        self.assertTrue(h1_ctx.is_new_bar, "First sync should trigger new bar")

    def test_new_bar_flag_reset(self):
        """Verify is_new_bar resets on subsequent syncs within same bar."""
        # 1. First sync -> New Bar
        self.mgr.sync_to(datetime(2023, 1, 1, 2, 0))
        self.assertTrue(self.mgr.is_new_bar('H1'))
        
        # 2. Second sync (same time/bar) -> No New Bar
        self.mgr.sync_to(datetime(2023, 1, 1, 2, 30))
        self.assertFalse(self.mgr.is_new_bar('H1'), "Flag should reset")

if __name__ == '__main__':
    unittest.main()
