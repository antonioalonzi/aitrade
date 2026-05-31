import logging

from ig_client import IGTradingClient
from gemini_client import GeminiClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("Main")


NVIDIA = "UC.D.NVDA.DAILY.IP"


if __name__ == "__main__":
    try:
        geminiClient = GeminiClient()
        geminiClient.test()

        igClient = IGTradingClient()
        igClient.connect()

        epic = NVIDIA
        prices_last_14_days = igClient.fetch_prices_last_14_days(epic)
        prices_last_3_days = igClient.fetch_prices_last_3_days(epic)
        prices_last_12_hours = igClient.fetch_prices_last_12_hours(epic)
        prices_last_1_hour = igClient.fetch_prices_last_1_hour(epic)
        logger.info(f"Successfully received data from igClient! ID is: {prices_last_14_days}\n {prices_last_3_days}\n {prices_last_12_hours}\n {prices_last_1_hour}")

    except Exception as e:
        print(f"API Integration Error: {e}")
