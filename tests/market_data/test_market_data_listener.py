from datetime import datetime

import pandas as pd
from pandas.testing import assert_frame_equal

from market_data.market_data_listener import MarketDataListener
from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_repository import MarketDataRepository


def test_handle(listener: MarketDataListener, market_data_repository: MarketDataRepository, memory_info: MarketDataInMemoryInfo):
    # given
    t_min1_a = datetime(2026, 8, 2, 10, 0, 15)
    t_min1_b = datetime(2026, 8, 2, 10, 0, 45)
    t_min2_a = datetime(2026, 8, 2, 10, 1, 5)

    # when --- Minute 1: 10:00 ---
    listener._handle("EPIC:NVDA", {"BID": 120.0, "OFFER": 120.5, "MARKET_STATE": "TRADEABLE"}, t_min1_a)
    listener._handle("EPIC:NVDA", {"BID": 122.0, "OFFER": 122.8, "MARKET_STATE": "TRADEABLE"}, t_min1_b)

    listener._handle("EPIC:AMD", {"BID": 140.0, "OFFER": 140.4, "MARKET_STATE": "TRADEABLE"}, t_min1_a)
    listener._handle("EPIC:AMD", {"BID": 139.5, "OFFER": 140.0, "MARKET_STATE": "TRADEABLE"}, t_min1_b)

    # then
    assert len(market_data_repository.get_market_data("NVDA")) == 0
    assert len(market_data_repository.get_market_data("AMD")) == 0

    assert memory_info.get_info("NVDA") == {"current_minute": datetime(2026, 8, 2, 10, 0), "market_state": "TRADEABLE", "ticks": [(120.0, 120.5), (122.0, 122.8)]}
    assert memory_info.get_info("AMD") == {"current_minute": datetime(2026, 8, 2, 10, 0), "market_state": "TRADEABLE", "ticks": [(140.0, 140.4), (139.5, 140.0)]}

    # when --- Minute 2: 10:01 (Triggers rollover) ---
    listener._handle("EPIC:NVDA", {"BID": 121.5, "OFFER": 122.0, "MARKET_STATE": "TRADEABLE"}, t_min2_a)
    listener._handle("EPIC:AMD", {"BID": 141.0, "OFFER": 141.5, "MARKET_STATE": "TRADEABLE"}, t_min2_a)

    # then
    assert_frame_equal(
        market_data_repository.get_market_data("NVDA"),
        pd.DataFrame({
            "datetime": ["2026-08-02 10:00:00"],
            "epic": ["NVDA"],
            "bid_high": [122.0],
            "bid_low": [120.0],
            "bid_open": [120.0],
            "bid_close": [122.0],
            "offer_high": [122.8],
            "offer_low": [120.5],
            "offer_open": [120.5],
            "offer_close": [122.8],
            "close_spread": [0.8],
            "volume": [2.0],
        })
    )

    assert_frame_equal(
        market_data_repository.get_market_data("AMD"),
        pd.DataFrame({
            "datetime": ["2026-08-02 10:00:00"],
            "epic": ["AMD"],
            "bid_high": [140.0],
            "bid_low": [139.5],
            "bid_open": [140.0],
            "bid_close": [139.5],
            "offer_high": [140.4],
            "offer_low": [140.0],
            "offer_open": [140.4],
            "offer_close": [140.0],
            "close_spread":[0.5],
            "volume": [2.0],
        })
    )

    assert memory_info.get_info("NVDA") == {"current_minute": datetime(2026, 8, 2, 10, 1), "market_state": "TRADEABLE", "ticks": [(121.5, 122.0)]}
    assert memory_info.get_info("AMD") == {"current_minute": datetime(2026, 8, 2, 10, 1), "market_state": "TRADEABLE", "ticks": [(141.0, 141.5)]}
