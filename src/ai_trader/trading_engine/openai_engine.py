import json
import requests

from dotenv import load_dotenv

from ai_trader.trading_engine.abstract_trading_engine import OpenPositionRecommendation, AbstractTradingEngine, \
    CloseDecision


class OpenAIEngine(AbstractTradingEngine):
    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        load_dotenv()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def ask_to_open_a_position(self, data: str) -> OpenPositionRecommendation:
        prompt = (
            "Analyze the following technical snapshot and determine if it is worth entering a trade.\n"
            "Recommend AT MOST one trade: the single best opportunity across all epics provided.\n"
            "If signals are weak, noisy, or conflicting, select HOLD (no need to fill the reasoning).\n"
            "Keep reasoning really short.\n"
            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles formatted as a 2D array:\n"
            " - (timestamp, timeframe (e.g. '1m', '5m', '1h', '1D'), open, high, low, close.\n\n"
            f"{json.dumps(data)}"
        )

        req = self._payload(prompt, OpenPositionRecommendation.model_json_schema())
        res = requests.post(f"{self.base_url}/api/chat", json=req)
        return OpenPositionRecommendation.model_validate_json(json.loads(res.text.strip())["message"]["content"])


    def ask_to_close_a_position(self, open_position, data: str) -> CloseDecision:
        prompt = (
            "Analyze the following technical snapshot and determine if this position should be closed.\n"
            f"{json.dumps(open_position)}"
            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles formatted as a 2D array:\n"
            " - (timestamp, timeframe (e.g. '1m', '5m', '1h', '1D'), open, high, low, close.\n\n"
            f"{json.dumps(data)}"
        )

        req = self._payload(prompt, CloseDecision.model_json_schema())
        res = requests.post(f"{self.base_url}/api/chat", json=req)

        return CloseDecision.model_validate_json(json.loads(res.text.strip())["message"]["content"])

    def _payload(self, prompt: str, mode_schema: dict) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert algorithmic trading assistant for day trading on IG spread betting."},
                {"role": "user", "content": prompt}
            ],
            "format": mode_schema,
            "options": {
                "num_ctx": 8192,
                "temperature": 0.1
            },
            "stream": False
        }