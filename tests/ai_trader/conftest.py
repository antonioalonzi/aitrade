from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.app import TradeRepository


@pytest.fixture
def trade_repository():
    repository = TradeRepository("ai_trader-test.db")
    yield repository
    Path("ai_trader-test.db").unlink(missing_ok=True)

@pytest.fixture
def real_market_data_repository():
    return MarketDataRepository("../data/ai_market_data.db")
