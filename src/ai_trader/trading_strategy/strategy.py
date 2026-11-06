from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ai_trader.trade.trade import Trade


class OpenStrategy(ABC):
    @abstractmethod
    def evaluate(self, now: datetime, epic: str):
        raise NotImplementedError


class CloseStrategy(ABC):
    @abstractmethod
    def evaluate(self, now: datetime, config: dict, open_position: dict[str, Any], open_trade: Trade):
        raise NotImplementedError
