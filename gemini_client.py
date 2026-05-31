import os
from dotenv import load_dotenv
from google import genai


class GeminiClient:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def test(self):
        print("Sending request to Gemini...")
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Explain the concept of algorithmic trading in one sentence.'
        )

        print("\nResponse from Gemini:")
        print(response.text)
