import os
import logging
from dotenv import load_dotenv
from trading_ig import IGService
from trading_ig.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IGClient")

class IGTradingClient:
    def __init__(self):
        load_dotenv()

        self.acc_number = os.getenv("IG_SERVICE_ACC_NUMBER")

        self.service = IGService(
            os.getenv("IG_SERVICE_USERNAME"),
            os.getenv("IG_SERVICE_PASSWORD"),
            os.getenv("IG_SERVICE_API_KEY"),
            os.getenv("IG_SERVICE_ACC_TYPE"),
            os.getenv("IG_SERVICE_ACC_NUMBER")
        )

    def connect(self):
        try:
            self.service.create_session()
            self.service.switch_account(os.getenv("IG_SERVICE_ACC_NUMBER"), False)
            logger.info("Successfully authenticated.")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_market_info(self, epic: str):
        try:
            return self.service.fetch_market_by_epic(epic)
        except Exception as e:
            logger.error(f"Failed to fetch market data for {epic}: {e}")
            return None
