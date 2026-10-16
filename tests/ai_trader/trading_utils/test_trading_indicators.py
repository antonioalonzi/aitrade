from datetime import datetime, timedelta

import pandas as pd

from ai_trader.trading_utils import trading_indicators


def test_atr():
    # given
    start_time = datetime(2026, 7, 29, 9, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(15)]

    df = pd.DataFrame({
        "datetime": timestamps,
        "open": [10.0, 20.0, 30.0] * 5,
        "high": [15.0, 25.0, 35.0] * 5,
        "low": [5.0, 15.0, 25.0] * 5,
        "close": [12.0, 22.0, 32.0] * 5
    })

    # when
    result_atr = trading_indicators.atr(df, 14)

    assert result_atr == 14.48


def test_rsi():
    # given
    start_time = datetime(2026, 7, 29, 9, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(15)]

    df = pd.DataFrame({
        "datetime": timestamps,
        "open": [10.0, 20.0, 30.0] * 5,
        "high": [15.0, 25.0, 35.0] * 5,
        "low": [5.0, 15.0, 25.0] * 5,
        "close": [12.0, 22.0, 32.0] * 5
    })

    # when
    result_atr = trading_indicators.rsi(df, 14)

    assert result_atr == 69.21


def test_window_exponential_average():
    # given
    start_time = datetime(2026, 7, 29, 9, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(100)]
    closes = list(range(1, 101))

    df = pd.DataFrame({
        "datetime": timestamps,
        "close": closes,
        "volume": [1000] * 100
    })

    # when
    avg_5min = trading_indicators.window_exponential_average(df, 5, 5)
    avg_15min = trading_indicators.window_exponential_average(df, 15, 5)
    avg_1h = trading_indicators.window_exponential_average(df, 60, 5)

    assert avg_5min == [94.0, 95.0, 96.0, 97.0, 98.0]
    assert avg_15min == [89.0, 90.0, 91.0, 92.0, 93.0]
    assert avg_1h == [67.74, 68.7, 69.66, 70.62, 71.59]
