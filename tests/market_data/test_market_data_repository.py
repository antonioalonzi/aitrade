from pathlib import Path

import pandas as pd
import pytest

from market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def repository():
    repository = MarketDataRepository("aitrader-test.db")
    yield repository
    Path("aitrader-test.db").unlink(missing_ok=True)

def test_insert_and_get_market_data(repository):
    # given
    data_to_insert = {
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00", "2026-07-29 10:00:00"],
        "epic": ["NVIDIA", "NVIDIA", "AMAZON"],
        "bid_high": [501.0, 502.5, 101.5],
        "bid_low": [499.5, 500.8, 99.5],
        "bid_open": [500.0, 501.0, 100.5],
        "bid_close": [500.8, 502.0, 100.5],
        "ask_high": [501.2, 502.7, 102.5],
        "ask_low": [499.7, 501.0, 100.5],
        "ask_open": [500.2, 501.2, 101.5],
        "ask_close": [501.0, 502.2, 101.5]
    }
    df = pd.DataFrame(data_to_insert)

    # when
    repository.insert_market_data(df)

    # then
    retrieved_df = repository.get_market_data("NVIDIA")
    assert not retrieved_df.empty, "Market data was not saved"
    assert len(retrieved_df) == 2
    nvidia_data_df = pd.DataFrame({
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "epic": ["NVIDIA", "NVIDIA"],
        "bid_high": [501.0, 502.5],
        "bid_low": [499.5, 500.8],
        "bid_open": [500.0, 501.0],
        "bid_close": [500.8, 502.0],
        "ask_high": [501.2, 502.7],
        "ask_low": [499.7, 501.0],
        "ask_open": [500.2, 501.2],
        "ask_close": [501.0, 502.2]
    })
    pd.testing.assert_frame_equal(retrieved_df, nvidia_data_df)

    retrieved_df = repository.get_market_data("AMAZON")
    assert not retrieved_df.empty, "Market data was not saved"
    assert len(retrieved_df) == 1


def test_get_latest_datetime(repository):
    # given
    test_data = {
        "datetime": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
        "epic": ["NVIDIA", "NVIDIA"],
        "bid_high": [501.0, 502.5],
        "bid_low": [499.5, 500.8],
        "bid_open": [500.0, 501.0],
        "bid_close": [500.8, 502.0],
        "ask_high": [501.2, 502.7],
        "ask_low": [499.7, 501.0],
        "ask_open": [500.2, 501.2],
        "ask_close": [501.0, 502.2],
    }
    repository.insert_market_data(pd.DataFrame(test_data))

    # when
    datetime = repository.get_latest_datetime("NVIDIA")

    # then
    assert datetime == "2026-07-29 10:01:00"


def test_get_latest_datetime_no_data(repository):
    # when
    datetime = repository.get_latest_datetime("NVIDIA")

    # then
    assert datetime is None
