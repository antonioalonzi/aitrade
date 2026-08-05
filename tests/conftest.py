from pathlib import Path

import pytest

from market_data.market_data_handler import MarketDataHandler
from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_repository import MarketDataRepository
from trade.trade_repository import TradeRepository


@pytest.fixture
def trade_repository():
    repository = TradeRepository("aitrader-test.db")
    yield repository
    Path("aitrader-test.db").unlink(missing_ok=True)

@pytest.fixture
def market_data_repository():
    repository = MarketDataRepository("aitrader-test.db")
    yield repository
    Path("aitrader-test.db").unlink(missing_ok=True)

@pytest.fixture
def memory_info():
    return MarketDataInMemoryInfo()

@pytest.fixture
def handler(memory_info: MarketDataInMemoryInfo, market_data_repository: MarketDataRepository):
    return MarketDataHandler(memory_info, market_data_repository)

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
