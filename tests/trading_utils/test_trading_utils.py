import textwrap
from datetime import datetime

import pandas as pd
import pandas.testing as pdt
import pytest

from trading_utils import trading_utils
from trading_utils.trading_utils import _aggregate_for_ai, atr


def test_calculate_avg_bid_offer():
    # given
    df = pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "epic": ["NVIDIA"] * 2,
        "bid_high": [500.0, 490.0],
        "bid_low": [490.0, 480.0],
        "bid_open": [503.0, 493.0],
        "bid_close": [497.0, 487.0],
        "offer_high": [510.0, 500.0],
        "offer_low": [500.0, 490.0],
        "offer_open": [513.0, 503.0],
        "offer_close": [507.0, 497.0],
        "close_spread": [10, 10],
        "volume": [1.0, 1.0]
    })

    # when
    result = trading_utils.avg_bid_offer(df)

    # then
    assert result is not None
    pdt.assert_frame_equal(result, pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "high": [505.0, 495.0],
        "low": [495.0, 485.0],
        "open": [508.0, 498.0],
        "close": [502.0, 492.0]
    }))

def test_aggregate_for_ai():
    # given
    df = pd.DataFrame({
        "datetime": [
            # Bucket 1: Last 15m (3 ticks)
            "2026-07-29 09:46:00", "2026-07-29 09:50:00", "2026-07-29 10:00:00",
            # Bucket 2: -1h to -15m (3 ticks -> 5m resample)
            "2026-07-29 09:10:00", "2026-07-29 09:20:00", "2026-07-29 09:30:00",
            # Bucket 3: -12h to -1h (3 ticks -> 15m resample)
            "2026-07-29 03:00:00", "2026-07-29 05:00:00", "2026-07-29 07:00:00",
            # Bucket 4: -24h to -12h (3 ticks -> 1h resample)
            "2026-07-28 12:00:00", "2026-07-28 15:00:00", "2026-07-28 18:00:00",
            # Bucket 5: -14d to -24h (3 ticks -> 1D resample)
            "2026-07-20 10:00:00", "2026-07-22 10:00:00", "2026-07-25 10:00:00",
        ],
        "open": [10.0, 20.0, 30.0] * 5,
        "high": [15.0, 25.0, 35.0] * 5,
        "low": [5.0, 15.0, 25.0] * 5,
        "close": [12.0, 22.0, 32.0] * 5,
    })

    # when
    result_str = _aggregate_for_ai(df, datetime.fromisoformat("2026-07-29 10:00:10"))

    # then
    assert result_str == [
        [1784505, "1D", 10.0, 15.0, 5.0, 12.0],
        [1784678, "1D", 20.0, 25.0, 15.0, 22.0],
        [1784937, "1D", 30.0, 35.0, 25.0, 32.0],
        [1785240, "1h", 10.0, 15.0, 5.0, 12.0],
        [1785250, "1h", 20.0, 25.0, 15.0, 22.0],
        [1785261, "1h", 30.0, 35.0, 25.0, 32.0],
        [1785294, "15m", 10.0, 15.0, 5.0, 12.0],
        [1785301, "15m", 20.0, 25.0, 15.0, 22.0],
        [1785308, "15m", 30.0, 35.0, 25.0, 32.0],
        [1785316, "5m", 10.0, 15.0, 5.0, 12.0],
        [1785316, "5m", 20.0, 25.0, 15.0, 22.0],
        [1785317, "5m", 30.0, 35.0, 25.0, 32.0],
        [1785318, "1m", 10.0, 15.0, 5.0, 12.0],
        [1785318, "1m", 20.0, 25.0, 15.0, 22.0],
        [1785319, "1m", 30.0, 35.0, 25.0, 32.0],
    ]


def test_atr():
    # given
    df = pd.DataFrame({
        "datetime": [
            "2026-07-29 09:10:00",
            "2026-07-29 09:46:00",
            "2026-07-29 10:00:00"
        ],
        "open": [10.0, 20.0, 30.0],
        "high": [15.0, 25.0, 35.0],
        "low": [5.0, 15.0, 25.0],
        "close": [12.0, 22.0, 32.0]
    })

    # when
    result = atr(df, 14)

    assert result == pytest.approx(10.41326, abs=1e-4)
