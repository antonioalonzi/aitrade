import pandas as pd

from ai_web.controllers.market_data import market_data_ui_aggregator


def test_fill_missing_candles():
    # given
    candles = pd.DataFrame([
        {"datetime": "2026-07-29 09:00:00", "open": 10.0, "high": 15.0, "low": 5.0, "close": 12.0},
        {"datetime": "2026-07-29 09:01:00", "open": 20.0, "high": 25.0, "low": 15.0, "close": 22.0},
        {"datetime": "2026-07-29 09:03:00", "open": 30.0, "high": 35.0, "low": 25.0, "close": 32.0}
    ])

    # when
    result_filled = market_data_ui_aggregator.fill_missing_candles(candles, interval_minutes=1)

    # then
    expected_df = pd.DataFrame([
        {"datetime": "2026-07-29 09:00:00", "open": 10.0, "high": 15.0, "low": 5.0, "close": 12.0},
        {"datetime": "2026-07-29 09:01:00", "open": 20.0, "high": 25.0, "low": 15.0, "close": 22.0},
        {"datetime": "2026-07-29 09:02:00"},
        {"datetime": "2026-07-29 09:03:00", "open": 30.0, "high": 35.0, "low": 25.0, "close": 32.0}
    ])
    pd.testing.assert_frame_equal(result_filled, expected_df)
