import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataInMemoryInfo:
    def __init__(self) -> None:
        self.data = {}

    def process_tick(self, epic: str, timestamp: datetime, bid: float | None, offer: float | None, market_state: str | None) -> dict | None:
        tick_minute = timestamp.replace(second=0, microsecond=0)
        logger.debug(f"Processing tick: tick_minute={tick_minute}, epic={epic}, bid={bid}, offer={offer}, market_state={market_state}")

        if epic not in self.data:
            logger.debug(f"First tick for epic={epic}, initializing data structure.")
            self.data[epic] = {
                "latest_bid": bid,
                "latest_offer": offer,
                "market_state": market_state,
                "current_minute": tick_minute,
                "ticks": []
            }
            return None

        self.data[epic]["latest_bid"] = bid
        self.data[epic]["latest_offer"] = offer
        self.data[epic]["market_state"] = market_state
        self.data[epic]["ticks"].append((bid, offer))

        logger.debug(f"Next tick for tick_minute={tick_minute}, self.data[epic]['current_minute']={self.data[epic]["current_minute"]}.")
        if tick_minute > self.data[epic]["current_minute"]:
            logger.info(f"Building candle for epic={epic}")
            candle = self._build_candle(self.data.pop(epic))
            logger.info(f"Built candle for epic={epic}: {candle}")
            return candle

        self.data[epic]["current_minute"] = tick_minute

        return None

    def get_info(self, epic: str) -> dict:
        return self.data.get(epic, {})

    def _build_candle(self, epic_data: dict) -> dict:
        bids = [t[0] for t in epic_data["ticks"]]
        offers = [t[1] for t in epic_data["ticks"]]

        logger.info("is this called?")
        return {
            "datetime": epic_data["current_minute"],
            "bid_open": bids[0],
            "bid_high": max(bids),
            "bid_low": min(bids),
            "bid_close": bids[-1],
            "offer_open": offers[0],
            "offer_high": max(offers),
            "offer_low": min(offers),
            "offer_close": offers[-1],
            "close_spread": round(offers[-1] - bids[-1], 5),
            "volume": len(epic_data["ticks"])
        }
