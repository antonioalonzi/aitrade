from datetime import datetime

import pandas as pd


def avg_bid_offer(prices_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "datetime": prices_df["datetime"],
        "high": (prices_df['bid_high'] + prices_df['offer_high']) / 2,
        "low": (prices_df['bid_low'] + prices_df['offer_low']) / 2,
        "open": (prices_df['bid_open'] + prices_df['offer_open']) / 2,
        "close": (prices_df['bid_close'] + prices_df['offer_close']) / 2,
        "close_spread": prices_df['close_spread'],
        "volume": prices_df['volume']
    })



# 1 candle = 110 characters. It's about 35 tokens.
WINDOWS = [
    ['1h', '1min'], # 60 candles
    ['11h', '15min'], # 44 candles
    ['12h', '1h'], # 12 candles
    ['13D', '1D'] # 13 candles
]

OHLC_DICT = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}

def aggregate_for_ai(prices_df: pd.DataFrame, windows: list = WINDOWS) -> list:
    df = prices_df.copy()
    print(df["datetime"].head(10))
    print(df["datetime"].dtype)
    df["datetime"] = pd.to_datetime(df["datetime"], format="mixed")
    df = df.sort_values("datetime").set_index("datetime")

    if df.empty:
        return []

    # Automatically anchor to the newest candle in the dataset
    latest_time = df.index.max()

    dfs = []
    prev_time = latest_time

    for lookback_str, resolution_tag in windows:
        curr_time = latest_time - pd.Timedelta(lookback_str)
        slice_df = df[(df.index > curr_time) & (df.index <= prev_time)]

        if resolution_tag == '1min':
            r_df = slice_df[["open", "high", "low", "close", "volume"]].copy()
        else:
            r_df = slice_df.resample(resolution_tag).agg(OHLC_DICT).dropna()

        r_df["resolution"] = resolution_tag.replace('in', '')
        dfs.append(r_df)
        prev_time = curr_time

    final_df = pd.concat(dfs).sort_index()

    final_df = final_df.reset_index()
    final_df["timestamp"] = final_df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')
    price_cols = ["open", "high", "low", "close"]
    final_df[price_cols] = final_df[price_cols].round(2)

    ordered_df = final_df[["timestamp", "resolution", "open", "high", "low", "close", "volume"]]
    ordered_df = ordered_df.rename(columns={
        "timestamp": "t",
        "resolution": "tf",
        "open": "o",
        "high": "h",
        "low": "l",
        "close": "c",
        "volume": "v"
    })

    return ordered_df.to_dict(orient="records")


def aggregate_fo_ui(prices_df: pd.DataFrame, freq: str) -> pd.DataFrame:
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
