import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("AiTrader")

class AiTrader():
    def run(self):
        logger.info("Running")


def run_trader():
    scheduler = BackgroundScheduler()
    ai_trader = AiTrader()
    scheduler.add_job(ai_trader.run, 'interval', minutes=1)
    scheduler.start()
