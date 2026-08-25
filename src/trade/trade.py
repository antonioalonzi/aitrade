from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class Trade:
    id: str
    epic: str
    amount: float
    direction: str
    size: float
    opened_at: str
    open_price: float
    comment: str | None = None
    closed_at: str | None = None
    close_price: float | None = None
    profit_or_loss: float | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Trade":
        return cls(
            id=row["id"],
            epic=row["epic"],
            amount=row["amount"],
            direction=row["direction"],
            size=row["size"],
            opened_at=row["opened_at"],
            open_price=row["open_price"],
            closed_at=row["closed_at"],
            close_price=row["close_price"],
            profit_or_loss=row["profit_or_loss"],
            comment=row["comments"]
        )
