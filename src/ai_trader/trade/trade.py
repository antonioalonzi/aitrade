from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Trade:
    id: str
    epic: str
    amount: float
    direction: str
    confidence: int
    size: float
    opened_at: str
    open_price: float
    comment: str
    balance_at_opening: float
    closed_at: str | None = None
    close_price: float | None = None
    profit_or_loss: float | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Trade:
        return cls(
            id=row["id"],
            epic=row["epic"],
            amount=row["amount"],
            direction=row["direction"],
            confidence=row["confidence"],
            size=row["size"],
            opened_at=row["opened_at"],
            open_price=row["open_price"],
            comment=row["comments"],
            balance_at_opening=row["balance_at_opening"],
            closed_at=row["closed_at"],
            close_price=row["close_price"],
            profit_or_loss=row["profit_or_loss"]
        )

    def calculate_profit_and_loss(self, current_price: float) -> float | None:
        if self.direction == "BUY":
            return ((current_price - self.open_price) / self.open_price) * self.amount
        else:
            return ((self.open_price - current_price) / self.open_price) * self.amount
