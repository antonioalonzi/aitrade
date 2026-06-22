import logging

from server.http_server import run_http_server
from aitrader import run_trader


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    #run_trader()
    run_http_server()

