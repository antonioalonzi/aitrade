import logging

from clients.ig_data_downloader_client import IGDataDownloaderClient
from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_listener import MarketDataListener
from market_data.market_data_repository import MarketDataRepository

logger = logging.getLogger(__name__)

class AiDataDownloader:
    def __init__(
            self,
            ig_data_downloader_client: IGDataDownloaderClient,
            market_data_repository: MarketDataRepository,
            market_data_in_memory_info: MarketDataInMemoryInfo,
            market_data_listener: MarketDataListener,
            epics: list[str]
    ):
        self.ig_data_downloader_client = ig_data_downloader_client
        self.market_data_repository = market_data_repository
        self.market_data_in_memory_info = market_data_in_memory_info
        self.market_data_listener = market_data_listener
        self.epics = epics

    def subscribe_to_market_data(self) -> None:
        self.connect()
        # self.ig_data_downloader_client.search_markets("S&P 500")
        self.ig_data_downloader_client.subscribe_to_epics(self.epics, self.market_data_listener)

    def connect(self):
        try:
            self.ig_data_downloader_client.connect()
            logger.info("IG data downloader client connected successfully.")

        except Exception as e:
            logger.error(f"Could not connect to IG data downloader: {str(e)}")
            return False


def run_data_downloader(
        ig_data_downloader_client: IGDataDownloaderClient,
        market_data_repository: MarketDataRepository,
        market_data_in_memory_info: MarketDataInMemoryInfo,
        market_data_listener: MarketDataListener,
        epics: list[str]
):
    ai_data_downloader = AiDataDownloader(ig_data_downloader_client, market_data_repository, market_data_in_memory_info, market_data_listener, epics)
    ai_data_downloader.subscribe_to_market_data()
