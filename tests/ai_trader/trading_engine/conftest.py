from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@pytest.fixture
def real_market_data_repository():
    return MarketDataRepository(str(DATA_DIR / "ai_market_data.db"))

@pytest.fixture
def back_testing_trade_repository():
    db_path = DATA_DIR / "ai_trades.db"
    db_path.unlink(missing_ok=True)
    return TradeRepository(str(db_path))
