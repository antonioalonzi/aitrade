import logging

from etoro_client import EToroClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("Main")


if __name__ == "__main__":
    try:
        client = EToroClient()
        ticker = "BTC"
        logger.info(f"Triggering workflow for {ticker}...")
        instrument_id = client.get_instrument_id(ticker)
        logger.info(f"Successfully received data from client! ID is: {instrument_id}")

    except Exception as e:
        print(f"API Integration Error: {e}")
