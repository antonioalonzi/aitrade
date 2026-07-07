import atexit
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from trading_ig import IGService

logger = logging.getLogger(__name__)

class IGTradingClient:
    def __init__(self):
        load_dotenv()
        self.acc_number = os.getenv("IG_SERVICE_ACC_NUMBER")
        self.ig_service = IGService(
            os.getenv("IG_SERVICE_USERNAME"),
            os.getenv("IG_SERVICE_PASSWORD"),
            os.getenv("IG_SERVICE_API_KEY"),
            os.getenv("IG_SERVICE_ACC_TYPE"),
            os.getenv("IG_SERVICE_ACC_NUMBER")
        )

    def connect(self):
        self.ig_service.create_session()
        self.ig_service.switch_account(self.acc_number, False)
        logger.info("Successfully authenticated.")
        atexit.register(self.ig_service.logout)

    def fetch_account_balance(self):
        accounts = self.ig_service.fetch_accounts()
        available_balance = accounts.loc[accounts['accountId'] == self.acc_number, 'available'].values[0]
        return available_balance

    def is_market_open(self, epic: str):
        return self.ig_service.fetch_market_by_epic(epic).snapshot.marketStatus == "TRADEABLE"

    def fetch_prices_last_14_days(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, 'D', datetime.now() - timedelta(days=14), datetime.now())

    def fetch_prices_last_3_days(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, '1h', datetime.now() - timedelta(days=3), datetime.now())

    def fetch_prices_last_12_hours(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, '15MIN', datetime.now() - timedelta(hours=12), datetime.now())

    def fetch_prices_last_1_hour(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, '1MIN', datetime.now() - timedelta(hours=1), datetime.now())

    def get_first_open_position(self):
        positions = self.ig_service.fetch_open_positions()
        if not positions.empty:
            return positions.iloc[0].to_dict()
        return None

    def open_position(self, epic: str, direction: str, stop_distance: float, limit_distance: float):
        return self.ig_service.create_open_position(
            currency_code="GBP",
            direction=direction,
            epic=epic,
            expiry="-",
            order_type="MARKET",
            size=1.0,
            force_open=True,
            guaranteed_stop=False,
            stop_distance=stop_distance,
            trailing_stop=True,
            trailing_stop_increment=10.0,
            limit_distance=limit_distance
        )

    def search_markets(self, epic: str):
        search_results = self.ig_service.search_markets(epic)
        logger.info(f"search_results: {search_results}")

    def _fetch_historical_prices_by_epic_and_date_range(self, epic: str, resolution: str, start_date: datetime, end_date: datetime):
        try:
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            return self.ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to fetch market data for {epic}: {e}")
            return None
