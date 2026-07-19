from typing import Any
import pandas as pd


def avg_bid_ask(prices_df: Any) -> Any:
    """
    Calculate average and bid prices using a rolling window.

    Args:
        prices_df: DataFrame-like object containing price series.

    Returns:
        DataFrame-like object with average prices.
    """
    if prices_df is None:
        return None

    mid_df = (prices_df['bid'] + prices_df['ask']) / 2
    mid_df.columns = pd.MultiIndex.from_product([['avg'], mid_df.columns])
    return mid_df


def atr(prices_df: Any, window: int = 7) -> float:
    """Calculate ATR-like metric from a prices DataFrame.

    Expects a DataFrame-like object with a nested column index where
    the highs and lows are reachable as `prices_df['avg']['High']` and
    `prices_df['avg']['Low']` (the same shape used in the original code).

    Args:
        prices_df: DataFrame-like object containing price series.
        window: rolling window size for smoothing.

    Returns:
        The last value of the rolling mean of (High - Low).
    """
    high_low = prices_df['avg']['High'] - prices_df['avg']['Low']
    clean_high_low = high_low.dropna()
    return clean_high_low.rolling(window=window, min_periods=1).mean().iloc[-1]
