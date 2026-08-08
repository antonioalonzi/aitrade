import logging
import sys
from datetime import datetime

from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_repository import MarketDataRepository

logger = logging.getLogger(__name__)

# https://lightstreamer.com/sdks/ls-python-client/2.1.0/api/lightstreamer.html
class MarketDataListener:
    def __init__(self, market_data_in_memory_info: MarketDataInMemoryInfo,
                 market_data_repository: MarketDataRepository):
        self.market_data_in_memory_info = market_data_in_memory_info
        self.market_data_repository = market_data_repository

    def onItemUpdate(self, item_update):
        item_name = item_update.getItemName()
        data = {
            "BID": item_update.getValue("BID"),
            "OFFER": item_update.getValue("OFFER"),
            "MARKET_STATE": item_update.getValue("MARKET_STATE"),
        }

        self._handle(item_name, data, datetime.now())

    def onSubscription(self):
        logger.info("Subscription SUCCESS: Subscribed to IG market stream.")

    def onSubscriptionError(self, code, message):
        logger.error(f"Subscription REJECTED (Code {code}): {message}")
        sys.exit(1)

    def _handle(self, item_name: str, data: dict, timestamp: datetime):
        epic = item_name.split(":")[-1]
        bid = data.get("BID")
        offer = data.get("OFFER")
        market_state = data.get("MARKET_STATE")
        logger.debug(f"Received item update - TIMESTAMP={timestamp}, EPIC={epic}, BID={bid}, OFFER={offer}, MARKET_STATE={market_state}")

        completed_candle = self.market_data_in_memory_info.process_tick(
            timestamp=timestamp,
            epic=epic,
            bid=bid,
            offer=offer,
            market_state=market_state,
        )

        logger.info(f"Completed candle: {completed_candle}")
        if completed_candle:
            logger.info(f"Aggregated Candle: {completed_candle}")
            self.market_data_repository.insert_market_data(epic, completed_candle)
