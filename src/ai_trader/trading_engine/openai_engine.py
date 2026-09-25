import json
import requests

from dotenv import load_dotenv
from pydantic import Field, BaseModel

from ai_trader.trade.trade import TradeDirection


class OpenPositionRecommendation(BaseModel):
    direction: TradeDirection = Field(description="BUY, SELL.")
    reasoning: str = Field(description="Extremely brief technical rationale for the decision.")
    confidence: int = Field(description="Confidence level from 1 to 100 for the decision.")


class CloseDecision(BaseModel):
    should_close: bool


class OpenAIEngine:
    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        load_dotenv()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.sessions = {}


    def forget_sessions(self) -> None:
        self.sessions = {}


    def ask_to_open_a_position(self, epic: str, data: dict):
        return self._ask(epic, 'open', data, OpenPositionRecommendation)


    def ask_to_close_a_position(self, epic: str, open_position, data: dict):
        return self._ask(epic, 'close', data, CloseDecision, open_position)


    def _ask(self, epic: str, session_type: str, data: dict, base_model: type[BaseModel], open_position = None):
        messages = self._get_session(epic, session_type, open_position)
        messages.append({"role": "user", "content": f"Append this data and analyse: {json.dumps(data)}"})

        req = {
            "model": self.model,
            "messages": messages,
            "format": base_model.model_json_schema(),
            "options": {"num_ctx": 16384, "temperature": 0.1},
            "stream": False
        }

        res = requests.post(f"{self.base_url}/api/chat", json=req)

        if res.status_code != 200:
            raise RuntimeError(f"Ollama error {res.status_code}: {res.text}")

        content = json.loads(res.text.strip())["message"]["content"]
        messages.append({"role": "assistant", "content": content})

        return base_model.model_validate_json(content)


    def _get_session(self, epic: str, session_type: str, open_position = None) -> list:
        session_id = epic + '-' + session_type
        if session_id not in self.sessions:
            if session_type == 'open':
                self.sessions[session_id] = [
                    {
                        "role": "system",
                        "content": (
                            f"Analyze the following market data for {epic} and determine what type of trade would be best to enter.\n"
                            "Return a confidence for the trade from 1 to 100.\n"
                            "Keep reasoning really short.\n"
                            "Use direction BUY if predicting that the market is going up and direction SELL if predicting the market is going down.\n"
                            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles formatted as a 2D array:\n"
                            " - (timestamp, timeframe (e.g. '1m', '5m', '1h', '1D'), open, high, low, close.\n\n"
                        )
                    }
                ]
            elif session_type == 'close':
                self.sessions[session_id] = [
                    {
                        "role": "system",
                        "content": (
                            f"Analyze the following market data for {epic} and determine if this position should be closed.\n"
                            "Note it's a day trading, so position should rarely be kept overnight and never during weekends.\n"
                            "Try to not make too many trades in a day to minimise costs, so don't close extremely early if not necessary.\n"
                            f"{json.dumps(open_position)}\n"
                            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles:\n"
                        )
                    }
                ]

        return self.sessions[session_id]
