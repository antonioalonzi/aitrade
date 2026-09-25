from datetime import datetime

import pandas as pd


def avg_bid_offer(prices_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "datetime": prices_df["datetime"],
        "high": (prices_df['bid_high'] + prices_df['offer_high']) / 2,
        "low": (prices_df['bid_low'] + prices_df['offer_low']) / 2,
        "open": (prices_df['bid_open'] + prices_df['offer_open']) / 2,
        "close": (prices_df['bid_close'] + prices_df['offer_close']) / 2,
    })


def aggregate_for_ai(prices_df: pd.DataFrame) -> list:
    return _aggregate_for_ai(prices_df, datetime.now())


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


FREQ_MAP = {
        '1m': None,  # Raw data
        '5m': '5min',
        '15m': '15min',
        '1h': '1h',
        '1D': '1D'
    }

WINDOWS = [
        ['1h', '1m'],
        ['23h', '15m'],
        ['4D', '1h'],
        ['25D', '1D']
    ]

OHLC_DICT = {"open": "first", "high": "max", "low": "min", "close": "last"}

def _aggregate_for_ai(prices_df: pd.DataFrame, latest_time: datetime, windows: list = WINDOWS) -> list:
    df = prices_df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").set_index("datetime")

    dfs = []
    prev_time = latest_time

    for lookback_str, res_tag in windows:
        curr_time = latest_time - pd.Timedelta(lookback_str)
        slice_df = df[(df.index > curr_time) & (df.index <= prev_time)]

        freq = FREQ_MAP[res_tag]
        if freq is None:
            r_df = slice_df[["open", "high", "low", "close"]].copy()
        else:
            r_df = slice_df.resample(freq).agg(OHLC_DICT).dropna()

        r_df["resolution"] = res_tag
        dfs.append(r_df)
        prev_time = curr_time

    final_df = pd.concat(dfs).sort_index()

    # Finalize format: [timestamp (epoch int), resolution, open, high, low, close]
    final_df = final_df.reset_index()
    final_df["timestamp"] = final_df["datetime"].astype("int64") // 10 ** 6
    price_cols = ["open", "high", "low", "close"]
    final_df[price_cols] = final_df[price_cols].round(2)

    ordered_df = final_df[["timestamp", "resolution", "open", "high", "low", "close"]]
    return ordered_df.values.tolist()
