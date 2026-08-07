import logging

from clients.ig_data_downloader_client import IGDataDownloaderClient
from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_listener import MarketDataListener
from market_data.market_data_repository import MarketDataRepository

logger = logging.getLogger(__name__)

class AiDataDownloader:
    def __init__(self, epics: list[str]):
        self.ig_client = IGDataDownloaderClient()
        self.market_data_repository = MarketDataRepository("ai_trader.db")
        self.market_data_in_memory_info = MarketDataInMemoryInfo()
        self.market_data_listener = MarketDataListener(self.market_data_in_memory_info, self.market_data_repository)
        self.epics = epics

    def subscribe_to_market_data(self) -> None:
        self.connect()
        self.ig_client.subscribe_to_epics(self.epics, self.market_data_listener)

    def connect(self):
        try:
            self.ig_client.connect()
            logger.info("IG client connected successfully.")

        except Exception as e:
            logger.error(f"Could not connect to IG: {str(e)}")
            return False


def run_data_downloader(epics: list[str]) -> None:
    ai_data_downloader = AiDataDownloader(epics)
    ai_data_downloader.subscribe_to_market_data()
