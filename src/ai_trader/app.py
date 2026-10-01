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


def _build_trading_engine(base_url: str, model: str, api_key: str|None, num_ctx: int, temperature: float) -> OpenAIEngine:
    if not base_url or not model:
        raise ValueError(f"Missing required OpenAI configuration (BASE_URL={base_url}, MODEL={model}).")

    return OpenAIEngine(base_url=base_url, model=model, api_key=api_key)

def main():
    log_file = Path("./logs/ai_trader.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    load_dotenv()

    openai_base_url = os.environ["OPENAI_BASE_URL"]
    openai_model = os.environ["OPENAI_MODEL"]
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_num_ctx = int(os.getenv("OPENAI_NUM_CTX", 2048))
    openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.1))

    account_type = "DEMO"
    ig_username = os.environ[account_type + "_IG_SERVICE_USERNAME"]
    ig_password = os.environ[account_type + "_IG_SERVICE_PASSWORD"]
    ig_api_key = os.environ[account_type + "_IG_SERVICE_API_KEY"]
    ig_acc_type = os.environ[account_type + "_IG_SERVICE_ACC_TYPE"]
    ig_acc_number = os.environ[account_type + "_IG_SERVICE_ACC_NUMBER"]

    trading_epics = os.environ["TRADING_EPICS"]
    confidence_threshold = int(os.getenv("CONFIDENCE_THRESHOLD", 50))
    percentage_of_balance_to_trade = int(os.getenv("PERCENTAGE_OF_BALANCE_TO_TRADE", 50))
    use_indicator_to_decide = bool(os.getenv("USE_INDICATOR_TO_DECIDE", False))
    evaluate_enter_the_market_interval_in_minutes = int(os.getenv('EVALUATE_ENTER_THE_MARKET_INTERVAL_IN_MINUTES', 1))

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

    trader_config = {
        'epics': [e.strip() for e in trading_epics.split(",") if e.strip()],
        'confidence_threshold': confidence_threshold,
        'percentage_of_balance_to_trade': percentage_of_balance_to_trade,
        'use_indicator_to_decide': use_indicator_to_decide,
        'evaluate_enter_the_market_interval_in_minutes': evaluate_enter_the_market_interval_in_minutes
    }

    trading_engine_bean = _build_trading_engine(openai_base_url, openai_model, openai_api_key, openai_num_ctx, openai_temperature)
    ig_trading_client_bean = IGTradingClient(ig_username, ig_password, ig_api_key, ig_acc_type, ig_acc_number)
    trade_repository_bean = TradeRepository(str(data_dir / "ai_trades.db"))
    market_data_repository_bean = MarketDataRepository(str(data_dir / "ai_market_data.db"))


    trader = Trader(trading_engine_bean, ig_trading_client_bean, trade_repository_bean, market_data_repository_bean, trader_config)

    trader_scheduler = BackgroundScheduler()
    # Run every minute during day hours (e.g., 07:00 AM to 21:59 Mon to Fri)
    trader_scheduler.add_job(trader.run, CronTrigger.from_crontab("* 7-21 * * 0-4"))
    # Run every 10 minutes during night hours (e.g., 11 PM to 6 AM)
    # trader_scheduler.add_job(ai_trader.run, CronTrigger.from_crontab("*/10 0-6,23 * * 1-5"))
    trader_scheduler.start()

    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
