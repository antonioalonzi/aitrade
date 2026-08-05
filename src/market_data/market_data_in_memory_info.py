from datetime import datetime
from typing import Optional


class MarketDataInMemoryInfo:
    def __init__(self) -> None:
        self.data = {}

    def process_tick(self, epic: str, timestamp: datetime, bid: float | None, offer: float | None, market_state: str | None) -> Optional[dict]:
        """
        Updates latest state and aggregates tick data in a single call.
        Returns a completed candle dict on minute rollover, otherwise None.
        """
        tick_minute = timestamp.replace(second=0, microsecond=0)

        if epic not in self.data:
            self.data[epic] = {
                "latest_bid": bid,
                "latest_offer": offer,
                "market_state": market_state,
                "current_minute": tick_minute,
                "ticks": []
            }
        else:
            self.data[epic]["latest_bid"] = bid
            self.data[epic]["latest_offer"] = offer
            self.data[epic]["market_state"] = market_state

        epic_store = self.data[epic]
        current_minute = epic_store["current_minute"]
        completed_candle = None

        if current_minute is not None and tick_minute > current_minute:
            completed_candle = self._build_candle(epic)

        epic_store["current_minute"] = tick_minute
        epic_store["ticks"].append((bid, offer))

        return completed_candle

    def get_info(self, epic: str) -> dict:
        return self.data.get(epic, {})

    def _build_candle(self, epic: str) -> Optional[dict]:
        ticks = self.data[epic]["ticks"]
        if not ticks:
            return None

        bids = [t[0] for t in ticks]
        offers = [t[1] for t in ticks]

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
            "volume": len(ticks)
        }

        self.data[epic]["ticks"] = []
        return candle