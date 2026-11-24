import json

import pandas as pd

from ai_web.controllers.market_data import market_data_controller


def test_get_market_data_returns_seconds_for_chart_timestamps(monkeypatch):
    market_data = pd.DataFrame({
        "time": [1],
        "high": [12.0],
        "low": [8.0],
        "open": [9.0],
        "close": [11.0],
    })
    monkeypatch.setattr(market_data_controller, "_get_market_data", lambda *args: market_data)

    result = json.loads(market_data_controller.get_market_data(None, "epic", "from", "to", "1min"))

    assert result == [{"time": 1, "high": 12.0, "low": 8.0, "open": 9.0, "close": 11.0}]


def test_get_indicators_returns_timestamped_finite_series(monkeypatch):
    market_data = pd.DataFrame({
        "time": [2, 1, 3],
        "close": [20.0, 10.0, 30.0],
    })
    monkeypatch.setattr(market_data_controller, "_get_market_data", lambda *args: market_data)
    monkeypatch.setattr(
        market_data_controller.trading_indicators,
        "atr",
        lambda *_: [2.0, float("nan"), 4.0],
    )
    monkeypatch.setattr(
        market_data_controller.trading_indicators,
        "adx",
        lambda *_: [20.0, 10.0, 30.0],
    )
    monkeypatch.setattr(
        market_data_controller.trading_indicators,
        "rsi",
        lambda *_: [30.0, 40.0, 50.0],
    )
    monkeypatch.setattr(
        market_data_controller.trading_indicators,
        "window_exponential_average",
        lambda _, span: [float(span)] * 3,
    )

    result = json.loads(market_data_controller.get_indicators(None, "epic", "from", "to", "1min"))

    assert result["atr"] == [
        {"time": 2, "value": 2.0},
        {"time": 3, "value": 4.0},
    ]
    assert result["adx"] == [
        {"time": 1, "value": 10.0},
        {"time": 2, "value": 20.0},
        {"time": 3, "value": 30.0},
    ]
    assert result["emas"]["ema_fast_10"] == [
        {"time": 1, "value": 10.0},
        {"time": 2, "value": 10.0},
        {"time": 3, "value": 10.0},
    ]


def test_get_indicators_handles_indicator_without_values(monkeypatch):
    market_data = pd.DataFrame({"time": [1_000]})
    monkeypatch.setattr(market_data_controller, "_get_market_data", lambda *args: market_data)
    monkeypatch.setattr(market_data_controller.trading_indicators, "adx", lambda *_: [])
    monkeypatch.setattr(market_data_controller.trading_indicators, "atr", lambda *_: [1.0])
    monkeypatch.setattr(market_data_controller.trading_indicators, "rsi", lambda *_: [50.0])
    monkeypatch.setattr(
        market_data_controller.trading_indicators,
        "window_exponential_average",
        lambda *_: [1.0],
    )

    result = json.loads(market_data_controller.get_indicators(None, "epic", "from", "to", "1min"))

    assert result["adx"] == []
