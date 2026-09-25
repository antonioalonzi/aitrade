import pandas as pd


def atr(df: pd.DataFrame, period: int = 14) -> float:
    prev_close = df["close"].shift(1)
    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - prev_close).abs()
    low_prev_close = (df["low"] - prev_close).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(
        axis=1
    )

    atr_series = tr.ewm(alpha=1 / period, adjust=False).mean()

    return round(float(atr_series.iloc[-1]), 2)


def rsi(df: pd.DataFrame, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_array = 100 - (100 / (1 + rs))
    return round(rsi_array.iloc[-1].item(), 2)
