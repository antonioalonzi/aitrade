import pandas as pd

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository


def get_market_data(market_data_repository: MarketDataRepository):
    df = market_data_repository.get_latest_market_data("IX.D.SPTRD.DAILY.IP")

    df['time'] = pd.to_datetime(df['datetime']).astype('int64') // 10 ** 6

    chart_df = df[['time']].copy()
    chart_df['open'] = df['bid_open']
    chart_df['high'] = df['bid_high']
    chart_df['low'] = df['bid_low']
    chart_df['close'] = df['bid_close']

    chart_df = chart_df.sort_values('time').drop_duplicates(subset=['time'])

    return chart_df.to_json(orient='records')

