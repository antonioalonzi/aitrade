from datetime import datetime

import pandas as pd


def avg_bid_offer(prices_df: pd.DataFrame | None) -> pd.DataFrame | None:
    if prices_df is None or prices_df.empty:
        return prices_df

    return pd.DataFrame({
        "datetime": prices_df["datetime"],
        "high": (prices_df['bid_high'] + prices_df['offer_high']) / 2,
        "low": (prices_df['bid_low'] + prices_df['offer_low']) / 2,
        "open": (prices_df['bid_open'] + prices_df['offer_open']) / 2,
        "close": (prices_df['bid_close'] + prices_df['offer_close']) / 2,
    })


def aggregate_for_ai(prices_df: pd.DataFrame | None) -> str:
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


def _aggregate_for_ai(prices_df: pd.DataFrame | None, latest_time: datetime) -> str:
    if prices_df is None or prices_df.empty:
        return "No market data available."

    df = prices_df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").set_index("datetime")

    ohlc_dict = {
        "high": "max",
        "low": "min",
        "open": "first",
        "close": "last"
    }

    t_15m = latest_time - pd.Timedelta(minutes=15)
    t_1h = latest_time - pd.Timedelta(hours=1)
    t_12h = latest_time - pd.Timedelta(hours=12)
    t_24h = latest_time - pd.Timedelta(hours=24)
    t_14d = latest_time - pd.Timedelta(days=14)

    df_15m = df[df.index > t_15m]
    df_1h = df[(df.index > t_1h) & (df.index <= t_15m)]
    df_12h = df[(df.index > t_12h) & (df.index <= t_1h)]
    df_24h = df[(df.index > t_24h) & (df.index <= t_12h)]
    df_14d = df[(df.index >= t_14d) & (df.index <= t_24h)]

    resampled_blocks = [
        df_15m[["open", "high", "low", "close"]],
        df_1h.resample("5min").agg(ohlc_dict).dropna(),
        df_12h.resample("15min").agg(ohlc_dict).dropna(),
        df_24h.resample("1h").agg(ohlc_dict).dropna(),
        df_14d.resample("1D").agg(ohlc_dict).dropna()
    ]

    final_df = pd.concat(resampled_blocks).sort_index().reset_index()
    final_df["datetime"] = final_df["datetime"].dt.strftime("%Y-%m-%d %H:%M")

    return final_df.to_markdown(index=False)
