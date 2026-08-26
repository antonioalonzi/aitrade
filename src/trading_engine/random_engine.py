import random

from trade.trade import TradeDirection
from trading_engine.abstract_trading_engine import OpenPositionRecommendation, AbstractTradingEngine


class RandomEngine(AbstractTradingEngine):
    def ask_to_open_a_position(self, data: dict) -> OpenPositionRecommendation:
        directions = [TradeDirection.BUY, TradeDirection.SELL, TradeDirection.HOLD]
        weights = [0.01, 0.01, 0.98]

        selected_direction = random.choices(directions, weights=weights, k=1)[0]
        epic = random.choice(list(data.keys()))

        if selected_direction == TradeDirection.HOLD:
            return OpenPositionRecommendation(
                epic="NONE",
                direction=TradeDirection.HOLD,
                reasoning="Market conditions neutral. Holding cash.",
            )

        return OpenPositionRecommendation(
            epic=epic,
            direction=selected_direction,
            reasoning=f"Random mock trigger executed: {selected_direction.value}",
        )
