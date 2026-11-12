import json
from datetime import datetime
from zoneinfo import ZoneInfo

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade
from ai_trader.openai.openai_client import OpenAIClient, OpenPositionRecommendation, CloseDecision
from ai_trader.trading_strategy.strategy import CloseStrategy, OpenStrategy
from ai_trader.trading_utils import trading_indicators, trading_utils
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade


class AiOpenStrategy(OpenStrategy):
    def __init__(
            self,
            open_ai_client: OpenAIClient,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.open_ai_client = open_ai_client
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def evaluate(self, now: datetime, epic: str):
        prompt_ai_market_data = _build_market_data_ticks_for_ai(now, self.config['ai_strategy_decision_mode'], self.market_data_repository, epic)
        indicators = calculate_indicators(now, self.config['ai_strategy_decision_mode'], self.market_data_repository, epic, self.config)

        system_prompt = _get_system_prompt(epic, 'open_a_position', self.config)
        user_prompt = _get_user_prompt(now, prompt_ai_market_data, indicators, None, None, 'open_a_position')

        response = self.open_ai_client.ask(system_prompt, user_prompt, OpenPositionRecommendation)

        if indicators:
            response.reasoning = 'indicators: ' + indicators + '\n\n' + (response.reasoning or '')
        return response


class AiCloseStrategy(CloseStrategy):
    def __init__(
            self,
            open_ai_client: OpenAIClient,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.open_ai_client = open_ai_client
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def evaluate(self, now: datetime, config: dict, open_position, open_trade: Trade):
        last_price = get_last_price_for_trade(self.market_data_repository, open_trade)
        profit_or_loss = open_trade.calculate_profit_and_loss(last_price)
        prompt_ai_market_data = _build_market_data_ticks_for_ai(now, self.config['ai_strategy_decision_mode'], self.market_data_repository, open_position['epic'])
        indicators = calculate_indicators(now, self.config['ai_strategy_decision_mode'], self.market_data_repository, open_position['epic'], self.config)

        system_prompt = _get_system_prompt(open_position['epic'], 'close_a_position', self.config)
        user_prompt = _get_user_prompt(now, prompt_ai_market_data, indicators, open_position, profit_or_loss, 'close_a_position')

        response = self.open_ai_client.ask(system_prompt, user_prompt, CloseDecision)

        if indicators:
            response.reasoning = 'indicators: ' + indicators + '\n\n' + (response.reasoning or '')
        return response




def _build_market_data_ticks_for_ai(now: datetime, ai_strategy_decision_mode: str, market_data_repository: MarketDataRepository, epic: str) -> str | None:
    if ai_strategy_decision_mode == 'INDICATORS_ONLY':
        return None

    epic_data = market_data_repository.get_latest_market_data(epic, 1, now)
    if not epic_data.empty:
        avg_epic_data = trading_utils.avg_bid_offer(epic_data)
        ticks = trading_utils.aggregate_for_ai(avg_epic_data)
        return json.dumps(ticks)

    return None


def calculate_indicators(now: datetime, ai_strategy_decision_mode: str, market_data_repository: MarketDataRepository, epic: str, config: dict) -> str | None:
    if ai_strategy_decision_mode == 'TICKS_ONLY':
        return None

    epic_data = market_data_repository.get_latest_market_data(epic, 1, now)
    if not epic_data.empty:
        avg_epic_data = trading_utils.avg_bid_offer(epic_data)
        indicators = {
            "atr": trading_indicators.atr(avg_epic_data, 14, 1)[0],
            "adx": trading_indicators.adx(avg_epic_data, 14, 1)[0],
            "rsi": trading_indicators.rsi(avg_epic_data, 14, 1)[0],
            "emas": [
                ema_data_to_string("fast", config['indicator_ema_fast'], avg_epic_data),
                ema_data_to_string("slow", config['indicator_ema_slow'], avg_epic_data),
                ema_data_to_string("trend", config['indicator_ema_trend'], avg_epic_data)
            ],
        }
        return json.dumps(indicators)

    return None

def ema_data_to_string(type: str, length: int, avg_epic_data) -> dict:
    ema = trading_indicators.window_exponential_average(avg_epic_data, length, 2)
    direction = "UP" if len(ema) == 2 and ema[1] > ema[0] else "DOWN"
    return {
        f"ema_{type}_{length}": {
            'values': ema,
            'direction': direction
        }
    }





def _get_system_prompt(epic: str, prompt_type: str, config: dict) -> str:
    return (
            _get_system_prompt_init(epic) +
            _get_system_prompt_trading_strategy(prompt_type) +
            _get_system_prompt_market_data(config['ai_strategy_decision_mode']) +
            _get_system_prompt_indicators(config['ai_strategy_decision_mode'])
    )

def _get_system_prompt_init(epic: str) -> str:
    return (
        f"You are a quantitative trading engine analyzing {epic} for a low frequency trend-following trading strategy.\n"
        "Your objective is to evaluate market structure and return:\n"
    )

def _get_system_prompt_response_format(prompt_type: str) -> str:
    if prompt_type == 'open_a_position':
        return (
            " - direction: NONE if should not trade, BUY if should trade and expect market to go up (long position), SELL if should trade and expect market to go down (short position).\n"
            " - reasoning: Brief technical rationale.\n"
            " - confidence: integer from 1 to 100.\n\n"
        )
    elif prompt_type == 'close_a_position':
        return (
            " - should_close: True if the position should be closed, False if it should be kept open.\n"
            " - reasoning: Brief technical rationale.\n"
        )
    return ''

def _get_system_prompt_trading_strategy(prompt_type: str) -> str:
    if prompt_type == 'open_a_position':
        return (
            'Strategy (all below apply):\n'
            ' - EMA Stack Verified: Fast > Slow > Trend (Buy) or Fast < Slow < Trend (Sell).\n'
            ' - EMA Direction Verified: Fast, Slow, Trend directions are UP (Buy) or Fast, Slow, Trend directions are DOWN (Sell).\n'
            ' - Trend Strength Check: ADX > 20 to confirm an actual trend instead of sideways market chop.\n'
            ' - RSI Filter Passed: 40–70 for Buy, 30–60 for Sell to dodge overbought/oversold traps.\n'
        )
    elif prompt_type == 'close_a_position':
        return (
            'Minimum Age Check: Hold position for at least 3 to 5 minutes before evaluating exit rules to absorb spread noise.\n'
            '\n'
            'Strategy (any below applies):\n'
            ' - Stop Loss Breach: Price hit entry minus/plus ATR x 2.5 risk limit.\n'
            ' - Take Profit Reached: Price hit target at ATR x 5 reward multiple.\n'
            ' - Trend Collapse / Exhaustion: EMA Fast/Slow crossed back or ADX dropped below 15.\n'
        )
    return ''

def _get_system_prompt_market_data(ai_strategy_decision_mode: str) -> str:
    if ai_strategy_decision_mode != 'INDICATORS_ONLY':
        return (
            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:"
            " - t=timestamp; tf=timeframe (e.g. 15m for a 15 minute candle); o=open; h=high, l=low, c=close, v=volume.\n"
        )
    else:
        return ''

def _get_system_prompt_indicators(ai_strategy_decision_mode: str) -> str:
    if ai_strategy_decision_mode == 'TICKS_ONLY':
        return "Evaluate raw ticks alongside indicators: rsi, atr, adx, ema_x (latest x minutes ema in chronological oldest-to-newest).\n"
    else:
        return ''



def _get_user_prompt(now: datetime, market_data: str | None, indicators: str | None, open_position, profit_or_loss: float | None, prompt_type: str) -> str:
    return (
        f"London, {now.astimezone(ZoneInfo("Europe/London")).strftime('%Y-%m-%d %H:%M:%S (%A)')}.\n\n" +
        _get_user_prompt_open_position(open_position, profit_or_loss) +
        _get_user_prompt_market_data(market_data) +
        _get_user_prompt_indicators(indicators) +
        _get_user_prompt_final_text(prompt_type)
    )

def _get_user_prompt_open_position(open_position, profit_or_loss: float | None) -> str:
    if open_position:
        position_type = "LONG" if open_position['direction'] == 'BUY' else "SHORT"
        return (
            f"The current open position is a {position_type} position opened at {open_position['createdDate']} at price {open_position['level']}."
            f"The current profit is: {profit_or_loss}\n"
        )
    else:
        return ''

def _get_user_prompt_market_data(market_data: str | None) -> str:
    return f"Latest aggregated market data: {market_data}\n\n" if market_data else ""

def _get_user_prompt_indicators(indicators: str | None) -> str:
    return f"Latest technical indicators: {indicators}\n\n" if indicators else ""

def _get_user_prompt_final_text(prompt_type: str) -> str:
    if prompt_type == 'open_a_position':
        return (
            "Based on the above data, please provide your recommendation for opening a position.\n"
        )
    elif prompt_type == 'close_a_position':
        return (
            "Based on the above data, please provide your recommendation for closing the position.\n"
        )
    return ''