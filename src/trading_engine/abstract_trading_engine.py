from pydantic import BaseModel, Field

from trade.trade import TradeDirection


class OpenPositionRecommendation(BaseModel):
    epic: str = Field(description="The epic identifier of the recommended trade, or 'NONE' if holding.")
    direction: TradeDirection = Field(description="BUY, SELL, or HOLD.")
    reasoning: str = Field(description="Brief technical rationale for the decision.")

class AbstractTradingEngine:

    def ask_to_open_a_position(self, data: dict) -> OpenPositionRecommendation:
        raise NotImplementedError("Subclasses must implement this method")
