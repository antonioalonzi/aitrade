import logging
from datetime import datetime

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trading_strategy.ai_strategy_helper import _build_prompt_ai_market_data
from ai_trader.trading_strategy.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

class AiOpenStrategy():
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
        prompt_ai_market_data = _build_prompt_ai_market_data(self.market_data_repository, self.config, epic)
        return self.trading_engine.ask_to_open_a_position(now, self.config, epic, prompt_ai_market_data) if prompt_ai_market_data else None

