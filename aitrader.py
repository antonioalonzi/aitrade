import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from clients.gemini_client import GeminiClient
from clients.ig_client import IGTradingClient

CRON_EXPRESSION = "2/5 * * * *"

NVIDIA = "UC.D.NVDA.DAILY.IP"

logger = logging.getLogger("AiTrader")

class AiTrader():
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.ig_client = IGTradingClient()
        self.ig_client.connect()

    def run(self):
        if not self.gemini_client.is_market_open():
            logger.info("The US Stock Market is Closed.")
            return

        logger.info("The US Stock Market is Open.")

    def download_data(self):
        epic = NVIDIA
        prices_last_14_days = self.ig_client.fetch_prices_last_14_days(epic)
        prices_last_3_days = self.ig_client.fetch_prices_last_3_days(epic)
        prices_last_12_hours = self.ig_client.fetch_prices_last_12_hours(epic)
        prices_last_1_hour = self.ig_client.fetch_prices_last_1_hour(epic)
        logger.info(f"Successfully received data from ig_client! ID is: {prices_last_14_days}\n {prices_last_3_days}\n {prices_last_12_hours}\n {prices_last_1_hour}")

def run_trader():
    scheduler = BackgroundScheduler()
    ai_trader = AiTrader()
    ai_trader.run()
    scheduler.add_job(ai_trader.run, CronTrigger.from_crontab(CRON_EXPRESSION))
    scheduler.start()
