from pathlib import Path

import pytest

from ai_trader.app import TradeRepository


@pytest.fixture
def trade_repository():
    repository = TradeRepository("ai_trader-test.db")
    yield repository
    Path("ai_trader-test.db").unlink(missing_ok=True)
