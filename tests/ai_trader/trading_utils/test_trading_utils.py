from datetime import datetime

import pandas as pd
import pandas.testing as pdt

from ai_trader.trading_utils import trading_utils


def test_calculate_avg_bid_offer():
    # given
    df = pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00+00:00", "2026-07-29 10:01:00+00:00"],
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
    result_avg = trading_utils.avg_bid_offer(df)

    # then
    assert result_avg is not None
    pdt.assert_frame_equal(result_avg, pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00+00:00", "2026-07-29 10:01:00+00:00"],
        "high": [505.0, 495.0],
        "low": [495.0, 485.0],
        "open": [508.0, 498.0],
        "close": [502.0, 492.0],
        "close_spread": [10, 10],
        "volume": [1.0, 1.0]
    }))

def test_aggregate_for_ai():
    # given
    df = pd.DataFrame({
        "datetime": [
            # Bucket 1: Last 15m (3 ticks)
            "2026-07-29 09:46:00+00:00", "2026-07-29 09:50:00+00:00", "2026-07-29 10:00:00+00:00",
            # Bucket 2: -1h to -15m (3 ticks -> 5m resample)
            "2026-07-29 09:10:00+00:00", "2026-07-29 09:11:00+00:00", "2026-07-29 09:30:00+00:00",
            # Bucket 3: -12h to -1h (3 ticks -> 15m resample)
            "2026-07-29 03:00:00+00:00", "2026-07-29 05:00:00+00:00", "2026-07-29 05:10:00+00:00",
            # Bucket 4: old ticks
            "2026-07-28 00:00:00+00:00", "2026-07-27 00:01:00+00:00", "2026-07-27 00:00:00+00:00",
        ],
        "open": [10.0, 20.0, 30.0] * 4,
        "high": [15.0, 25.0, 35.0] * 4,
        "low": [5.0, 15.0, 25.0] * 4,
        "close": [12.0, 22.0, 32.0] * 4,
        "volume": [100, 200, 300] * 4,
    })

    windows = [
        ['15m', '1min'],
        ['1h', '5min'],
        ['12h', '15min']
    ]

    # when
    result_str = trading_utils.aggregate_for_ai(df, windows)

    # then
    assert result_str == [
        {"t": "2026-07-29 03:00:00", "tf": "15m", "o": 10.0, "h": 15.0, "l": 5.0, "c": 12.0, "v": 100},
        {"t": "2026-07-29 05:00:00", "tf": "15m", "o": 20.0, "h": 35.0, "l": 15.0,"c": 32.0, "v": 500},
        {"t": "2026-07-29 09:10:00", "tf": "5m",  "o": 10.0, "h": 25.0, "l": 5.0, "c": 22.0, "v": 300},
        {"t": "2026-07-29 09:30:00", "tf": "5m",  "o": 30.0, "h": 35.0, "l": 25.0,"c": 32.0, "v": 300},
        {"t": "2026-07-29 09:46:00", "tf": "1m",  "o": 10.0, "h": 15.0, "l": 5.0, "c": 12.0, "v": 100},
        {"t": "2026-07-29 09:50:00", "tf": "1m",  "o": 20.0, "h": 25.0, "l": 15.0,"c": 22.0, "v": 200},
        {"t": "2026-07-29 10:00:00", "tf": "1m",  "o": 30.0, "h": 35.0, "l": 25.0,"c": 32.0, "v": 300},
    ]
