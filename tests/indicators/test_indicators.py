import pytest
import pandas as pd
import pandas.testing as pdt

from indicators import indicators


def test_calculate_avg_bid_ask():
    # given
    highs_ask = [11, 12, 13, 14, 15]
    lows_ask = [9, 10, 11, 12, 13]
    close_ask = [10, 11, 12, 13, 14]
    highs_bid = [10, 11, 12, 13, 14]
    lows_bid = [8, 9, 10, 11, 12]
    close_bid = [9, 10, 11, 12, 13]
    df = _make_full_prices(highs_ask, lows_ask, highs_bid, lows_bid, close_ask, close_bid)

    # when
    result = indicators.avg_bid_ask(df)

    # then
    idx = pd.date_range('2020-01-01', periods=len(highs_ask), freq='D')
    data = {
        ('avg', 'High'): [10.5, 11.5, 12.5, 13.5, 14.5],
        ('avg', 'Low'): [8.5, 9.5, 10.5, 11.5, 12.5],
        ('avg', 'Close'): [9.5, 10.5, 11.5, 12.5, 13.5]
    }
    expected = pd.DataFrame(data, index=idx)
    pdt.assert_frame_equal(result, expected)

def test_calculate_atr_from_prices_constant_diff():
    # given
    highs = [11, 12, 13, 14, 15]
    lows = [9, 10, 11, 12, 13]
    df = _make_prices(highs, lows)

    # when
    res = indicators.atr(df, window=3)

    # then
    assert pytest.approx(res, rel=1e-12) == 2.0

def _make_prices(highs, lows, close = None):
    idx = pd.date_range('2020-01-01', periods=len(highs), freq='D')
    data = {
        ('ask', 'High'): highs,
        ('ask', 'Low'): lows,
        ('ask', 'Close'): close if close is not None else highs
    }
    return pd.DataFrame(data, index=idx)

def _make_full_prices(highs_ask, lows_ask, highs_bid, lows_bid, close_ask = None, close_bid = None):
    idx = pd.date_range('2020-01-01', periods=len(highs_ask), freq='D')
    data = {
        ('ask', 'High'): highs_ask,
        ('ask', 'Low'): lows_ask,
        ('ask', 'Close'): close_ask if close_ask is not None else highs_ask,
        ('bid', 'High'): highs_bid,
        ('bid', 'Low'): lows_bid,
        ('bid', 'Close'): close_bid if close_bid is not None else highs_bid
    }
    return pd.DataFrame(data, index=idx)