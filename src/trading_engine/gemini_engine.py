import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from trading_engine.abstract_trading_engine import OpenPositionRecommendation, AbstractTradingEngine


class GeminiEngine(AbstractTradingEngine):
    def __init__(self, model: str):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model

    def ask_to_open_a_position(self, data: str) -> OpenPositionRecommendation:
        prompt = (
            "You are an expert algorithmic trading assistant for day trading on IG spread betting.\n"
            "Analyze the following technical snapshot and determine if it is worth entering a trade.\n"
            "Recommend AT MOST one trade: the single best opportunity across all epics provided.\n"
            "If signals are weak, noisy, or conflicting, select HOLD.\n"
            "Market Data is provided as a JSON payload where `ticks` contains multi-timeframe OHLC candles formatted as a 2D array:\n"
            " - (timestamp, timeframe (e.g. '1m', '5m', '1h', '1D'), open, high, low, close.\n\n"
            f"{json.dumps(data)}"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OpenPositionRecommendation,
                temperature=0.1, # Low temperature for deterministic evaluation
            ),
        )

        return response.parsed
