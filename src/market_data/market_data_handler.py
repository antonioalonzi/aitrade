import logging
from datetime import datetime

from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_repository import MarketDataRepository

logger = logging.getLogger(__name__)


class MarketDataHandler:
    def __init__(self, market_data_in_memory_info: MarketDataInMemoryInfo,
                 market_data_repository: MarketDataRepository):
        self.market_data_in_memory_info = market_data_in_memory_info
        self.market_data_repository = market_data_repository

    def handle(self, item_name: str, data: dict):
        logger.info(f"Received MarketData: {item_name}: {data}")
        self._handle(item_name, data, datetime.now())

    def _handle(self, item_name: str, data: dict, timestamp: datetime):
        epic = item_name.split(":")[-1]
        bid = data.get("BID")
        offer = data.get("OFFER")
        market_state = data.get("MARKET_STATE")

        completed_candle = self.market_data_in_memory_info.process_tick(
            timestamp=timestamp,
            epic=epic,
            bid=bid,
            offer=offer,
            market_state=market_state,
        )

        if completed_candle:
            logger.info(f"Aggregated Candle: {completed_candle}")
            self.market_data_repository.insert_market_data(epic, completed_candle)