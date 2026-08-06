import logging

from ai_data_downloader import run_data_downloader
from ai_trader import run_trader
from http_server.http_server import run_http_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


AMAZON = "SE.D.AMZN.DAILY.IP"
AMD = "SE.D.AMD.DAILY.IP"
APPLE = "SE.D.AAPL.DAILY.IP"
META = "SE.D.FB.DAILY.IP"
MICROSOFT = "SE.D.MSFT.DAILY.IP"
NVIDIA = "SE.D.NVDA.DAILY.IP"
PALANTIR = "SE.D.PLTRUS.DAILY.IP"
SMCI = "SE.D.SMCIUS.DAILY.IP"
TESLA = "SE.D.TSLA.DAILY.IP"


if __name__ == "__main__":
    run_data_downloader([NVIDIA])
    # run_trader([NVIDIA])
    run_http_server()
