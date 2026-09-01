import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler

from ai_data_downloader.market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from ai_data_downloader.market_data.market_data_listener import MarketDataListener
from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_data_downloader.trading_platform.ig_data_downloader_client import IGDataDownloaderClient

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





logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        TimedRotatingFileHandler(
            filename="../../logs/ai_data_downloader.log",
            when="D",
            interval=14,
            backupCount=12,
            encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

# Stocks - don't work, only indexes work
# AMAZON = "SE.D.AMZN.DAILY.IP"
# AMD = "SE.D.AMD.DAILY.IP"
# APPLE = "SE.D.AAPL.DAILY.IP"
# META = "SE.D.FB.DAILY.IP"
# MICROSOFT = "SE.D.MSFT.DAILY.IP"
# NVIDIA = "UC.D.NVDA.DAILY.IP"
# PALANTIR = "SE.D.PLTRUS.DAILY.IP"
# SMCI = "SE.D.SMCIUS.DAILY.IP"
# TESLA = "SE.D.TSLA.DAILY.IP"

# Indexes
DAX40 = "IX.D.DAX.DAILY.IP"
DOW = "IX.D.DOW.DAILY.IP"
FTSE100 = "IX.D.FTSE.DAILY.IP"
NASDAQ = "IX.D.NASDAQ.CASH.IP"
SEMICONDUCTOR = "UD.D.SOXXUS.DAILY.IP"
US500 = "IX.D.SPTRD.DAILY.IP"


ig_data_downloader_client_bean = IGDataDownloaderClient()
market_data_repository_bean = MarketDataRepository("../../data/ai_market_data.db")
market_data_in_memory_info_bean = MarketDataInMemoryInfo()
market_data_listener_bean = MarketDataListener(market_data_in_memory_info_bean, market_data_repository_bean)

ai_data_downloader = AiDataDownloader(ig_data_downloader_client_bean, market_data_repository_bean, market_data_in_memory_info_bean, market_data_listener_bean, [DAX40, DOW, FTSE100, NASDAQ, SEMICONDUCTOR, US500])
ai_data_downloader.subscribe_to_market_data()

while True:
    time.sleep(5)