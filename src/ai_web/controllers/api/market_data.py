import json

import pandas as pd

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trading_utils import trading_utils


def get_market_data(market_data_repository: MarketDataRepository, epic: str, from_param: str, to_param: str, freq: str):
    market_data = market_data_repository.get_market_data(epic, from_param, to_param)

    market_data = trading_utils.avg_bid_offer(market_data)
    market_data = trading_utils.fill_missing_candles(market_data, interval_minutes=1)
    if freq != "1min":
        market_data = trading_utils.aggregate_fo_ui(market_data, freq)

    market_data['time'] = pd.to_datetime(market_data['datetime']).astype('int64') // 10 ** 6

    chart_df = market_data[['time']].copy()
    chart_df['high'] = market_data['high']
    chart_df['low'] = market_data['low']
    chart_df['open'] = market_data['open']
    chart_df['close'] = market_data['close']

    chart_df = chart_df.sort_values('time').drop_duplicates(subset=['time'])

    records = chart_df.to_dict(orient="records")
    clean_records = [
        {k: v for k, v in row.items() if pd.notna(v)}
        for row in records
    ]

    return json.dumps(clean_records)
