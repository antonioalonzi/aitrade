import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataInMemoryInfo:
    def __init__(self) -> None:
        self.data = {}

    def process_tick(self, epic: str, timestamp: datetime, bid: float | None, offer: float | None, market_state: str | None) -> dict | None:
        tick_minute = timestamp.replace(second=0, microsecond=0)

        if epic not in self.data:
            logger.debug(f"Processing first tick: tick_minute={tick_minute}, epic={epic}, bid={bid}, offer={offer}, market_state={market_state}")
            self.data[epic] = {
                "current_minute": tick_minute,
                "market_state": market_state,
                "ticks": [(bid, offer)]
            }
            return None

        elif tick_minute <= self.data[epic]["current_minute"]:
            logger.debug(f"Processing same minute tick: tick_minute={tick_minute}, epic={epic}, bid={bid}, offer={offer}, market_state={market_state}")
            self.data[epic]["market_state"] = market_state
            self.data[epic]["ticks"].append((bid, offer))
            return None

        else:
            logger.debug(f"Processing next minute tick: tick_minute={tick_minute}, epic={epic}, bid={bid}, offer={offer}, market_state={market_state}")
            candle = self._build_candle(self.data[epic])
            self.data[epic] = {
                "current_minute": tick_minute,
                "market_state": market_state,
                "ticks": [(bid, offer)]
            }
            logger.debug(f"Built candle for epic={epic}: {candle}")
            return candle

    def get_info(self, epic: str) -> dict:
        return self.data.get(epic, {})

    def get_current_avg_price(self, epic: str) -> float | None:
        if not self.get_info(epic):
            return None

        tick = self.get_info(epic)["ticks"][-1]
        return (tick[0] + tick[1]) / 2

    def _build_candle(self, epic_data: dict) -> dict:
        bids = [t[0] for t in epic_data["ticks"]]
        offers = [t[1] for t in epic_data["ticks"]]

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
