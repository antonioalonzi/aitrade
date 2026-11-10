import numpy as np
import pandas as pd


def atr(df: pd.DataFrame, period: int = 14, tail: int = 0) -> list[float]:
    prev_close = df["close"].shift(1)
    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - prev_close).abs()
    low_prev_close = (df["low"] - prev_close).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(
        axis=1
    )

    atr_series = tr.ewm(alpha=1 / period, adjust=False).mean()
    series = atr_series if tail <= 0 else atr_series.tail(tail)
    return series.round(2).tolist()


def rsi(df: pd.DataFrame, period: int = 14, tail: int = 0) -> list[float]:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_array = 100 - (100 / (1 + rs))

    series = rsi_array if tail <= 0 else rsi_array.tail(tail)
    return series.round(2).tolist()


def adx(df: pd.DataFrame, period: int = 14, tail: int = 0) -> list[float]:
    if df.empty or len(df) < 2:
        return [] if tail <= 0 else [0.0] * tail

    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    up_move = high.diff()
    down_move = low.diff().mul(-1)
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=df.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=df.index,
    )

    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    atr_series = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = (
        100
        * plus_dm.ewm(alpha=1 / period, adjust=False).mean()
        / atr_series.replace(0, np.nan)
    )
    minus_di = (
        100
        * minus_dm.ewm(alpha=1 / period, adjust=False).mean()
        / atr_series.replace(0, np.nan)
    )
    dx = (
        100
        * (plus_di - minus_di).abs()
        / (plus_di + minus_di).replace(0, np.nan)
    )
    adx_series = dx.ewm(alpha=1 / period, adjust=False).mean()

    series = adx_series if tail <= 0 else adx_series.tail(tail)
    return series.round(2).tolist()


def window_exponential_average(df: pd.DataFrame, span: int, tail: int = 0) -> list[float]:
    ema = df["close"].ewm(span=span, adjust=False).mean()
    series = ema if tail <= 0 else ema.tail(tail)
    return series.round(2).tolist()