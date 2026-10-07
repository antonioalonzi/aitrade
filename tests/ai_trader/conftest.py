from datetime import datetime
from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.app import TradeRepository
from ai_trader.trade.trade import Trade


@pytest.fixture
def trade_repository():
    repository = TradeRepository("ai_trader-test.db")
    yield repository
    Path("ai_trader-test.db").unlink(missing_ok=True)

@pytest.fixture
def real_market_data_repository():
    return MarketDataRepository("../data/ai_market_data.db")

@pytest.fixture
def trade_fixture() -> Trade:
    return Trade(
        id="trade-001",
        epic="NVIDIA",
        amount=100.0,
        direction="BUY",
        confidence=85,
        size=1,
        opened_at=datetime.fromisoformat("2023-01-01 10:00:00"),
        open_price=500.0,
        open_comment="Test trade",
        balance_at_opening=1000.0
    )