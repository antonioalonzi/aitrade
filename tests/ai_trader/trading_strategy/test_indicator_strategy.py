from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from ai_trader.trade.trade import Trade, TradeDirection
from ai_trader.trading_strategy import indicator_strategy
from ai_trader.trading_strategy.indicator_strategy import (
    IndicatorCloseStrategy,
    IndicatorOpenStrategy,
    IndicatorValues,
)


@pytest.fixture
def config():
    return {
        "ai_strategy_decision_mode": "TICKS_ONLY",
        "indicator_ema_fast": 10,
        "indicator_ema_slow": 30,
        "indicator_ema_trend": 90,
    }


def test_open_strategy_returns_buy_when_all_rules_pass(monkeypatch, config):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    monkeypatch.setattr(
        indicator_strategy,
        "_calculate_indicator_values",
        lambda *_: IndicatorValues(
            atr=1,
            adx=20.1,
            rsi=70,
            fast_ema=[101, 102],
            slow_ema=[100, 101],
            trend_ema=[99, 100],
        ),
    )

    recommendation = IndicatorOpenStrategy(repository, config).evaluate(datetime.now(), "EPIC")

    assert recommendation.direction == TradeDirection.BUY


def test_open_strategy_returns_sell_when_all_rules_pass(monkeypatch, config):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    monkeypatch.setattr(
        indicator_strategy,
        "_calculate_indicator_values",
        lambda *_: IndicatorValues(
            atr=1,
            adx=21,
            rsi=30,
            fast_ema=[103, 102],
            slow_ema=[104, 103],
            trend_ema=[105, 104],
        ),
    )

    recommendation = IndicatorOpenStrategy(repository, config).evaluate(datetime.now(), "EPIC")

    assert recommendation.direction == TradeDirection.SELL


def test_open_strategy_rejects_signal_when_adx_is_not_above_20(monkeypatch, config):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    monkeypatch.setattr(
        indicator_strategy,
        "_calculate_indicator_values",
        lambda *_: IndicatorValues(
            atr=1,
            adx=20,
            rsi=50,
            fast_ema=[101, 102],
            slow_ema=[100, 101],
            trend_ema=[99, 100],
        ),
    )

    recommendation = IndicatorOpenStrategy(repository, config).evaluate(datetime.now(), "EPIC")

    assert recommendation.direction == TradeDirection.NONE


@pytest.mark.parametrize(
    ("direction", "price", "should_close"),
    [
        ("BUY", 97.5, True),
        ("BUY", 102.5, False),
        ("BUY", 105, True),
        ("SELL", 102.5, True),
        ("SELL", 97.5, False),
        ("SELL", 95, True),
    ],
)
def test_close_strategy_applies_atr_stop_and_target(
    monkeypatch, config, direction, price, should_close
):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    monkeypatch.setattr(
        indicator_strategy,
        "_calculate_indicator_values",
        lambda *_: IndicatorValues(
            atr=1,
            adx=25,
            rsi=50,
            fast_ema=[102, 103],
            slow_ema=[101, 102],
            trend_ema=[100, 101],
        ),
    )
    monkeypatch.setattr(indicator_strategy, "get_last_price_for_trade", lambda *_: price)
    trade = Trade(
        id="trade",
        epic="EPIC",
        amount=1,
        direction=direction,
        size=1,
        opened_at=datetime.now(),
        open_price=100,
        open_comment="",
        balance_at_opening=1000,
    )

    decision = IndicatorCloseStrategy(repository, config).evaluate(
        datetime.now(), config, {"direction": direction}, trade
    )

    assert decision.should_close is should_close


@pytest.mark.parametrize(
    ("direction", "fast_ema", "adx", "should_close"),
    [
        ("BUY", [102, 101], 25, True),
        ("SELL", [100, 103], 25, True),
        ("BUY", [102, 103], 14.9, True),
        ("BUY", [102, 103], 15, False),
    ],
)
def test_close_strategy_closes_on_ema_cross_or_weak_adx(
    monkeypatch, config, direction, fast_ema, adx, should_close
):
    repository = MagicMock()
    repository.get_latest_market_data.return_value = pd.DataFrame([{"close": 100}])
    monkeypatch.setattr(
        indicator_strategy,
        "_calculate_indicator_values",
        lambda *_: IndicatorValues(
            atr=1,
            adx=adx,
            rsi=50,
            fast_ema=fast_ema,
            slow_ema=[101, 102],
            trend_ema=[100, 101],
        ),
    )
    monkeypatch.setattr(indicator_strategy, "get_last_price_for_trade", lambda *_: 100)
    trade = Trade(
        id="trade",
        epic="EPIC",
        amount=1,
        direction=direction,
        size=1,
        opened_at=datetime.now(),
        open_price=100,
        open_comment="",
        balance_at_opening=1000,
    )

    decision = IndicatorCloseStrategy(repository, config).evaluate(
        datetime.now(), config, {"direction": direction}, trade
    )

    assert decision.should_close is should_close
