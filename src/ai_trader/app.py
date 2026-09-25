import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_engine.trader import Trader
from ai_trader.trading_engine.openai_engine import OpenAIEngine
from ai_trader.trading_platform.ig_trading_client import IGTradingClient

logger = logging.getLogger(__name__)


def _build_trading_engine() -> OpenAIEngine:
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")
    api_key = os.getenv("OPENAI_API_KEY")

    if not base_url or not model:
        raise ValueError(f"Missing required OpenAI configuration (BASE_URL={base_url}, MODEL={model}).")

    return OpenAIEngine(base_url=base_url, model=model, api_key=api_key)

def main():
    log_file = Path("./logs/ai_trader.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    data_dir = Path(os.getenv("DATA_DIR", "../../data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            TimedRotatingFileHandler(
                filename=log_file,
                when="D",
                interval=14,
                backupCount=12,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )


    load_dotenv()

    epics = [e.strip() for e in os.getenv("TRADING_EPICS", "").split(",") if e.strip()]
    confidence_threshold = int(os.getenv("CONFIDENCE_THRESHOLD", 50))

    trading_engine_bean = _build_trading_engine()
    ig_trading_client_bean = IGTradingClient("DEMO")
    trade_repository_bean = TradeRepository(str(data_dir / "ai_trades.db"))
    market_data_repository_bean = MarketDataRepository(str(data_dir / "ai_market_data.db"))

    trader = Trader(trading_engine_bean, ig_trading_client_bean, trade_repository_bean, market_data_repository_bean, confidence_threshold, epics)

    trader_scheduler = BackgroundScheduler()
    # Run every minute during day hours (e.g., 7:00 AM to 10:59 PM)
    trader_scheduler.add_job(trader.run, CronTrigger.from_crontab("* 7-22 * * *"))
    # Run every 10 minutes during night hours (e.g., 11 PM to 6 AM)
    # trader_scheduler.add_job(ai_trader.run, CronTrigger.from_crontab("*/10 0-6,23 * * *"))
    trader_scheduler.start()

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
