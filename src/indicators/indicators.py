from typing import Any


def atr(prices_df: Any, window: int = 7) -> float:
    """Calculate ATR-like metric from a prices DataFrame.

    Expects a DataFrame-like object with a nested column index where
    the highs and lows are reachable as `prices_df['ask']['High']` and
    `prices_df['ask']['Low']` (the same shape used in the original code).

    Args:
        prices_df: DataFrame-like object containing price series.
        window: rolling window size for smoothing.

    Returns:
        The last value of the rolling mean of (High - Low).
    """
    high_low = prices_df['ask']['High'] - prices_df['ask']['Low']
    clean_high_low = high_low.dropna()
    return clean_high_low.rolling(window=window, min_periods=1).mean().iloc[-1]
