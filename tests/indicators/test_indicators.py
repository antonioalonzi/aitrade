import pandas as pd
import pandas.testing as pdt
import pytest

from indicators import indicators


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
    result = indicators.avg_bid_offer(df)

    # then
    assert result is not None
    pdt.assert_frame_equal(result, pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "high": [505.0, 495.0],
        "low": [495.0, 485.0],
        "open": [508.0, 498.0],
        "close": [502.0, 492.0]
    }))

def test_calculate_atr_from_prices_constant_diff():
    # given
    pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "epic": ["NVIDIA"] * 2,
        "bid_high": [501.0] * 2,
        "bid_low": [499.5] * 2,
        "bid_open": [500.0] * 2,
        "bid_close": [500.8] * 2,
        "offer_high": [501.2] * 2,
        "offer_low": [499.7] * 2,
        "offer_open": [500.2] * 2,
        "offer_close": [501.0] * 2,
        "close_spread": [1.0] * 2,
        "volume": [10.0] * 2
    })

    # when
    res = indicators.atr(df, window=3)

    # then
    assert pytest.approx(res, rel=1e-12) == 2.0
