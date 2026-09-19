import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from ai_trader.trading_engine.abstract_trading_engine import OpenPositionRecommendation, AbstractTradingEngine


class OpenAIEngine(AbstractTradingEngine):
    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        load_dotenv()
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def ask_to_open_a_position(self, data: str) -> OpenPositionRecommendation:
        prompt = (
            "Analyze the following technical snapshot and determine if it is worth entering a trade.\n"
            "Recommend AT MOST one trade: the single best opportunity across all epics provided.\n"
            "If signals are weak, noisy, or conflicting, select HOLD.\n"
            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles formatted as a 2D array:\n"
            " - (timestamp, timeframe (e.g. '1m', '5m', '1h', '1D'), open, high, low, close.\n\n"
            f"{json.dumps(data)}"
        )

        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert algorithmic trading assistant for day trading on IG spread betting."
                },
                {"role": "user", "content": prompt}
            ],
            response_format=OpenPositionRecommendation,
            temperature=0.1,
        )

        return completion.choices[0].message.parsed
