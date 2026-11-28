from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from ai_trader.trade.trade import Trade, TradeDirection
from ai_trader.trading_strategy import moving_average_strategy
from ai_trader.trading_strategy.moving_average_strategy import (
    IndicatorValues,
    MovingAverageCloseStrategy,
    MovingAverageOpenStrategy,
)


@pytest.fixture
def config():
    return {
        "indicator_ema_fast": 10,
        "indicator_ema_slow": 30,
        "indicator_ema_trend": 90,
    }


def _mock_indicators(monkeypatch, indicators):
    monkeypatch.setattr(
        moving_average_strategy,
        "_calculate_indicator_values",
        lambda *_: indicators,
    )


@pytest.mark.parametrize(
    ("fast", "slow", "trend", "expected_direction"),
    [
        ([98, 100], [99, 99.5], [105, 105.5], TradeDirection.BUY),
        ([102, 100], [101, 100.5], [95, 94.5], TradeDirection.SELL),
        ([98, 100], [99, 99.5], [99.5, 99.5], TradeDirection.NONE),
    ],
)
def test_open_strategy_enters_on_fast_slow_cross_toward_trend(
    monkeypatch, config, fast, slow, trend, expected_direction
):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    _mock_indicators(
        monkeypatch,
        IndicatorValues(
            atr=None,
            adx=None,
            rsi=None,
            fast_ema=fast,
            slow_ema=slow,
            trend_ema=trend,
        ),
    )

    recommendation = MovingAverageOpenStrategy(repository, config).evaluate(
        datetime.now(), "EPIC"
    )

    assert recommendation.direction == expected_direction


@pytest.mark.parametrize(
    ("slow", "trend", "should_close"),
    [
        ([99, 101], [100, 100], True),
        ([101, 99], [100, 100], True),
        ([99, 99.5], [100, 100.5], False),
    ],
)
def test_close_strategy_exits_when_slow_crosses_trend(
    monkeypatch, config, slow, trend, should_close
):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    _mock_indicators(
        monkeypatch,
        IndicatorValues(
            atr=None,
            adx=None,
            rsi=None,
            fast_ema=[100, 101],
            slow_ema=slow,
            trend_ema=trend,
        ),
    )
    trade = Trade(
        id="trade",
        epic="EPIC",
        amount=1,
        direction=TradeDirection.BUY,
        size=1,
        opened_at=datetime.now(),
        open_price=100,
        open_comment="",
        balance_at_opening=1000,
    )

    decision = MovingAverageCloseStrategy(repository, config).evaluate(
        datetime.now(), config, {"direction": TradeDirection.BUY}, trade
    )

    assert decision.should_close is should_close
