import uuid
import logging
import os
import requests

from dotenv import load_dotenv


logger = logging.getLogger("eToroClient")

class EToroClient:
    def __init__(self):
        load_dotenv()
        self.base_url = "https://public-api.etoro.com/api/v1"
        self.headers = {
            "x-api-key": os.getenv("ETORO_API_KEY"),
            "x-user-key": os.getenv("ETORO_USER_KEY"),
            "Content-Type": "application/json"
        }

    def _get_headers(self) -> dict:
        """Generates a fresh request dictionary tracking a unique UUID."""
        req_headers = self.headers.copy()
        req_headers["x-request-id"] = str(uuid.uuid4())
        return req_headers

    def get_instrument_id(self, ticker: str) -> int:
        """Resolves a ticker string into eToro's internal numeric ID."""
        url = f"{self.base_url}/market-data/search"
        headers = self._get_headers()

        logger.info(f"Searching ID for ticker: '{ticker}' [UUID: {headers['x-request-id']}]")
        response = requests.get(url, headers=headers, params={"internalSymbolFull": ticker})
        response.raise_for_status()
        return response.json().get("InstrumentID")
