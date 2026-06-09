import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from clients.gemini_client import GeminiClient
from clients.ig_client import IGTradingClient

CRON_EXPRESSION = "* * * * *"


AMAZON = "UA.D.AMZN.DAILY.IP"
AMD = "SA.D.AMD.DAILY.IP"
APPLE = "UA.D.AAPL.DAILY.IP"
META = "UB.D.FB.DAILY.IP"
MICROSOFT = "UC.D.MSFT.DAILY.IP"
NVIDIA = "UC.D.NVDA.DAILY.IP"
PALANTIR = "SE.D.PLTRUS.DAILY.IP"
SMCI = "UD.D.SMCIUS.DAILY.IP"
TESLA = "UD.D.TSLA.DAILY.IP"

EPICS = [AMD, NVIDIA]


logger = logging.getLogger("AiTrader")

class AiTrader():
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.ig_client = IGTradingClient()
        self.ig_client.connect()

    def run(self):
        open_epics = [epic for epic in EPICS if self.ig_client.is_market_open(epic)]
        closed_epics = set(EPICS) - set(open_epics)

        if closed_epics:
            logger.info(f"Market is closed for: {', '.join(closed_epics)}")

        if open_epics:
            combined_data = "\n".join(f"[{epic}]\n{self.download_data(epic)}" for epic in open_epics)
            response = self.gemini_client.decide_if_open_a_position(combined_data)


    def download_data(self, epic):
        prices_last_14_days = self.ig_client.fetch_prices_last_14_days(epic)
        prices_last_3_days = self.ig_client.fetch_prices_last_3_days(epic)
        prices_last_12_hours = self.ig_client.fetch_prices_last_12_hours(epic)
        prices_last_1_hour = self.ig_client.fetch_prices_last_1_hour(epic)
        return (
            f"--- DATA FOR EPIC = {epic} ---\n"
            f"${prices_last_14_days}\n\n"
            f"${prices_last_3_days}\n\n"
            f"${prices_last_12_hours}\n\n"
            f"${prices_last_1_hour}\n\n"
        )

def run_trader():
    scheduler = BackgroundScheduler()
    ai_trader = AiTrader()
    ai_trader.run()
    scheduler.add_job(ai_trader.run, CronTrigger.from_crontab(CRON_EXPRESSION))
    scheduler.start()
