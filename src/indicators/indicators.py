from typing import Any

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

