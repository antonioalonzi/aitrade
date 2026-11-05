import logging
from datetime import datetime

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade
from ai_trader.trading_strategy.ai_strategy_helper import _build_prompt_ai_market_data
from ai_trader.trading_strategy.openai_client import OpenAIClient
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade

logger = logging.getLogger(__name__)

class AiCloseStrategy():
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
        prompt_ai_market_data = _build_prompt_ai_market_data(self.market_data_repository, self.config, open_position['epic'])
        return self.trading_engine.ask_to_close_a_position(now, config, open_position, profit_or_loss, prompt_ai_market_data) if prompt_ai_market_data else None
