import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from ai_data_downloader import AiDataDownloader
from ai_trader import AiTrader
from trading_engine.gemini_engine import GeminiEngine

from trading_engine.abstract_trading_engine import AbstractTradingEngine
from trading_engine.random_engine import RandomEngine
from trading_platform.ig_data_downloader_client import IGDataDownloaderClient
from trading_platform.ig_trading_client import IGTradingClient
from http_server.http_server import AiTraderHTTPServer
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


def main():
    load_dotenv()

    ### BEANS ###
    # trading_engine
    trading_engine = _build_trading_engine(os.getenv("TRADING_ENGINE"))

    # trading_platform
    ig_trading_client = IGTradingClient("DEMO")
    ig_data_downloader_client = IGDataDownloaderClient()

    # market data
    market_data_repository = MarketDataRepository("../data/ai_trader.db")
    market_data_in_memory_info = MarketDataInMemoryInfo()
    market_data_listener = MarketDataListener(market_data_in_memory_info, market_data_repository)

    # trade
    trade_repository = TradeRepository("../data/ai_trader.db")


    ### SERVICES ###
    ai_data_downloader = AiDataDownloader(ig_data_downloader_client, market_data_repository, market_data_in_memory_info, market_data_listener, [DAX40, DOW, FTSE100, NASDAQ, SEMICONDUCTOR, US500])
    ai_data_downloader.subscribe_to_market_data()

    if trading_engine:
        ai_trader = AiTrader(trading_engine, ig_trading_client, trade_repository, market_data_repository, market_data_in_memory_info, market_data_listener, [US500, NASDAQ])
        ai_trader_scheduler = BackgroundScheduler()
        ai_trader_scheduler.add_job(ai_trader.run, CronTrigger.from_crontab("* * * * *"))
        ai_trader_scheduler.start()

    ai_trader_http_server = AiTraderHTTPServer(trade_repository)
    ai_trader_http_server.serve_forever()


def _build_trading_engine(trading_engine_config: str | None) -> AbstractTradingEngine | None:
    match trading_engine_config:
        case None | "off":
            return None
        case "random":
            return RandomEngine()
        case engine if engine.startswith("gemini"):
            return GeminiEngine(trading_engine_config)
        case _:
            raise ValueError(f"Unknown trading engine: {trading_engine_config}")


if __name__ == "__main__":
    main()
