import pandas as pd
import pytest

from ai_trader.trading_utils import trading_indicators


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
    result_atr = trading_indicators.atr(df, 14)

    assert result_atr == 10.41


def test_rsi():
    # given
    df = pd.DataFrame({
        "datetime": [
            "2026-07-29 09:10:00",
            "2026-07-29 09:46:00",
            "2026-07-29 10:00:00"
        ] * 10,
        "open": [10.0, 20.0, 30.0] * 10,
        "high": [15.0, 25.0, 35.0] * 10,
        "low": [5.0, 15.0, 25.0] * 10,
        "close": [12.0, 22.0, 32.0] * 10
    })

    # when
    result_atr = trading_indicators.rsi(df, 14)

    assert result_atr == pytest.approx(57.830363, rel=1e-5)
