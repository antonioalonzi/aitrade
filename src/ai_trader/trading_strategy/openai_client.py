import json
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from pydantic import Field, BaseModel

from ai_trader.trade.trade import TradeDirection

logger = logging.getLogger(__name__)

class OpenPositionRecommendation(BaseModel):
    direction: TradeDirection = Field(description="NONE, BUY, SELL.")
    reasoning: str | None = Field(description="Brief technical rationale for the decision.")
    confidence: int | None = Field(description="Confidence level from 1 to 100 for the decision.")


class CloseDecision(BaseModel):
    should_close: bool = Field(description="Boolean that says if the position should be closed or not.")
    reasoning: str | None = Field(description="Brief technical rationale for the decision.")


class OpenAIClient:
    def __init__(self, base_url: str, model: str, api_key: str | None, num_ctx: int, temperature: float, timeout: int):
        load_dotenv()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.timeout = timeout


    def ask_to_open_a_position(self, now: datetime, config: dict, epic: str, market_data: str | None, indicators: str | None):
        response = self._ask(now, config, epic, 'ask_to_open_a_position', market_data, indicators, OpenPositionRecommendation)
        if indicators:
            response.reasoning = 'indicators: ' + indicators + '\n\n' + response.reasoning
        return response


    def ask_to_close_a_position(self, now: datetime, config: dict, open_position, profit_or_loss: float, market_data: str | None, indicators: str | None):
        response = self._ask(now, config, open_position['epic'], 'ask_to_close_a_position', market_data, indicators, CloseDecision, open_position, profit_or_loss)
        if indicators:
            response.reasoning = 'indicators: ' + indicators + '\n\n' + response.reasoning
        return response


    def _ask(self, now: datetime, config: dict, epic: str, prompt_type: str, market_datadata: str | None, indicators: str | None, base_model: type[BaseModel], open_position = None, profit_or_loss: float | None = None) -> dict:
        system_prompt = {
            "role": "system",
            "content":
                self._get_system_prompt_init(epic) +
                self._get_system_prompt_response_format(prompt_type) +
                self._get_system_prompt_trading_strategy(prompt_type) +
                self._get_system_prompt_market_data(config['ai_strategy_decision_mode']) +
                self._get_system_prompt_indicators(config['ai_strategy_decision_mode'])
        }

        user_prompt = {
            "role": "user",
            "content":
                f"London, {now.astimezone(ZoneInfo("Europe/London")).strftime('%Y-%m-%d %H:%M:%S (%A)')}.\n\n" +
                self._get_system_prompt_open_position(open_position, profit_or_loss) +
                f"Market data to analyse: {market_datadata}\n\n" if market_datadata else "" +
                f"Indicators: {indicators}\n\n" if indicators else ""
        }

        request_json = {
            "model": self.model,
            "messages": [
                system_prompt,
                user_prompt
            ],
            "format": base_model.model_json_schema(),
            "options": {"num_ctx": self.num_ctx, "temperature": self.temperature},
            "stream": False
        }

        start = time.perf_counter()
        res = requests.post(f"{self.base_url}/api/chat", json=request_json, timeout=(5, self.timeout))
        end = time.perf_counter()

        if res.status_code != 200:
            raise RuntimeError(f"Ollama error {res.status_code}: {res.text}")

        response_json = json.loads(res.text.strip())
        content = response_json["message"]["content"]

        self._log_reponse_metrics(prompt_type, request_json, response_json, end - start)

        return base_model.model_validate_json(content)


    def _get_system_prompt_init(self, epic: str) -> str:
        return (
            f"You are a quantitative trading engine analyzing {epic} for a low frequency trend-following trading strategy.\n"
            "Your objective is to evaluate market structure and return:\n"
        )

    def _get_system_prompt_response_format(self, prompt_type: str) -> str:
        if prompt_type == 'ask_to_open_a_position':
            return (
                " - direction: NONE if should not trade, BUY if should trade and expect market to go up (long position), SELL if should trade and expect market to go down (short position).\n"
                " - reasoning: Brief technical rationale.\n"
                " - confidence: integer from 1 to 100.\n\n"
            )
        elif prompt_type == 'ask_to_close_a_position':
            return (
                " - should_close: True if the position should be closed, False if it should be kept open.\n"
                " - reasoning: Brief technical rationale.\n"
            )
        return ''

    def _get_system_prompt_trading_strategy(self, prompt_type: str) -> str:
        if prompt_type == 'ask_to_open_a_position':
            return ''
        elif prompt_type == 'ask_to_close_a_position':
            return ''
        return ''

    def _get_system_prompt_market_data(self, ai_strategy_decision_mode: str) -> str:
        if ai_strategy_decision_mode == 'INDICATORS_ONLY':
            return ''
        else:
            return (
                "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:"
                " - t=timestamp; tf=timeframe (e.g. 15m for a 15 minute candle); o=open; h=high, l=low, c=close, v=volume.\n"
            )

    def _get_system_prompt_indicators(self, ai_strategy_decision_mode: str) -> str:
        if ai_strategy_decision_mode == 'TICKS_ONLY':
            return ''
        else:
            return "Evaluate raw ticks alongside indicators: rsi, atr, adx, ema_x (latest x minutes ema in chronological oldest-to-newest).\n"

    def _get_system_prompt_open_position(self, open_position, profit_or_loss: float | None) -> str:
        if open_position == 'TICKS_ONLY':
            return (
                f"Currently open position: {json.dumps(open_position)}\n"
                f"Current profit of: {profit_or_loss}\n"
            )
        else:
            return ''


    def _log_reponse_metrics(self, prompt_type: str, request, response, duration: float):
        metrics = {
            "request_length": len(json.dumps(request)),
            "response_length": len(json.dumps(response)),
            "prompt_tokens": response.get("prompt_eval_count"),
            "response_tokens": response.get("eval_count"),
            "prefill_ms": response.get("prompt_eval_duration", 0) / 1_000_000,
            "eval_ms": response.get("eval_duration", 0) / 1_000_000,
            "total_ms": response.get("total_duration", 0) / 1_000_000,
        }
        logger.info(f"{prompt_type} [metrics={metrics}] (Duration: {duration:.3f} sec)   <--   {json.dumps(response["message"]["content"])})")
