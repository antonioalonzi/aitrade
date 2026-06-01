import os
import logging

from dotenv import load_dotenv
from google import genai

logger = logging.getLogger("GeminiClient")

class GeminiClient:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def test(self):
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Explain the concept of algorithmic trading in one sentence.'
        )

        logger.info("Response from Gemini:")
        logger.info(response.text)
