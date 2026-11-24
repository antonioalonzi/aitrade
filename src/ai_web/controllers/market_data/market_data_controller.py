import json

import pandas as pd
from pandas import DataFrame

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trading_utils import trading_utils, trading_indicators
from ai_web.controllers.market_data import market_data_ui_aggregator
from ai_web.controllers.web_utils.time_utils import to_localised_time_panda


def get_market_data(market_data_repository: MarketDataRepository, epic: str, from_param: str, to_param: str, freq: str):
    market_data = _get_market_data(epic, freq, from_param, market_data_repository, to_param)

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


def get_indicators(market_data_repository: MarketDataRepository, epic: str, from_param: str, to_param: str, freq: str):
    market_data = _get_market_data(epic, freq, from_param, market_data_repository, to_param)

    indicators = {
        "atr": trading_indicators.atr(market_data, 14),
        "adx": trading_indicators.adx(market_data, 14),
        "rsi": trading_indicators.rsi(market_data, 14),
        "emas": {
            "ema_fast_10": trading_indicators.window_exponential_average(market_data, 10),
            "ema_slow_30": trading_indicators.window_exponential_average(market_data, 30),
            "ema_trend_90": trading_indicators.window_exponential_average(market_data, 90)
        }
    }
    return json.dumps(indicators)


def _get_market_data(epic: str, freq: str, from_param: str, market_data_repository: MarketDataRepository,
                     to_param: str) -> DataFrame:
    market_data = market_data_repository.get_market_data(epic, from_param, to_param)

    market_data = trading_utils.avg_bid_offer(market_data)
    market_data = market_data_ui_aggregator.fill_missing_candles(market_data, interval_minutes=1)
    if freq != "1min":
        market_data = market_data_ui_aggregator.aggregate_for_ui(market_data, freq)

    market_data['time'] = to_localised_time_panda(pd.to_datetime(market_data['datetime'], utc=True)).astype(
        'int64') // 10 ** 6
    return market_data
