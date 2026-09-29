from datetime import datetime

import pandas as pd
import pandas.testing as pdt

from ai_trader.trading_utils import trading_utils


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
    result_avg = trading_utils.avg_bid_offer(df)

    # then
    assert result_avg is not None
    pdt.assert_frame_equal(result_avg, pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
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
            "2026-07-29 09:46:00", "2026-07-29 09:50:00", "2026-07-29 10:00:00",
            # Bucket 2: -1h to -15m (3 ticks -> 5m resample)
            "2026-07-29 09:10:00", "2026-07-29 09:11:00", "2026-07-29 09:30:00",
            # Bucket 3: -12h to -1h (3 ticks -> 15m resample)
            "2026-07-29 03:00:00", "2026-07-29 05:00:00", "2026-07-29 05:10:00",
        ],
        "open": [10.0, 20.0, 30.0] * 3,
        "high": [15.0, 25.0, 35.0] * 3,
        "low": [5.0, 15.0, 25.0] * 3,
        "close": [12.0, 22.0, 32.0] * 3,
        "volume": [100, 200, 300] * 3,
    })

    windows = [
        ['15m', '1m'],
        ['1h', '5m'],
        ['12h', '15m']
    ]

    # when
    result_str = trading_utils._aggregate_for_ai(df, datetime.fromisoformat("2026-07-29 10:00:10"), windows)

    # then
    assert result_str == [
        ["2026-07-29 03:00:00", "15m", 10.0, 15.0, 5.0, 12.0, 100],
        ['2026-07-29 05:00:00', '15m', 20.0, 35.0, 15.0, 32.0, 500],
        ['2026-07-29 09:10:00', '5m', 10.0, 25.0, 5.0, 22.0, 300],
        ["2026-07-29 09:30:00", "5m", 30.0, 35.0, 25.0, 32.0, 300],
        ["2026-07-29 09:46:00", "1m", 10.0, 15.0, 5.0, 12.0, 100],
        ["2026-07-29 09:50:00", "1m", 20.0, 25.0, 15.0, 22.0, 200],
        ["2026-07-29 10:00:00", "1m", 30.0, 35.0, 25.0, 32.0, 300],
    ]


def test_fill_missing_candles():
    # given
    candles = pd.DataFrame([
        {"datetime": "2026-07-29 09:00:00", "open": 10.0, "high": 15.0, "low": 5.0, "close": 12.0},
        {"datetime": "2026-07-29 09:01:00", "open": 20.0, "high": 25.0, "low": 15.0, "close": 22.0},
        {"datetime": "2026-07-29 09:03:00", "open": 30.0, "high": 35.0, "low": 25.0, "close": 32.0}
    ])

    # when
    result_filled = trading_utils.fill_missing_candles(candles, interval_minutes=1)

    # then
    expected_df = pd.DataFrame([
        {"datetime": "2026-07-29 09:00:00", "open": 10.0, "high": 15.0, "low": 5.0, "close": 12.0},
        {"datetime": "2026-07-29 09:01:00", "open": 20.0, "high": 25.0, "low": 15.0, "close": 22.0},
        {"datetime": "2026-07-29 09:02:00"},
        {"datetime": "2026-07-29 09:03:00", "open": 30.0, "high": 35.0, "low": 25.0, "close": 32.0}
    ])
    pd.testing.assert_frame_equal(result_filled, expected_df)
