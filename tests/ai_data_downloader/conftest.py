from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_listener import MarketDataListener
from ai_data_downloader.market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from ai_data_downloader.market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def market_data_repository():
    repository = MarketDataRepository("ai_trader-test.db")
    yield repository
    Path("ai_trader-test.db").unlink(missing_ok=True)

@pytest.fixture
def memory_info():
    return MarketDataInMemoryInfo()

@pytest.fixture
def listener(memory_info: MarketDataInMemoryInfo, market_data_repository: MarketDataRepository):
    return MarketDataListener(memory_info, market_data_repository)

market_data_fixture = {
        "datetime": "2026-07-29 10:00:00",
        "bid_high": 501.0,
        "bid_low": 499.5,
        "bid_open": 500.0,
        "bid_close": 500.8,
        "offer_high": 501.2,
        "offer_low": 499.7,
        "offer_open": 500.2,
        "offer_close": 501.0,
        "close_spread": 1.0,
        "volume": 10.0
    }
