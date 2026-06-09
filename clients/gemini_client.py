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

    def decide_if_open_a_position(self, data: str) -> bool:
        question = (
            "You are a day trader who would like to open a position and close it within few hours or a day (rarely keep it open overnight).\n"
            "Check if it is worth to open a position on any of the epics underneath.\n"
            "Respond with a json format like: \n\n"
            '''{
                "action": string, // "OPEN" or "NOT_YET", if OPEN then other fields will be populated, if NOT_YET no other fields will be populated
                "epic": string,   // the epic chosen
                "stop_distance": float,  // the stop distance using to close the position. It will be a Trailing Stop.
                "limit_distance": float, // the limit distance for the profic
                "reason": string // "a short explaination about the decision
            }\n\n'''
            f"{data}"
        )
        return self._ask(question)

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
