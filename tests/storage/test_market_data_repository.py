import pytest

from pathlib import Path
import pandas as pd

from storage.market_data_repository import MarketDataRepository


@pytest.fixture(scope="module")
def repository():
    repository = MarketDataRepository("aitrader-test.db")
    yield repository
    Path("aitrader-test.db").unlink(missing_ok=True)

def test_insert_market_data(repository):
    # given
    test_data = {
        "timestamp": ["2026-07-29 10:00:00", "2026-07-29 10:01:00"],
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
    df = pd.DataFrame(test_data)

    # when
    repository.insert_market_data(df)

    # then
    retrieved_df = repository.get_market_data("NVIDIA")

    assert not retrieved_df.empty, "Market data was not saved"
    assert len(retrieved_df) == 2

    pd.testing.assert_frame_equal(retrieved_df, df)
