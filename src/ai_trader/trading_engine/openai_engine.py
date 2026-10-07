import json
import logging
import time
from datetime import datetime, timezone

import requests

from dotenv import load_dotenv
from pydantic import Field, BaseModel

from ai_trader.trade.trade import TradeDirection


logger = logging.getLogger(__name__)

class OpenPositionRecommendation(BaseModel):
    direction: TradeDirection = Field(description="NONE, BUY, SELL.")
    reasoning: str = Field(description="Brief technical rationale for the decision.")
    confidence: int = Field(description="Confidence level from 1 to 100 for the decision.")


class CloseDecision(BaseModel):
    should_close: bool
    reasoning: str = Field(description="Brief technical rationale for the decision.")


class OpenAIEngine:
    def __init__(self, base_url: str, model: str, api_key: str | None, num_ctx: int, temperature: float, timeout: int):
        load_dotenv()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.timeout = timeout


    def ask_to_open_a_position(self, epic: str, data: str):
        return self._ask(epic, 'ask_to_open_a_position', data, OpenPositionRecommendation)


    def ask_to_close_a_position(self, epic: str, open_position, data: str):
        return self._ask(epic, 'ask_to_close_a_position', data, CloseDecision, open_position)


    def _ask(self, epic: str, prompt_type: str, data: str, base_model: type[BaseModel], open_position = None):
        system_prompt = self._get_system_prompt(epic, prompt_type, open_position)
        user_prompt = {"role": "user", "content": f"London, {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S (%A)')}: Market data to analyse: {data}"}

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


    def _get_system_prompt(self, epic: str, prompt_type: str, open_position = None) -> dict:
        if prompt_type == 'ask_to_open_a_position':
            return {
                "role": "system",
                "content": (
                    f"Analyze the following market data for {epic} and return:\n"
                    " - direction: NONE if should not trade, BUY if should trade and expect market to go up, SELL if should trade and expect market to go down.\n"
                    " - reasoning: Brief technical rationale, target price expected to hit and the time.\n"
                    " - confidence: for the trade from 1 to 100 (low confidence will not be traded).\n\n"
                    "Do not open a trade on the last 10 minutes of the trading day (consider timezones)\n"
                    "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:"
                    "t=timestamp; tf=timeframe (e.g. 15m for a 15 minute candle); o=open; h=high, l=low, c=close, v=volume .\n\n"
                )
            }
        elif prompt_type == 'ask_to_close_a_position':
            return {
                "role": "system",
                "content": (
                    f"Analyze the following market data for {epic} and return:\n"
                    " - should_close: True if the position should be closed, False if it should be kept open.\n"
                    " - reasoning: Brief technical rationale.\n"
                    "Do not make too many trades in a day to minimise costs. Do not close soon unless necessary."
                    "Do not close just because market did not move, keep it open unless big loss foreseen or to materialize big win.\n"
                    "Try to close the trade on the last 10 minutes of a trading day (consider timezones).\n"
                    f"This is the currently open position: {json.dumps(open_position)}\n"
                    "Consider the comment in the open position above when deciding if closing it.\n"
                    "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:"
                    "t=timestamp; tf=timeframe (e.g. 15m for a 15 minute candle); o=open; h=high, l=low, c=close, v=volume .\n\n"
                )
            }

        raise ValueError("Invalid prompt type")

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
