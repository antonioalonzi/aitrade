from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from freezegun import freeze_time

from market_data.market_data_fetcher import MarketDataFetcher, HISTORY_DAYS
from market_data.market_data_repository import MarketDataRepository


@pytest.fixture
def mock_ig_client(mocker):
    return mocker.Mock()

@pytest.fixture
def repository():
    repository = MarketDataRepository("aitrader-test.db")
    yield repository
    Path("aitrader-test.db").unlink(missing_ok=True)

def test_fetch_market_data_when_no_data(mock_ig_client, repository: MarketDataRepository):
    with freeze_time("2026-07-31 12:00:00"):
        # given
        num_minutes = HISTORY_DAYS * 24 * 60

        prices_df = pd.DataFrame(
            index=pd.date_range(name="datetime", start="2026-07-01 12:00:00", periods=num_minutes, freq="1min"),
            columns=pd.MultiIndex.from_product([["bid", "ask"], ["high", "low", "open", "close"]]),
            data=[[1.0870, 1.0830, 1.0850, 1.0840, 1.0770, 1.0730, 1.0750, 1.0740]] * num_minutes # repeat the row num_minutes times
        )
        mock_ig_client.fetch_market_data.return_value = {
            "allowance": {"remaining": 10000},
            "prices": prices_df,
        }

        fetcher = MarketDataFetcher(ig_client=mock_ig_client, market_data_repository=repository)

        # when
        fetcher.fetch_market_data('NVIDIA')

        # then
        mock_ig_client.fetch_market_data.assert_called_once_with(
            "NVIDIA",
            datetime.fromisoformat("2026-07-01 12:00:00"),
            datetime.fromisoformat("2026-07-31 12:00:00")
        )

        saved_market_data = repository.get_market_data('NVIDIA')
        expected_df = pd.DataFrame({
            "datetime": pd.date_range(name="datetime", start="2026-07-01 12:00:00", periods=num_minutes, freq="1min").astype(str),
            "epic": ["NVIDIA"] * num_minutes,
            "bid_high": [1.0870] * num_minutes,
            "bid_low": [1.0830] * num_minutes,
            "bid_open": [1.0850] * num_minutes,
            "bid_close": [1.0840] * num_minutes,
            "ask_high": [1.0770] * num_minutes,
            "ask_low": [1.0730] * num_minutes,
            "ask_open": [1.0750] * num_minutes,
            "ask_close": [1.0740] * num_minutes
        })
        pd.testing.assert_frame_equal(saved_market_data, expected_df)


def test_fetch_market_data_when_already_some_data(mock_ig_client, repository: MarketDataRepository):
    with freeze_time("2026-07-31 12:00:00"):
        # given
        initial_data = {
            "datetime": ["2026-07-31 11:55:00"],
            "epic": ["NVIDIA"],
            "bid_high": [1.0870],
            "bid_low": [1.0830],
            "bid_open": [1.0850],
            "bid_close": [1.0840],
            "ask_high": [1.0770],
            "ask_low": [1.0730],
            "ask_open": [1.0750],
            "ask_close": [1.0740],
        }

        repository.insert_market_data(pd.DataFrame(initial_data))

        missing_rows_count = 5

        prices_df = pd.DataFrame(
            index=pd.date_range(name="datetime", start="2026-07-31 11:56:00", periods=missing_rows_count, freq="1min"),
            columns=pd.MultiIndex.from_product([["bid", "ask"], ["high", "low", "open", "close"]]),
            data=[[1.0870, 1.0830, 1.0850, 1.0840, 1.0770, 1.0730, 1.0750, 1.0740]] * missing_rows_count # repeat the row missing_rows_count times
        )
        mock_ig_client.fetch_market_data.return_value = {
            "allowance": {"remaining": 10000},
            "prices": prices_df,
        }

        fetcher = MarketDataFetcher(ig_client=mock_ig_client, market_data_repository=repository)

        # when
        fetcher.fetch_market_data('NVIDIA')

        # then
        mock_ig_client.fetch_market_data.assert_called_once_with(
            "NVIDIA",
            datetime.fromisoformat("2026-07-31 11:56:00"),
            datetime.fromisoformat("2026-07-31 12:00:00")
        )

        saved_market_data = repository.get_market_data('NVIDIA')
        expected_df = pd.DataFrame({
            "datetime": pd.date_range(name="datetime", start="2026-07-31 11:55:00", periods=missing_rows_count + 1, freq="1min").astype(str),
            "epic": ["NVIDIA"] * (missing_rows_count + 1),
            "bid_high": [1.0870] * (missing_rows_count + 1),
            "bid_low": [1.0830] * (missing_rows_count + 1),
            "bid_open": [1.0850] * (missing_rows_count + 1),
            "bid_close": [1.0840] * (missing_rows_count + 1),
            "ask_high": [1.0770] * (missing_rows_count + 1),
            "ask_low": [1.0730] * (missing_rows_count + 1),
            "ask_open": [1.0750] * (missing_rows_count + 1),
            "ask_close": [1.0740] * (missing_rows_count + 1)
        })
        pd.testing.assert_frame_equal(saved_market_data, expected_df)
