import os

from dotenv import load_dotenv
from google import genai

class GeminiClient:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat = None

    def create_chat(self, tools: list):
        self.chat = self.client.chats.create(
            #model = 'gemini-2.5-flash',
            model ='gemini-2.5-flash-lite',
            config = {'tools': tools}
        )

    def ask_to_open_a_position(self, data: str) -> bool:
        message = (
            "You are an expert algorithmic trading assistant for day trading trading on spread betting in IG.\n"
            "I would like to open a position and close it within few hours or a day (rarely keep it open overnight).\n"
            "Analyze the following technical data and check if it is worth to open a position on any of the epics underneath.\n"
            "Recommend only one trade, the best of all the options.\n"
            "Use the tools.\n"
            f"{data}"
        )
        return self.chat.send_message(message)

    def send_message(self, message: str):
        return self.chat.send_message(message)

