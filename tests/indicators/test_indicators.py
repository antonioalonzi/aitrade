import pytest
import pandas as pd

from indicators import indicators


def test_calculate_atr_from_prices_constant_diff():
    highs = [11, 12, 13, 14, 15]
    lows = [9, 10, 11, 12, 13]  # high-low == 2 for every row
    df = _make_prices(highs, lows)

    # Using a small window still returns 2.0 as the rolling mean of constant 2s
    res = indicators.atr(df, window=3)
    assert pytest.approx(res, rel=1e-12) == 2.0

def _make_prices(highs, lows, closes=None):
    idx = pd.date_range('2020-01-01', periods=len(highs), freq='D')
    data = {
        ('ask', 'High'): highs,
        ('ask', 'Low'): lows,
        ('ask', 'Close'): closes if closes is not None else highs
    }
    df = pd.DataFrame(data, index=idx)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    return df