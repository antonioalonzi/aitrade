import pytest
import pandas as pd

from indicators import indicators


def test_calculate_atr_from_prices_constant_diff():
    # given
    highs = [11, 12, 13, 14, 15]
    lows = [9, 10, 11, 12, 13]
    df = _make_prices(highs, lows)

    # when
    res = indicators.atr(df, window=3)

    # then
    assert pytest.approx(res, rel=1e-12) == 2.0

def _make_prices(highs, lows):
    idx = pd.date_range('2020-01-01', periods=len(highs), freq='D')
    data = {
        ('ask', 'High'): highs,
        ('ask', 'Low'): lows,
    }
    return pd.DataFrame(data, index=idx)