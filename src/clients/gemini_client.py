import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from trade.trade import TradeDirection


class OpenPositionRecommendation(BaseModel):
    epic: str = Field(description="The epic identifier of the recommended trade, or 'NONE' if holding.")
    direction: TradeDirection = Field(description="BUY, SELL, or HOLD.")
    reasoning: str = Field(description="Brief technical rationale for the decision.")

class GeminiClient:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # self.model = 'gemini-2.5-flash'
        self.model = "gemini-2.5-flash-lite"

    def ask_to_open_a_position(self, data: str) -> OpenPositionRecommendation:
        prompt = (
            "You are an expert algorithmic trading assistant for day trading on IG spread betting.\n"
            "Analyze the following technical snapshot and determine if it is worth entering a trade.\n"
            "Recommend AT MOST one trade—the single best opportunity across all epics provided.\n"
            "If signals are weak, noisy, or conflicting, select HOLD.\n\n"
            f"Market Snapshot Data:\n{data}"
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
