import atexit
import logging
import os

from dotenv import load_dotenv
from trading_ig import IGService, IGStreamService
from trading_ig.stream import Subscription

from market_data.market_data_listener import MarketDataListener

logger = logging.getLogger(__name__)

IG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

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
        self.ig_stream_service = None

    def is_connected(self):
        try:
            self.fetch_account_balance()
            logger.info("IG client is connected.")
            return True

        except Exception as e:
            logger.info(f"Not Connected: {e}. Connecting...")
            return False

    def connect(self):
        self.ig_service.create_session()
        self.ig_service.switch_account(self.acc_number, False)
        self.ig_stream_service = IGStreamService(self.ig_service)
        self.ig_stream_service.create_session()
        atexit.register(self.ig_service.logout)

    def fetch_account_balance(self):
        accounts = self.ig_service.fetch_accounts()
        available_balance = accounts.loc[accounts['accountId'] == self.acc_number, 'available'].values[0]
        return available_balance

    def subscribe_to_epics(self, epics: list, market_data_listener: MarketDataListener):
        logger.info(f"Subscribing to : {epics}")
        subscription = Subscription(
            mode="MERGE",
            items=[f"L1:{epic}" for epic in epics],
            fields=["BID", "OFFER", "MARKET_STATE"]
        )
        subscription.addListener(market_data_listener)
        self.ig_stream_service.subscribe(subscription)

    def get_first_open_position(self):
        positions = self.ig_service.fetch_open_positions()
        if not positions.empty:
            return positions.iloc[0].to_dict()
        return None

    def open_position(self, epic: str, direction: str, stop_distance: float, limit_distance: float):
        result = self.ig_service.create_open_position(
            currency_code="GBP",
            direction=direction,
            epic=epic,
            expiry="-",
            order_type="MARKET",
            size=1.0,
            force_open=True,
            guaranteed_stop=False,
            stop_distance=str(round(stop_distance, 1)),
            trailing_stop=True,
            trailing_stop_increment=10.0,
            limit_distance=str(round(limit_distance, 1))
        )
        logger.info(result)

        deal_ref = result.get("dealReference")

        if deal_ref:
            confirmation = self.ig_service.fetch_deal_by_deal_reference(deal_ref)
            logger.info(confirmation)
            if confirmation.get('dealStatus') == 'ACCEPTED':
                logger.info(f"Actual Open Price: {confirmation.get('level')}")
                logger.info(f"Assigned Deal ID: {confirmation.get('dealId')}")
                return confirmation

        return None


    def search_markets(self, epic: str):
        search_results = self.ig_service.search_markets(epic)
        logger.info(f"search_results: {search_results}")
