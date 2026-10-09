from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

class TradeSummaryType(str, Enum):
    DAILY = "%Y-%m-%d"
    WEEKLY = "%Y-%W"
    MONTHLY = "%Y-%m"

@dataclass
class TradeSummary:
    timeframe: str
    total_trades: int
    net_pnl: float
    net_pnl_perc: float
    avg_pnl: float
    balance_at_opening: float

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> TradeSummary:
        return cls(
            timeframe=row["timeframe"],
            total_trades=row["total_trades"],
            net_pnl=row["net_pnl"],
            net_pnl_perc=row["net_pnl_perc"],
            avg_pnl=row["avg_pnl"],
            balance_at_opening=row["balance_at_opening"],
        )
