import logging

from datetime import datetime, timedelta

from clients.ig_client import IGTradingClient
from market_data.market_data_repository import MarketDataRepository

HISTORY_DAYS=30

SCHEMA_COLUMNS = [
    "datetime",
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
]

logger = logging.getLogger(__name__)

class MarketDataFetcher:
    def __init__(self, ig_client: IGTradingClient, market_data_repository: MarketDataRepository):
        self.ig_client = ig_client
        self.market_data_repository = market_data_repository

    def fetch_market_data(self, epic: str):
        from_date = datetime.now() - timedelta(days=HISTORY_DAYS)
        to_date = datetime.now() - timedelta(days=HISTORY_DAYS-1, hours=23)
        market_data = self.ig_client.fetch_market_data(epic, from_date, to_date)
        logger.info(f"Allowance: {market_data["allowance"]}")
        prices_df = market_data["prices"]

        prices_df = prices_df.reset_index()

        # flatten multi-index data: {bid: {open, close}, ask: {open, close}}
        prices_df.columns = [
            f"{a}_{b}".lower().strip("_") for a, b in prices_df.columns.to_flat_index()
        ]

        prices_df = prices_df[SCHEMA_COLUMNS]
        prices_df["epic"] = epic

        self.market_data_repository.insert_market_data(prices_df)
