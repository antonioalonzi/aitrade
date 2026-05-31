import logging

from ig_client import IGTradingClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("Main")


NVIDIA = "UC.D.NVDA.DAILY.IP"


if __name__ == "__main__":
    try:
        client = IGTradingClient()
        client.connect()
        epic = NVIDIA
        prices_last_14_days = client.fetch_prices_last_14_days(epic)
        prices_last_3_days = client.fetch_prices_last_3_days(epic)
        prices_last_12_hours = client.fetch_prices_last_12_hours(epic)
        prices_last_1_hour = client.fetch_prices_last_1_hour(epic)
        logger.info(f"Successfully received data from client! ID is: {prices_last_14_days}\n {prices_last_3_days}\n {prices_last_12_hours}\n {prices_last_1_hour}")

    except Exception as e:
        print(f"API Integration Error: {e}")
