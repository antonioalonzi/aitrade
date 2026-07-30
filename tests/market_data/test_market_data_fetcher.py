from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

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

def test_fetch_market_data(mocker, mock_ig_client, repository: MarketDataRepository):
    # given
    mock_datetime = mocker.patch("market_data.market_data_fetcher.datetime")
    mock_datetime.now.return_value = datetime.fromisoformat("2026-07-31 12:00:00")

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