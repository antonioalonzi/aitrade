from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_listener import MarketDataListener
from ai_data_downloader.market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from ai_data_downloader.market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def market_data_repository():
    repository = MarketDataRepository("ai_market_data-test.db")
    yield repository
    Path("ai_market_data-test.db").unlink(missing_ok=True)

@pytest.fixture
def memory_info():
    return MarketDataInMemoryInfo()

@pytest.fixture
def listener(memory_info: MarketDataInMemoryInfo, market_data_repository: MarketDataRepository):
    return MarketDataListener(memory_info, market_data_repository)
