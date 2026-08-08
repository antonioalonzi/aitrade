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
        items = [f"MARKET:{epic}" for epic in epics]
        logger.info(f"Subscribing to: {items}")

        # https://lightstreamer.com/sdks/ls-python-client/2.1.0/api/lightstreamer.html#lightstreamer.client.ls_python_client_wrapper.Subscription
        subscription = Subscription(
            mode="MERGE",
            items=items,
            fields=["BID", "OFFER", "MARKET_STATE"]
        )
        subscription.addListener(market_data_listener)

        self.ig_stream_service.subscribe(subscription)

    def search_markets(self, epic: str):
        df = self.ig_service.search_markets(epic)

        logger.info(f"Search {epic}")
        for idx, row in df.iterrows():
            logger.info(f"Row {idx}: {row.to_dict()}")
