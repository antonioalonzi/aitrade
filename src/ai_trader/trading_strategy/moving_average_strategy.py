import math
from dataclasses import dataclass
from datetime import datetime

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.openai.openai_client import CloseDecision, OpenPositionRecommendation
from ai_trader.trade.trade import Trade, TradeDirection
from ai_trader.trading_strategy.strategy import CloseStrategy, OpenStrategy
from ai_trader.trading_utils import trading_indicators, trading_utils


@dataclass
class IndicatorValues:
    atr: float | None
    adx: float | None
    rsi: float | None
    fast_ema: list[float | None]
    slow_ema: list[float | None]
    trend_ema: list[float | None]


class MovingAverageOpenStrategy(OpenStrategy):
    def __init__(
            self,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def evaluate(self, now: datetime, epic: str) -> OpenPositionRecommendation:
        market_data = self.market_data_repository.get_latest_market_data(epic, 1, now)
        if market_data.empty:
            return OpenPositionRecommendation(direction=TradeDirection.NONE, reasoning="No market data.")

        indicators = _calculate_indicator_values(market_data, self.config)
        if indicators is None:
            return OpenPositionRecommendation(direction=TradeDirection.NONE, reasoning="Indicators unavailable.")

        fast = _last_two(indicators.fast_ema)
        slow = _last_two(indicators.slow_ema)
        trend = _last_two(indicators.trend_ema)
        if not fast or not slow or not trend:
            return OpenPositionRecommendation(direction=TradeDirection.NONE, reasoning="EMA values unavailable.")

        if (
            fast[0] <= slow[0] < trend[0]
            and fast[1] > slow[1]
            and fast[1] < trend[1]
        ):
            return OpenPositionRecommendation(
                direction=TradeDirection.BUY,
                reasoning=f"{indicators}\n\nBUY: Fast EMA crossed above slow EMA toward trend EMA.",
            )

        if (
            fast[0] >= slow[0] > trend[0]
            and fast[1] < slow[1]
            and fast[1] > trend[1]
        ):
            return OpenPositionRecommendation(
                direction=TradeDirection.SELL,
                reasoning=f"{indicators}\n\nSELL: Fast EMA crossed below slow EMA toward trend EMA.",
            )

        return OpenPositionRecommendation(
            direction=TradeDirection.NONE,
            reasoning="No EMA crossover entry signal.",
        )


class MovingAverageCloseStrategy(CloseStrategy):
    def __init__(
            self,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def evaluate(
            self,
            now: datetime,
            config: dict,
            open_position: dict,
            open_trade: Trade
    ) -> CloseDecision:
        market_data = self.market_data_repository.get_latest_market_data(open_trade.epic, 1, now)
        indicators = _calculate_indicator_values(market_data, self.config)
        reasons = []

        if indicators is not None:
            slow = _last_two(indicators.slow_ema)
            trend = _last_two(indicators.trend_ema)
            if slow and trend:
                crossed_up = slow[0] < trend[0] and slow[1] >= trend[1]
                crossed_down = slow[0] > trend[0] and slow[1] <= trend[1]
                if crossed_up or crossed_down:
                    reasons.append("Slow EMA crossed trend EMA.")

        return CloseDecision(should_close=bool(reasons), reasoning=" ".join(reasons) or "No close signal.")



def _calculate_indicator_values(market_data, config: dict) -> IndicatorValues | None:
    if market_data.empty:
        return None

    avg_market_data = trading_utils.avg_bid_offer(market_data)
    return IndicatorValues(
        atr=_latest_finite(trading_indicators.atr(avg_market_data, 14, 1)),
        adx=_latest_finite(trading_indicators.adx(avg_market_data, 14, 1)),
        rsi=_latest_finite(trading_indicators.rsi(avg_market_data, 14, 1)),
        fast_ema=_finite_values(trading_indicators.window_exponential_average(
            avg_market_data, config["indicator_ema_fast"], 2
        )),
        slow_ema=_finite_values(trading_indicators.window_exponential_average(
            avg_market_data, config["indicator_ema_slow"], 2
        )),
        trend_ema=_finite_values(trading_indicators.window_exponential_average(
            avg_market_data, config["indicator_ema_trend"], 2
        )),
    )


def _latest_finite(values: list[float]) -> float | None:
    return _finite_value(values[-1]) if values else None


def _finite_values(values: list[float]) -> list[float | None]:
    return [_finite_value(value) for value in values]


def _finite_value(value: float) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _last_two(values: list[float | None]) -> list[float] | None:
    if len(values) < 2:
        return None
    previous, latest = values[-2:]
    if previous is None or latest is None:
        return None
    return [previous, latest]


def _ema_values_to_dict(name: str, length: int, values: list[float | None]) -> dict:
    ema_values = [value for value in values if value is not None]
    direction = "UP" if len(ema_values) == 2 and ema_values[1] > ema_values[0] else "DOWN"
    return {
        f"ema_{name}_{length}": {
            "values": values,
            "direction": direction,
        }
    }
