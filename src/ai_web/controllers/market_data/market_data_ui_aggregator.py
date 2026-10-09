import pandas as pd


def aggregate_for_ui(prices_df: pd.DataFrame, freq: str) -> pd.DataFrame:
    if prices_df.empty:
        return prices_df

    prices_df = prices_df.copy()
    if not isinstance(prices_df.index, pd.DatetimeIndex):
        prices_df["datetime"] = pd.to_datetime(prices_df["datetime"])
        prices_df = prices_df.set_index("datetime")

    resampled = prices_df.resample(freq).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    }).dropna(how="all")

    return resampled.reset_index()


def fill_missing_candles(candles: pd.DataFrame, interval_minutes=1) -> pd.DataFrame:
    candles = candles.copy()

    if not isinstance(candles.index, pd.DatetimeIndex):
        candles["datetime"] = pd.to_datetime(candles["datetime"])
        candles = candles.set_index("datetime")

    freq = f"{interval_minutes}min"
    filled_df = candles.resample(freq).asfreq().reset_index()

    filled_df["datetime"] = filled_df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return filled_df
