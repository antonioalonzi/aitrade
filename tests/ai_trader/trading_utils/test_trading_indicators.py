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


def test_window_average():
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
    avg_5min = trading_indicators.window_average(df, '5min')
    avg_15min = trading_indicators.window_average(df, '15min')
    avg_1h = trading_indicators.window_average(df, '1h')

    assert avg_5min == 98
    assert avg_15min == 93
    assert avg_1h == 70.5
