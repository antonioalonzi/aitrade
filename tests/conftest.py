from datetime import datetime
from pathlib import Path

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade
from ai_trader.trade.trade_repository import TradeRepository
from ai_web.controllers.trade_summary.trade_summary_repository import TradeSummaryRepository


@pytest.fixture
def market_data_repository():
    repository = MarketDataRepository("ai_market_data-test.db")
    yield repository
    Path("ai_market_data-test.db").unlink(missing_ok=True)


@pytest.fixture
def trade_repository():
    repository = TradeRepository("ai_trader-test.db")
    yield repository
    Path("ai_trader-test.db").unlink(missing_ok=True)


@pytest.fixture
def trade_summary_repository():
    repository = TradeSummaryRepository("ai_trader-test.db")
    yield repository
    Path("ai_trader-test.db").unlink(missing_ok=True)


@pytest.fixture
def market_data_fixture():
    return {
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
        "volume": 10.0,
        "market_state": "TRADABLE"
    }

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