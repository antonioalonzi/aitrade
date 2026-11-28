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
from ai_trader.openai.openai_client import OpenAIClient
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trader.trader import Trader
from ai_trader.trading_platform.ig_trading_client import IGTradingClient
from ai_trader.trading_strategy.ai_strategy import AiCloseStrategy, AiOpenStrategy
from ai_trader.trading_strategy.indicator_strategy import IndicatorCloseStrategy, IndicatorOpenStrategy
from ai_trader.trading_strategy.moving_average_strategy import MovingAverageOpenStrategy, MovingAverageCloseStrategy
from ai_trader.trading_strategy.strategy import OpenStrategy, CloseStrategy

logger = logging.getLogger(__name__)


def main():
    log_file = Path("./logs/ai_trader.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            TimedRotatingFileHandler(
                filename=log_file,
                when="D",
                interval=3,
                backupCount=3,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )



    load_dotenv()

    trader_config = load_trader_config()

    ig_account_type = os.environ["IG_ACCOUNT_TYPE"]
    ig_username = os.environ[ig_account_type + "_IG_SERVICE_USERNAME"]
    ig_password = os.environ[ig_account_type + "_IG_SERVICE_PASSWORD"]
    ig_api_key = os.environ[ig_account_type + "_IG_SERVICE_API_KEY"]
    ig_acc_type = os.environ[ig_account_type + "_IG_SERVICE_ACC_TYPE"]
    ig_acc_number = os.environ[ig_account_type + "_IG_SERVICE_ACC_NUMBER"]
    ig_trading_client_bean = IGTradingClient(ig_username, ig_password, ig_api_key, ig_acc_type, ig_acc_number)

    data_dir = Path(os.getenv("DATA_DIR", "../../data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    trade_repository_bean = TradeRepository(str(data_dir / "ai_trades.db"))
    market_data_repository_bean = MarketDataRepository(str(data_dir / "ai_market_data.db"))

    open_strategy = os.environ["OPEN_STRATEGY"]
    close_strategy = os.environ["CLOSE_STRATEGY"]
    logger.info(f"Trading Strategy: open={open_strategy}, close={close_strategy}")
    open_ai_client_bean = _build_open_ai_client(open_strategy, close_strategy)
    open_strategy_bean = _build_open_strategy_bean(market_data_repository_bean, open_ai_client_bean, open_strategy, trader_config)
    close_strategy_bean = _build_close_strategy_bean(close_strategy, market_data_repository_bean, open_ai_client_bean, trader_config)

    trader = Trader(open_strategy_bean, close_strategy_bean, ig_trading_client_bean, trade_repository_bean, market_data_repository_bean, trader_config)

    trader_scheduler = BackgroundScheduler()
    trader_scheduler.add_job(trader.run, CronTrigger.from_crontab("* * * * 0-4"))
    trader_scheduler.start()

    while True:
        time.sleep(60)


def load_trader_config() -> dict[str, list[str] | float | int | str]:
    trading_epics = os.environ["TRADING_EPICS"]
    leverage = float(os.getenv("LEVERAGE", 1.0))
    ai_strategy_decision_mode = os.getenv("AI_STRATEGY_DECISION_MODE", 'TICKS_AND_INDICATORS')
    indicator_ema_fast = int(os.getenv("INDICATOR_EMA_FAST", '10'))
    indicator_ema_slow = int(os.getenv("INDICATOR_EMA_SLOW", '30'))
    indicator_ema_trend = int(os.getenv("INDICATOR_EMA_TREND", '90'))
    evaluate_enter_the_market_interval_in_minutes = int(os.getenv('EVALUATE_ENTER_THE_MARKET_INTERVAL_IN_MINUTES', 1))
    evaluate_exit_the_market_interval_in_minutes = int(os.getenv('EVALUATE_EXIT_THE_MARKET_INTERVAL_IN_MINUTES', 1))
    trade_minimum_length_in_minutes = int(os.getenv('TRADE_MINIMUM_LENGTH_IN_MINUTES', 4))
    return {
        'epics': [e.strip() for e in trading_epics.split(",") if e.strip()],
        'leverage': leverage,
        'ai_strategy_decision_mode': ai_strategy_decision_mode,
        'indicator_ema_fast': indicator_ema_fast,
        'indicator_ema_slow': indicator_ema_slow,
        'indicator_ema_trend': indicator_ema_trend,
        'evaluate_enter_the_market_interval_in_minutes': evaluate_enter_the_market_interval_in_minutes,
        'evaluate_exit_the_market_interval_in_minutes': evaluate_exit_the_market_interval_in_minutes,
        'trade_minimum_length_in_minutes': trade_minimum_length_in_minutes,
    }


def _build_open_ai_client(open_strategy: str, close_strategy: str) -> OpenAIClient | None:
    if open_strategy == 'AiOpenStrategy' or close_strategy == 'AiCloseStrategy':
        logger.info("Loading AI config.")
        base_url = os.environ["OPENAI_BASE_URL"]
        model = os.environ["OPENAI_MODEL"]
        api_key = os.getenv("OPENAI_API_KEY")
        num_ctx = int(os.getenv("OPENAI_NUM_CTX", 2048))
        temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.1))
        timeout = int(os.getenv("OPENAI_TIMEOUT", 240))
        if not base_url or not model:
            raise ValueError(f"Missing required OpenAI configuration (BASE_URL={base_url}, MODEL={model}).")

        return OpenAIClient(base_url, model, api_key, num_ctx, temperature, timeout)

    return None


def _build_open_strategy_bean(market_data_repository_bean: MarketDataRepository, open_ai_client_bean: OpenAIClient | None, open_strategy: str, trader_config: dict[str, list[str] | float | int | str]) -> OpenStrategy:
    if open_strategy == 'AiOpenStrategy' and open_ai_client_bean:
        return AiOpenStrategy(open_ai_client_bean, market_data_repository_bean, trader_config)
    elif open_strategy == 'IndicatorOpenStrategy':
        return IndicatorOpenStrategy(market_data_repository_bean, trader_config)
    elif open_strategy == 'MovingAverageOpenStrategy':
        return MovingAverageOpenStrategy(market_data_repository_bean, trader_config)

    raise ValueError(f"open_strategy {open_strategy} not supported!")


def _build_close_strategy_bean(close_strategy: str, market_data_repository_bean: MarketDataRepository, open_ai_client_bean: OpenAIClient | None, trader_config: dict[str, list[str] | float | int | str]) -> CloseStrategy:
    if close_strategy == 'AiCloseStrategy' and open_ai_client_bean:
        return AiCloseStrategy(open_ai_client_bean, market_data_repository_bean, trader_config)
    elif close_strategy == 'IndicatorCloseStrategy':
        return IndicatorCloseStrategy(market_data_repository_bean, trader_config)
    elif close_strategy == 'MovingAverageCloseStrategy':
        return MovingAverageCloseStrategy(market_data_repository_bean, trader_config)

    raise ValueError(f"close_strategy {close_strategy} not supported!")



if __name__ == "__main__":
    main()
