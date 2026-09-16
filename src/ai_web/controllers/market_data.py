import json
from datetime import datetime, timedelta

import pandas as pd

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trading_utils import trading_utils


def get_market_data(market_data_repository: MarketDataRepository, epic: str, from_param: str, to_param: str):
    from_param = from_param if from_param else (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    to_param = to_param if to_param else "2100-01-01T00:00:00Z"

    market_data = market_data_repository.get_market_data(epic, from_param, to_param)
    avg_market_data_gap = trading_utils.avg_bid_offer(market_data)
    avg_market_data_gap_filled = trading_utils.fill_missing_candles(avg_market_data_gap, interval_minutes=1)

    avg_market_data_gap_filled['time'] = pd.to_datetime(avg_market_data_gap_filled['datetime']).astype('int64') // 10 ** 6

    chart_df = avg_market_data_gap_filled[['time']].copy()
    chart_df['high'] = avg_market_data_gap_filled['high']
    chart_df['low'] = avg_market_data_gap_filled['low']
    chart_df['open'] = avg_market_data_gap_filled['open']
    chart_df['close'] = avg_market_data_gap_filled['close']

    chart_df = chart_df.sort_values('time').drop_duplicates(subset=['time'])

    records = chart_df.to_dict(orient="records")
    clean_records = [
        {k: v for k, v in row.items() if pd.notna(v)}
        for row in records
    ]

    return json.dumps(clean_records)
