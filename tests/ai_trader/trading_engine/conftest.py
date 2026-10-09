import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def real_market_data_repository():
    return MarketDataRepository("../data/ai_market_data.db")
