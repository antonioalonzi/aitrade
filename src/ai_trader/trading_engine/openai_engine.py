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
    direction: TradeDirection = Field(description="NONE, LONG, SHORT.")
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


    def ask_to_open_a_position(self, config: dict, epic: str, data: str):
        return self._ask(config, epic, 'ask_to_open_a_position', data, OpenPositionRecommendation)


    def ask_to_close_a_position(self, config: dict, open_position, profit_or_loss: float | None, data: str):
        return self._ask(config, open_position['epic'], 'ask_to_close_a_position', data, CloseDecision, open_position, profit_or_loss)


    def _ask(self, config: dict, epic: str, prompt_type: str, data: str, base_model: type[BaseModel], open_position = None, profit_or_loss: float | None = None) -> dict:
        system_prompt = self._get_system_prompt(config, epic, prompt_type, open_position, profit_or_loss)
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


    def _get_system_prompt(self, config: dict, epic: str, prompt_type: str, open_position = None, profit_or_loss: float | None = None) -> dict:
        if prompt_type == 'ask_to_open_a_position':
            return {
                "role": "system",
                "content": (
                    f"Analyze the following market data for {epic} and return:\n"
                    " - direction: NONE if should not trade, LONG if should trade and expect market to go up, SHORT if should trade and expect market to go down.\n"
                    " - reasoning: Brief technical rationale, target price expected to hit and the time.\n"
                    " - confidence: integer from 1 to 100 representing signal strength based on technical alignment. Use 60+ for moderate setup.\n\n"
                    "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:"
                    "t=timestamp; tf=timeframe (e.g. 15m for a 15 minute candle); o=open; h=high, l=low, c=close, v=volume.\n"
                    "Some indicators are provided, don't use just the indicator but consider all the ticks too.\n" if config['use_indicator_to_decide'] else ""
                    "\n"
                )
            }
        elif prompt_type == 'ask_to_close_a_position':
            return {
                "role": "system",
                "content": (
                    f"Analyze the following market data for {epic} and return:\n"
                    " - should_close: True if the position should be closed, False if it should be kept open.\n"
                    " - reasoning: Brief technical rationale.\n"
                    f"This is a low frequency day trading and the closing position is analysed every {config['evaluate_exit_the_market_interval_in_minutes']} minutes.\n"
                    "Do not make too many trades in a day to minimise costs. Do not close soon unless necessary."
                    "Do not close just because market did not move. Keep the position open unless market direction has changed and a loss is foreseen or to lock a good profit.\n"
                    f"This is the currently open position: {json.dumps(open_position)}\n"
                    f"The current position has a profit of: {profit_or_loss}\n"
                    "Consider the comment in the open position above when deciding if closing it.\n"
                    "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:"
                    "t=timestamp; tf=timeframe (e.g. 15m for a 15 minute candle); o=open; h=high, l=low, c=close, v=volume.\n"
                    "Some indicators are provided, don't use just the indicator but consider all the ticks too.\n" if config['use_indicator_to_decide'] else ""
                    "\n"
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
