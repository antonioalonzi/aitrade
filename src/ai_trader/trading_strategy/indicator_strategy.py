import json
import math
from dataclasses import dataclass
from datetime import datetime

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.openai.openai_client import CloseDecision, OpenPositionRecommendation
from ai_trader.trade.trade import Trade, TradeDirection
from ai_trader.trading_strategy.strategy import CloseStrategy, OpenStrategy
from ai_trader.trading_utils import trading_indicators, trading_utils
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade


@dataclass
class IndicatorValues:
    atr: float | None
    adx: float | None
    rsi: float | None
    fast_ema: list[float | None]
    slow_ema: list[float | None]
    trend_ema: list[float | None]


class IndicatorOpenStrategy(OpenStrategy):
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

        fast_now, slow_now, trend_now = fast[-1], slow[-1], trend[-1]
        emas_rising = fast[0] < fast[1] and slow[0] < slow[1] and trend[0] < trend[1]
        emas_falling = fast[0] > fast[1] and slow[0] > slow[1] and trend[0] > trend[1]

        if (
            fast_now > slow_now > trend_now
            and emas_rising
            and indicators.adx is not None
            and indicators.adx > 20
            and indicators.rsi is not None
            and 40 <= indicators.rsi <= 70
        ):
            return OpenPositionRecommendation(
                direction=TradeDirection.BUY,
                reasoning=f"BUY: EMA stack and directions confirmed; ADX={indicators.adx}, RSI={indicators.rsi}.",
            )

        if (
            fast_now < slow_now < trend_now
            and emas_falling
            and indicators.adx is not None
            and indicators.adx > 20
            and indicators.rsi is not None
            and 30 <= indicators.rsi <= 60
        ):
            return OpenPositionRecommendation(
                direction=TradeDirection.SELL,
                reasoning=f"SELL: EMA stack and directions confirmed; ADX={indicators.adx}, RSI={indicators.rsi}.",
            )

        return OpenPositionRecommendation(
            direction=TradeDirection.NONE,
            reasoning=f"No entry signal; ADX={indicators.adx}, RSI={indicators.rsi}.",
        )


class IndicatorCloseStrategy(CloseStrategy):
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
        last_price = get_last_price_for_trade(self.market_data_repository, open_trade)
        reasons = []

        if (
            indicators is not None
            and indicators.atr is not None
            and indicators.atr > 0
            and last_price is not None
        ):
            risk_distance = indicators.atr * 2.5
            reward_distance = indicators.atr * 5
            if open_trade.direction == TradeDirection.BUY:
                if last_price <= open_trade.open_price - risk_distance:
                    reasons.append("Stop loss reached.")
                if last_price >= open_trade.open_price + reward_distance:
                    reasons.append("Take profit reached.")
            else:
                if last_price >= open_trade.open_price + risk_distance:
                    reasons.append("Stop loss reached.")
                if last_price <= open_trade.open_price - reward_distance:
                    reasons.append("Take profit reached.")

        if indicators is not None:
            fast = _last_two(indicators.fast_ema)
            slow = _last_two(indicators.slow_ema)
            if fast and slow:
                if open_trade.direction == TradeDirection.BUY and fast[0] > slow[0] and fast[1] <= slow[1]:
                    reasons.append("Fast EMA crossed below slow EMA.")
                elif open_trade.direction == TradeDirection.SELL and fast[0] < slow[0] and fast[1] >= slow[1]:
                    reasons.append("Fast EMA crossed above slow EMA.")

            if indicators.adx is not None and indicators.adx < 15:
                reasons.append(f"Trend strength exhausted; ADX={indicators.adx}.")

        return CloseDecision(should_close=bool(reasons), reasoning=" ".join(reasons) or "No close signal.")


def calculate_indicators(
        now: datetime,
        ai_strategy_decision_mode: str,
        market_data_repository: MarketDataRepository,
        epic: str,
        config: dict
) -> str | None:
    if ai_strategy_decision_mode == "TICKS_ONLY":
        return None

    market_data = market_data_repository.get_latest_market_data(epic, 1, now)
    if market_data.empty:
        return None

    indicators = _calculate_indicator_values(market_data, config)
    if indicators is None:
        return None

    ema_lengths = {
        "fast": config["indicator_ema_fast"],
        "slow": config["indicator_ema_slow"],
        "trend": config["indicator_ema_trend"],
    }
    return json.dumps({
        "atr": indicators.atr,
        "adx": indicators.adx,
        "rsi": indicators.rsi,
        "emas": [
            _ema_values_to_dict(name, length, getattr(indicators, f"{name}_ema"))
            for name, length in ema_lengths.items()
        ],
    })


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
