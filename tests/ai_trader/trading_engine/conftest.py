from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def real_market_data_repository():
    return MarketDataRepository("../data/ai_market_data.db")

@pytest.fixture
def back_testing_trade_repository():
    Path("../data/ai_trades_backtesting.db").unlink(missing_ok=True)
    return MarketDataRepository("../data/ai_trades_backtesting.db")
