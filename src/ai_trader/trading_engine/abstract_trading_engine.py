from pydantic import BaseModel, Field

from ai_trader.trade.trade import TradeDirection


class OpenPositionRecommendation(BaseModel):
    direction: TradeDirection = Field(description="BUY, SELL, or HOLD.")
    reasoning: str = Field(description="Extremely brief technical rationale for the decision if BUY or SELL.")
    confidence: int = Field(description="Confidence level from 1 to 100 for the decision if BUY or SELL.")

class CloseDecision(BaseModel):
    should_close: bool

class AbstractTradingEngine:

    def ask_to_open_a_position(self, epic: str, data: dict) -> OpenPositionRecommendation:
        raise NotImplementedError("Subclasses must implement this method")

    def ask_to_close_a_position(self, open_position, data: dict) -> CloseDecision:
        raise NotImplementedError("Subclasses must implement this method")
