import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from trading_ig import IGService
from trading_ig.config import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IGClient")

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
        try:
            self.ig_service.create_session()
            self.ig_service.switch_account(os.getenv("IG_SERVICE_ACC_NUMBER"), False)
            logger.info("Successfully authenticated.")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def fetch_prices_last_14_days(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, 'D', datetime.now() - timedelta(days=14), datetime.now())

    def fetch_prices_last_3_days(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, '1h', datetime.now() - timedelta(days=3), datetime.now())

    def fetch_prices_last_12_hours(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, '15MIN', datetime.now() - timedelta(hours=12), datetime.now())

    def fetch_prices_last_1_hour(self, epic: str):
        return self._fetch_historical_prices_by_epic_and_date_range(epic, '1MIN', datetime.now() - timedelta(hours=1), datetime.now())

    def search_markets(self):
        search_results = self.ig_service.search_markets("NVIDIA")
        print(f"search_results: {search_results}")

    def _fetch_historical_prices_by_epic_and_date_range(self, epic: str, resolution: str, start_date: datetime, end_date: datetime):
        try:
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            return self.ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to fetch market data for {epic}: {e}")
            return None

