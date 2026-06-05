import os
import logging

from datetime import datetime
from dotenv import load_dotenv
from google import genai

logger = logging.getLogger("GeminiClient")

class GeminiClient:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def is_market_open(self, instrument: str) -> bool:
        answer = self._ask(f"Is market open right now for {instrument}? Answer Yes or No")
        return answer == "Yes"

    def _ask(self, question: str) -> str:
        full_question = self._temporal_location_context() + question
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_question
        )
        logger.info(f"{full_question} -> {response.text}")
        return response.text

    def _temporal_location_context(self) -> str:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return "London " + current_time_str + ": "
