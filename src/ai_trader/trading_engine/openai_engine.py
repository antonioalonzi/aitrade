import json
import logging
import time
from datetime import datetime

import requests

from dotenv import load_dotenv
from pydantic import Field, BaseModel

from ai_trader.trade.trade import TradeDirection


logger = logging.getLogger(__name__)

class OpenPositionRecommendation(BaseModel):
    direction: TradeDirection = Field(description="BUY, SELL.")
    reasoning: str = Field(description="Extremely brief technical rationale for the decision.")
    confidence: int = Field(description="Confidence level from 1 to 100 for the decision.")


class CloseDecision(BaseModel):
    should_close: bool
    reasoning: str = Field(description="Extremely brief technical rationale for the decision.")


class OpenAIEngine:
    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        load_dotenv()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.sessions = {}


    def forget_sessions(self) -> None:
        self.sessions = {}


    def ask_to_open_a_position(self, epic: str, data: str):
        return self._ask(epic, 'ask_to_open_a_position', data, OpenPositionRecommendation)


    def ask_to_close_a_position(self, epic: str, open_position, data: str):
        return self._ask(epic, 'ask_to_close_a_position', data, CloseDecision, open_position)


    def _ask(self, epic: str, prompt_type: str, data: str, base_model: type[BaseModel], open_position = None):
        system_prompt = self._get_system_prompt(epic, prompt_type, open_position)
        user_prompt = {"role": "user", "content": f"London, {datetime.now().strftime('%Y-%m-%d %H:%M:%S (%A)')}: Market data to analyse: {data}"}

        request_json = {
            "model": self.model,
            "messages": [
                system_prompt,
                user_prompt
            ],
            "format": base_model.model_json_schema(),
            "options": {"num_ctx": 16384, "temperature": 0.1},
            "stream": False
        }

        start = time.perf_counter()
        res = requests.post(f"{self.base_url}/api/chat", json=request_json)
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
                    f"Analyze the following market data for {epic} and determine what type of trade would be best to enter.\n"
                    "Return a confidence for the trade from 1 to 100.\n"
                    "Use direction BUY if predicting that the market is going up and direction SELL if predicting the market is going down.\n"
                    "Extremely brief technical rationale (max 1 sentence).\n"
                    "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles formatted as a 2D array:\n"
                    " - (timestamp, timeframe (e.g. '1m', '5m', '1h', '1D'), open, high, low, close.\n\n"
                )
            }
        elif prompt_type == 'ask_to_close_a_position':
            return {
                "role": "system",
                "content": (
                    f"Analyze the following market data for {epic} and determine if this position should be closed.\n"
                    "Note it's a day trading, so position should rarely be kept overnight and never during weekends.\n"
                    "Try to not make too many trades in a day to minimise costs, so don't close extremely early if not necessary.\n"
                    "Extremely brief technical rationale (max 1 sentence).\n"
                    f"{json.dumps(open_position)}\n"
                    "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:\n"
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
