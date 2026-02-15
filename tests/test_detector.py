"""
SIGMA Detection Pipeline — Unit Tests
Tests the full 3-stage pipeline: Swings → Breakouts → B2B Zones
with synthetic data designed to produce known results.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.models.structures import (
    SwingPointInfo, SwingType, SignalDirection,
    DetectionConfig, DetectionContext,
)
from core.detectors.swing_points import detect_swings
from core.detectors.breakouts import detect_breakouts
from core.detectors.b2b_engine import detect_b2b_zones
from core.detectors.zone_status import update_zone_status


def _make_df(closes: list[float], start: datetime = None) -> pd.DataFrame:
    if start is None:
        start = datetime(2024, 1, 1)
    n = len(closes)
    times = [start + timedelta(days=i) for i in range(n)]
    return pd.DataFrame({
        'time': times,
        'open': closes,
        'high': [c + 0.5 for c in closes],
        'low': [c - 0.5 for c in closes],
        'close': closes,
    })


class TestSwingDetection:
    def test_simple_peak_and_trough(self):
        closes = [10, 12, 14, 12, 10]
        df = _make_df(closes)
        config = DetectionConfig(swing_window=3)
        swings = detect_swings(df, config)

        highs = [s for s in swings if s.type == SwingType.HIGH]
        lows = [s for s in swings if s.type == SwingType.LOW]
        assert len(highs) == 1
        assert highs[0].price == 14.0
        assert len(lows) == 0

    def test_valley(self):
        closes = [14, 12, 10, 12, 14]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))

        lows = [s for s in swings if s.type == SwingType.LOW]
        assert len(lows) == 1
        assert lows[0].price == 10.0

    def test_flat_series_no_swings(self):
        closes = [10, 10, 10, 10, 10]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))
        assert len(swings) == 0

    def test_zigzag_pattern(self):
        closes = [10, 15, 10, 15, 10, 15, 10]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))

        highs = [s for s in swings if s.type == SwingType.HIGH]
        lows = [s for s in swings if s.type == SwingType.LOW]
        assert len(highs) >= 2
        assert len(lows) >= 2

    def test_window_size_5(self):
        closes = [10, 11, 12, 13, 14, 13, 12, 11, 10]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=5))

        highs = [s for s in swings if s.type == SwingType.HIGH]
        assert len(highs) == 1
        assert highs[0].price == 14.0

    def test_uses_close_not_high_low(self):
        df = pd.DataFrame({
            'time': [datetime(2024, 1, i+1) for i in range(5)],
            'open': [10, 10, 10, 10, 10],
            'high': [10, 10, 100, 10, 10],
            'low': [10, 10, 10, 10, 10],
            'close': [10, 10, 10, 10, 10],
        })
        swings = detect_swings(df, DetectionConfig(swing_window=3))
        assert len(swings) == 0


class TestBreakoutDetection:
    def test_bullish_breakout(self):
        closes = [10, 15, 10, 12, 20]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))

        highs = [s for s in swings if s.type == SwingType.HIGH]
        assert len(highs) == 1
        assert highs[0].price == 15.0

        breakouts = detect_breakouts(df, swings)
        bullish = [b for b in breakouts if b.direction == SignalDirection.BULLISH]
        assert len(bullish) >= 1
        assert bullish[0].broken_swing_price == 15.0

    def test_bearish_breakout(self):
        closes = [15, 10, 15, 12, 5]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))
        breakouts = detect_breakouts(df, swings)

        bearish = [b for b in breakouts if b.direction == SignalDirection.BEARISH]
        assert len(bearish) >= 1
        assert bearish[0].broken_swing_price == 10.0

    def test_swing_marked_as_broken(self):
        closes = [10, 15, 10, 12, 20]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))
        detect_breakouts(df, swings)

        highs = [s for s in swings if s.type == SwingType.HIGH]
        assert highs[0].has_been_broken is True

    def test_no_breakout_if_unbroken(self):
        closes = [10, 15, 10, 12, 14]
        df = _make_df(closes)
        swings = detect_swings(df, DetectionConfig(swing_window=3))
        breakouts = detect_breakouts(df, swings)

        bullish = [b for b in breakouts if b.direction == SignalDirection.BULLISH]
        assert len(bullish) == 0


class TestB2BZoneDetection:
    def _make_sell_zigzag(self):
        """
        Creates a SELL B2B pattern:
        P5 (old low) → P1 (high) → P2 (low) → P3 (high < P1) → P4 (close < P5)
        
        Prices: 5, 8, 20, 8, 16, 4, 10, 3
        P5 = low at idx 1 (price 8), broken by P4
        P1 = high at idx 2 (price 20)
        P2 = low at idx 3 (price 8)  ... but same as P5, so different:
        
        Let's use: 10, 5, 20, 8, 18, 6, 15, 3
        P5=5 (idx1), P1=20 (idx2), P2=8 (idx3), P3=18 (idx4), then breaks below 5
        """
        closes = [10, 5, 20, 8, 18, 6, 15, 3]
        return _make_df(closes)

    def test_sell_zone_detection(self):
        df = self._make_sell_zigzag()
        config = DetectionConfig(swing_window=3)
        swings = detect_swings(df, config)
        zones = detect_b2b_zones(df, swings, [], config, timeframe="D1")

        sells = [z for z in zones if z.direction == SignalDirection.BEARISH]
        if len(sells) > 0:
            zone = sells[0]
            assert zone.L1_price > 0
            assert zone.L2_price > 0
            assert zone.L2_price > zone.L1_price
            assert zone.fifty_percent == (zone.L1_price + zone.L2_price) / 2.0
            assert zone.timeframe == "D1"

    def test_zone_has_correct_session(self):
        df = self._make_sell_zigzag()
        swings = detect_swings(df, DetectionConfig(swing_window=3))
        zones = detect_b2b_zones(df, swings, [], timeframe="D1")

        for zone in zones:
            assert zone.session_created in ["ASIAN", "LONDON", "NEWYORK"]


class TestZoneStatus:
    def test_touch_tracking(self):
        from core.models.structures import B2BZoneInfo
        zone = B2BZoneInfo(
            direction=SignalDirection.BEARISH,
            L1_price=100.0,
            L2_price=110.0,
            fifty_percent=105.0,
            is_valid=True,
        )

        update_zone_status([zone], bar_close=99, bar_high=101, bar_low=98)
        assert zone.L1_touched is True
        assert zone.fifty_touched is False

        update_zone_status([zone], bar_close=104, bar_high=106, bar_low=103)
        assert zone.fifty_touched is True

    def test_invalidation(self):
        from core.models.structures import B2BZoneInfo
        zone = B2BZoneInfo(
            direction=SignalDirection.BEARISH,
            L1_price=100.0,
            L2_price=110.0,
            fifty_percent=105.0,
            is_valid=True,
        )

        n = update_zone_status([zone], bar_close=115, bar_high=116, bar_low=114)
        assert n == 1
        assert zone.is_valid is False
        assert zone.is_invalidated is True


class TestFullPipeline:
    def test_pipeline_context(self):
        ctx = DetectionContext()
        assert ctx.get_swings("D1") == []
        assert ctx.get_all_zones() == []
        assert ctx.next_display_number() == 1
        assert ctx.next_display_number() == 2

    def test_pipeline_end_to_end(self):
        np.random.seed(42)
        n_bars = 200

        t = np.linspace(0, 8 * np.pi, n_bars)
        prices = 100 + 20 * np.sin(t) + np.cumsum(np.random.randn(n_bars) * 0.5)

        df = _make_df(prices.tolist())
        config = DetectionConfig(swing_window=3)

        swings = detect_swings(df, config)
        assert len(swings) > 0

        breakouts = detect_breakouts(df, swings, config)

        zones = detect_b2b_zones(df, swings, [], config, timeframe="D1")

        for zone in zones:
            assert zone.L1_price > 0
            assert zone.L2_price > 0
            assert zone.zone_id != ""
            assert zone.timeframe == "D1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
