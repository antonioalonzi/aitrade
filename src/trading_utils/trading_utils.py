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


def aggregate_for_ai(prices_df: pd.DataFrame) -> str:
    return _aggregate_for_ai(prices_df, datetime.now())


def atr(df: pd.DataFrame, period: int = 14) -> float:
    prev_close = df["close"].shift(1)
    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - prev_close).abs()
    low_prev_close = (df["low"] - prev_close).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(
        axis=1
    )

    atr_series = tr.ewm(alpha=1 / period, adjust=False).mean()

    return float(atr_series.iloc[-1])


def _aggregate_for_ai(prices_df: pd.DataFrame, latest_time: datetime) -> str:
    df = prices_df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").set_index("datetime")

    ohlc_dict = {"open": "first", "high": "max", "low": "min", "close": "last"}

    t_15m = latest_time - pd.Timedelta(minutes=15)
    t_1h = latest_time - pd.Timedelta(hours=1)
    t_12h = latest_time - pd.Timedelta(hours=12)
    t_24h = latest_time - pd.Timedelta(hours=24)
    t_14d = latest_time - pd.Timedelta(days=14)

    # 1. Slice time windows
    df_15m = df[df.index > t_15m]
    df_1h = df[(df.index > t_1h) & (df.index <= t_15m)]
    df_12h = df[(df.index > t_12h) & (df.index <= t_1h)]
    df_24h = df[(df.index > t_24h) & (df.index <= t_12h)]
    df_14d = df[(df.index >= t_14d) & (df.index <= t_24h)]

    # 2. Resample and tag resolution interval
    r_15m = df_15m[["open", "high", "low", "close"]].copy()
    r_15m["resolution"] = "1m"

    r_1h = df_1h.resample("5min").agg(ohlc_dict).dropna()
    r_1h["resolution"] = "5m"

    r_12h = df_12h.resample("15min").agg(ohlc_dict).dropna()
    r_12h["resolution"] = "15m"

    r_24h = df_24h.resample("1h").agg(ohlc_dict).dropna()
    r_24h["resolution"] = "1h"

    r_14d = df_14d.resample("1D").agg(ohlc_dict).dropna()
    r_14d["resolution"] = "1D"

    # 3. Concatenate and sort
    final_df = pd.concat([r_15m, r_1h, r_12h, r_24h, r_14d]).sort_index()

    # 4. Prepare columns: [timestamp (epoch int), resolution, open, high, low, close]
    final_df = final_df.reset_index()
    final_df["timestamp"] = final_df["datetime"].astype("int64") // 10 ** 9  # Unix epoch seconds
    price_cols = ["open", "high", "low", "close"]
    final_df[price_cols] = final_df[price_cols].round(2)

    # Select exact order of columns
    ordered_df = final_df[
        ["timestamp", "resolution", "open", "high", "low", "close"]
    ]

    # Convert to list of lists
    return ordered_df.values.tolist()
