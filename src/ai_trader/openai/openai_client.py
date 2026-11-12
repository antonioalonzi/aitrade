import json
import logging
import time

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

    def ask(self, system_prompt_text: str, user_prompt_text: str, base_model: BaseModel) -> dict:
        request_json = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt_text
                },
                {
                    "role": "user",
                    "content": user_prompt_text
                }
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

        self._log_reponse_metrics(request_json, response_json, end - start)

        return base_model.model_validate_json(content)


    def _log_reponse_metrics(self, request, response, duration: float):
        metrics = {
            "request_length": len(json.dumps(request)),
            "response_length": len(json.dumps(response)),
            "prompt_tokens": response.get("prompt_eval_count"),
            "response_tokens": response.get("eval_count"),
            "prefill_ms": response.get("prompt_eval_duration", 0) / 1_000_000,
            "eval_ms": response.get("eval_duration", 0) / 1_000_000,
            "total_ms": response.get("total_duration", 0) / 1_000_000,
        }
        logger.info(f" Request: {json.dumps(request['messages'])}[metrics={metrics}] -- (Duration: {duration:.3f} sec) -- Response: {json.dumps(response["message"]["content"])})")
