import logging
import json

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from clients.gemini_client import GeminiClient
from clients.ig_client import IGTradingClient
from storage.storage import Storage


AMAZON = "UA.D.AMZN.DAILY.IP"
AMD = "SA.D.AMD.DAILY.IP"
APPLE = "UA.D.AAPL.DAILY.IP"
META = "UB.D.FB.DAILY.IP"
MICROSOFT = "UC.D.MSFT.DAILY.IP"
NVIDIA = "UC.D.NVDA.DAILY.IP"
PALANTIR = "SE.D.PLTRUS.DAILY.IP"
SMCI = "UD.D.SMCIUS.DAILY.IP"
TESLA = "UD.D.TSLA.DAILY.IP"


logger = logging.getLogger("AiTrader")

class AiTrader():
    def __init__(self, epics: list[str]):
        self.gemini_client = GeminiClient()
        self.ig_client = IGTradingClient()
        self.ig_client.connect()
        self.storage = Storage()
        self.data = {epic: {} for epic in epics}

    def run(self):
        open_epics = [epic for epic in self.data.keys() if self.ig_client.is_market_open(epic)]
        closed_epics = set(self.data.keys()) - set(open_epics)

        if closed_epics:
            logger.info(f"Market is closed for: {', '.join(closed_epics)}")

        if open_epics:
            open_epics_data = {epic: self.data[epic] for epic in open_epics}
            response = self.gemini_client.decide_if_open_a_position(open_epics_data)
            json_body = response[response.find('{') : response.rfind('}') + 1]
            decision = json.loads(json_body)
            println(decision)

    def fetch_prices_last_14_days(self):
        for epic in self.data:
            self.data[epic]['prices_last_14_days'] = self.ig_client.fetch_prices_last_14_days(epic)

    def fetch_prices_last_3_days(self):
        for epic in self.data:
            self.data[epic]['prices_last_3_days'] = self.ig_client.fetch_prices_last_3_days(epic)

    def fetch_prices_last_12_hours(self):
        for epic in self.data:
            self.data[epic]['prices_last_12_hours'] = self.ig_client.fetch_prices_last_12_hours(epic)

    def fetch_prices_last_1_hour(self):
        for epic in self.data:
            self.data[epic]['prices_last_1_hour'] = self.ig_client.fetch_prices_last_1_hour(epic)


def run_trader():
    scheduler = BackgroundScheduler()
    ai_trader = AiTrader([AMD, NVIDIA])

    ai_trader.fetch_prices_last_14_days()
    ai_trader.fetch_prices_last_3_days()
    ai_trader.fetch_prices_last_12_hours()
    ai_trader.fetch_prices_last_1_hour()

    # this is for quick debug and not wanting to wait for the scheduler.
    ai_trader.run()

    scheduler.add_job(ai_trader.fetch_prices_last_14_days, CronTrigger.from_crontab("0 03 * * 1-5"))
    scheduler.add_job(ai_trader.fetch_prices_last_3_days, CronTrigger.from_crontab("0 03 * * 1-5"))
    scheduler.add_job(ai_trader.fetch_prices_last_12_hours, CronTrigger.from_crontab("*/15 * * * 1-5"))
    scheduler.add_job(ai_trader.fetch_prices_last_1_hour, CronTrigger.from_crontab("* * * * 1-5"))

    scheduler.add_job(ai_trader.run, CronTrigger.from_crontab("* * * * 1-5"))

    scheduler.start()
