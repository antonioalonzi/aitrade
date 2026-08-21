import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from ai_data_downloader import run_data_downloader
from ai_trader import run_trader
from clients.gemini_client import GeminiClient
from clients.ig_data_downloader_client import IGDataDownloaderClient
from clients.ig_trading_client import IGTradingClient
from http_server.http_server import run_http_server
from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_listener import MarketDataListener
from market_data.market_data_repository import MarketDataRepository
from trade.trade_repository import TradeRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        TimedRotatingFileHandler(
            filename="../logs/aitrade.log",
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


if __name__ == "__main__":
    ### BEANS ###
    # clients
    gemini_client = GeminiClient()
    ig_trading_client = IGTradingClient("DEMO")
    ig_data_downloader_client = IGDataDownloaderClient()

    # market data
    market_data_repository = MarketDataRepository("../data/ai_trader.db")
    market_data_in_memory_info = MarketDataInMemoryInfo()
    market_data_listener = MarketDataListener(market_data_in_memory_info, market_data_repository)

    # trade
    trade_repository = TradeRepository("../data/ai_trader.db")


    ### SERVICES ###
    run_data_downloader(ig_data_downloader_client, market_data_repository, market_data_in_memory_info, market_data_listener, [DAX40, DOW, FTSE100, NASDAQ, SEMICONDUCTOR, US500])

    run_trader(gemini_client, ig_trading_client, trade_repository, market_data_repository, market_data_in_memory_info, market_data_listener, [US500])

    run_http_server()
