from pathlib import Path

import pandas as pd
import pytest

from market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def repository():
    repository = MarketDataRepository("aitrader-test.db")
    yield repository
    Path("aitrader-test.db").unlink(missing_ok=True)

market_data_fixture = {
        "datetime": "2026-07-29 10:00:00",
        "bid_high": 501.0,
        "bid_low": 499.5,
        "bid_open": 500.0,
        "bid_close": 500.8,
        "ask_high": 501.2,
        "ask_low": 499.7,
        "ask_open": 500.2,
        "ask_close": 501.0,
        "close_spread": 1.0,
        "volume": 10.0
    }

def test_insert_and_get_market_data(repository):
    # when
    repository.insert_market_data("NVIDIA", market_data_fixture | {"datetime": "2026-07-29 10:00:00"})
    repository.insert_market_data("NVIDIA", market_data_fixture | {"datetime": "2026-07-29 10:01:00"})
    repository.insert_market_data("AMAZON", market_data_fixture | {"datetime": "2026-07-29 10:00:00"})

    retrieved_df = repository.get_market_data("NVIDIA")

    # then
    assert len(retrieved_df) == 2
    nvidia_data_df = pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "epic": ["NVIDIA"] * 2,
        "bid_high": [501.0] * 2,
        "bid_low": [499.5] * 2,
        "bid_open": [500.0] * 2,
        "bid_close": [500.8] * 2,
        "ask_high": [501.2] * 2,
        "ask_low": [499.7] * 2,
        "ask_open": [500.2] * 2,
        "ask_close": [501.0] * 2,
        "close_spread": [1.0] * 2,
        "volume": [10.0] * 2
    })
    pd.testing.assert_frame_equal(retrieved_df, nvidia_data_df)

    retrieved_df = repository.get_market_data("AMAZON")
    assert len(retrieved_df) == 1


def test_get_latest_datetime(repository):
    # given
    repository.insert_market_data("NVIDIA", market_data_fixture | {"datetime": "2026-07-29 10:00:00"})
    repository.insert_market_data("NVIDIA", market_data_fixture | {"datetime": "2026-07-29 10:01:00"})

    # when
    datetime = repository.get_latest_datetime("NVIDIA")

    # then
    assert datetime == "2026-07-29 10:01:00"


def test_get_latest_datetime_no_data(repository):
    # when
    datetime = repository.get_latest_datetime("NVIDIA")

    # then
    assert datetime is None
