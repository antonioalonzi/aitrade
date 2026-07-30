import logging
from datetime import datetime, timedelta

from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_repository import MarketDataRepository

logger = logging.getLogger(__name__)

class MarketDataHandler:
    def __init__(self, market_data_in_memory_info: MarketDataInMemoryInfo, market_data_repository: MarketDataRepository):
        self.market_data_in_memory_info = market_data_in_memory_info
        self.market_data_repository = market_data_repository
        self.data = {}

    def handle(self, item_name, data):
        epic = item_name.split(":")[-1]
        bid = data.get("BID")
        offer = data.get("OFFER")
        market_state = data.get("MARKET_STATE")

        self.market_data_in_memory_info.set_info(
            epic=epic,
            info={"latest_bid": bid, "latest_offer": offer, "market_state": market_state}
        )

        if epic not in self.data:
            self.data[epic] = {
                "current_minute": None,
                "ticks": []
            }

        self._aggregate_1m_candle(epic, bid, offer)

    def _aggregate_1m_candle(self, epic: str, bid: float, offer: float):
        now = datetime.now()
        tick_minute = now.replace(second=0, microsecond=0)

        epic_store = self.data[epic]
        current_minute = epic_store["current_minute"]

        if current_minute is not None and tick_minute > current_minute:
            self._finalize_candle(epic)

        epic_store["current_minute"] = tick_minute
        epic_store["ticks"].append((bid, offer))

    def _finalize_candle(self, epic: str):
        if not self.data[epic]["ticks"]:
            return

        bids = [t[0] for t in (self.data[epic]["ticks"])]
        offers = [t[1] for t in (self.data[epic]["ticks"])]

        candle = {
            "datetime": self.data[epic]["current_minute"],
            "bid_open": bids[0],
            "bid_high": max(bids),
            "bid_low": min(bids),
            "bid_close": bids[-1],
            "offer_open": offers[0],
            "offer_high": max(offers),
            "offer_low": min(offers),
            "offer_close": offers[-1],
            "close_spread": round(offers[-1] - bids[-1], 5),
            "volume": len(self.data[epic]["ticks"])
        }

        self.market_data_repository.insert_market_data(epic, candle)

        self.data[epic]["ticks"] = []
