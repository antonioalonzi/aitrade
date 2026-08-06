import atexit
import logging
import os

from dotenv import load_dotenv
from trading_ig import IGService, IGStreamService
from trading_ig.stream import Subscription

from market_data.market_data_listener import MarketDataListener

logger = logging.getLogger(__name__)

class IGDataDownloaderClient:
    def __init__(self):
        load_dotenv()
        self.ig_service = IGService(
            os.getenv("LIVE_IG_SERVICE_USERNAME"),
            os.getenv("LIVE_IG_SERVICE_PASSWORD"),
            os.getenv("LIVE_IG_SERVICE_API_KEY"),
            os.getenv("LIVE_IG_SERVICE_ACC_TYPE"),
            os.getenv("LIVE_IG_SERVICE_ACC_NUMBER")
        )
        self.ig_stream_service = None

    def connect(self):
        self.ig_service.create_session()
        self.ig_stream_service = IGStreamService(self.ig_service)
        self.ig_stream_service.create_session()
        atexit.register(self.ig_service.logout)

    def subscribe_to_epics(self, epics: list, market_data_listener: MarketDataListener):
        logger.info(f"Subscribing to : {epics}")
        subscription = Subscription(
            mode="MERGE",
            items=[f"L1:{epic}" for epic in epics],
            fields=["BID", "OFFER", "MARKET_STATE"]
        )
        subscription.addListener(market_data_listener)
        self.ig_stream_service.subscribe(subscription)

    def search_markets(self, epic: str):
        search_results = self.ig_service.search_markets(epic)
        logger.info(f"search_results: {search_results}")
