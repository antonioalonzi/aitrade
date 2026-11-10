import json
import logging
from datetime import datetime

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade
from ai_trader.trading_strategy.openai_client import OpenAIClient
from ai_trader.trading_strategy.strategy import CloseStrategy, OpenStrategy
from ai_trader.trading_utils import trading_indicators, trading_utils
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade

logger = logging.getLogger(__name__)


def _build_market_data_ticks_for_ai(ai_strategy_decision_mode: str, market_data_repository: MarketDataRepository, epic: str) -> str | None:
    if ai_strategy_decision_mode == 'INDICATORS_ONLY':
        return None

    epic_data = market_data_repository.get_latest_market_data(epic)
    if not epic_data.empty:
        avg_epic_data = trading_utils.avg_bid_offer(epic_data)
        ticks = trading_utils.aggregate_for_ai(avg_epic_data)
        return json.dumps(ticks)

    return None


def calculate_indicators(ai_strategy_decision_mode: str, market_data_repository: MarketDataRepository, epic: str, config: dict) -> str | None:
    if ai_strategy_decision_mode == 'TICKS_ONLY':
        return None

    epic_data = market_data_repository.get_latest_market_data(epic)
    if not epic_data.empty:
        avg_epic_data = trading_utils.avg_bid_offer(epic_data)
        indicators = {
            "atr": trading_indicators.atr(avg_epic_data, 14, 1)[0],
            "adx": trading_indicators.adx(avg_epic_data, 14, 1)[0],
            "rsi": trading_indicators.rsi(avg_epic_data, 14, 1)[0],
            f"ema_fast_{config['indicator_ema_fast']}": trading_indicators.window_exponential_average(avg_epic_data, config['indicator_ema_fast'], 2),
            f"ema_slow_{config['indicator_ema_slow']}": trading_indicators.window_exponential_average(avg_epic_data, config['indicator_ema_slow'], 2),
            f"ema_trend_{config['indicator_ema_trend']}": trading_indicators.window_exponential_average(avg_epic_data, config['indicator_ema_trend'], 2),
        }

        logger.info(f"indicators: {json.dumps(indicators)}")
        return json.dumps(indicators)

    return None


class AiOpenStrategy(OpenStrategy):
    def __init__(
            self,
            trading_engine: OpenAIClient,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.trading_engine = trading_engine
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def evaluate(self, now: datetime, epic: str):
        prompt_ai_market_data = _build_market_data_ticks_for_ai(self.config['ai_strategy_decision_mode'], self.market_data_repository, epic)
        indicators = calculate_indicators(self.config['ai_strategy_decision_mode'], self.market_data_repository, epic, self.config)
        return self.trading_engine.ask_to_open_a_position(now, self.config, epic, prompt_ai_market_data, indicators)


class AiCloseStrategy(CloseStrategy):
    def __init__(
            self,
            trading_engine: OpenAIClient,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.trading_engine = trading_engine
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def evaluate(self, now: datetime, config: dict, open_position, open_trade: Trade):
        last_price = get_last_price_for_trade(self.market_data_repository, open_trade)
        profit_or_loss = open_trade.calculate_profit_and_loss(last_price)
        prompt_ai_market_data = _build_market_data_ticks_for_ai(self.config['ai_strategy_decision_mode'], self.market_data_repository, open_position['epic'])
        indicators = calculate_indicators(self.config['ai_strategy_decision_mode'], self.market_data_repository, open_position['epic'], self.config)
        return self.trading_engine.ask_to_close_a_position(now, config, open_position, profit_or_loss, prompt_ai_market_data, indicators)

