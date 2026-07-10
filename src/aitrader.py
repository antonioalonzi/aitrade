import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
from trading_ig.rest import TokenInvalidException

from clients.gemini_client import GeminiClient
from clients.ig_client import IGTradingClient
from storage.storage import Storage
from indicators import indicators


AMAZON = "UA.D.AMZN.DAILY.IP"
AMD = "SA.D.AMD.DAILY.IP"
APPLE = "UA.D.AAPL.DAILY.IP"
META = "UB.D.FB.DAILY.IP"
MICROSOFT = "UC.D.MSFT.DAILY.IP"
NVIDIA = "UC.D.NVDA.DAILY.IP"
PALANTIR = "SE.D.PLTRUS.DAILY.IP"
SMCI = "UD.D.SMCIUS.DAILY.IP"
SPACEX_WE = "IX.D.SUNSPACEX.DAILY.IP"
TESLA = "UD.D.TSLA.DAILY.IP"


logger = logging.getLogger(__name__)

class AiTrader():
    def __init__(self, epics: list[str]):
        self.gemini_client = GeminiClient()
        self.ig_client = IGTradingClient()
        self.storage = Storage()
        self.data = {epic: {} for epic in epics}
        self.balance = 0
        self.percentage_of_balance_to_trade = 0.5

    def run(self):
        if not self._connect_if_required():
            return None

        self.balance = self.ig_client.fetch_account_balance()
        # self.fetch_prices_last_14_days()
        # self.fetch_prices_last_3_days()
        # self.fetch_prices_last_12_hours()
        self.fetch_prices_last_1_hour()

        logger.info(f"Available Balance is: {self.balance}")

        open_epics = [epic for epic in self.data.keys() if self.ig_client.is_market_open(epic)]
        closed_epics = set(self.data.keys()) - set(open_epics)

        if closed_epics:
            logger.info(f"Market is closed for: {', '.join(closed_epics)}")

        open_position = self.ig_client.get_first_open_position()
        if open_position:
            logger.info("An open position already exists. Exiting early.")

        if open_epics:
            ### TODO Test this code then drop it ###
            self.enter_the_market(open_epics[0], 'BUY', 'Manual Trade.')
            return None

            open_epics_data = {epic: self.data[epic] for epic in open_epics}

            tools = [ self.enter_the_market ]
            self.gemini_client.create_chat(tools)

            response = self.gemini_client.ask_to_open_a_position(open_epics_data)

            while True:
                candidate = response.candidates[0]
                part = candidate.content.parts[0]

                if part.function_call:
                    fn_call = part.function_call
                    fn_name = fn_call.name
                    fn_args = dict(fn_call.args)

                    execution_result = self[fn_name](**fn_args)

                    response = self.gemini_client.send_message({
                        "role": "user",
                        "content": [{
                            "function_response": {
                                "name": fn_name,
                                "response": {"result": execution_result}
                            }
                        }]
                    })

                elif part.text:
                    logger.info(f"Final Execution Assessment: {part.text}")
                    break


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

    def _connect_if_required(self):
        if not self.ig_client.is_connected():
            try:
                self.ig_client.connect()
                logger.info("IG client connected successfully.")

            except TokenInvalidException as e:
                logger.error(f"Could not connect to IG: {str(e)}")
                return False

        return True


    def _current_price(self, epic: str):
        prices_df = self.data[epic]['prices_last_1_hour']['prices']
        return prices_df['ask']['Close'].iloc[-1]

    # _calculate_atr was extracted to `src/indicators.py` as `calculate_atr`
    # kept a small compatibility wrapper in the atr module instead of a method
    # to make the calculation reusable and easier to test.




    ### Tools

    def enter_the_market(self, epic: str, direction: str, comment: str):
        """
        Decided if entering the market and open a position, close it, edit it or hold.

        Args:
            epic: the epic to open the position for
            direction: BUY or SELL
            comment: a short reason for why opening that position
        """
        logger.info(f"enter_the_market(epic={epic}, direction={direction}, comment={comment})")

        margin_rate = 0.2
        current_price = self._current_price(epic)
        atr = indicators.atr(self.data[epic]['prices_last_14_days']['prices'])
        stop_distance = atr * 2.5
        limit_distance = stop_distance * 2.0
        size = (self.balance * self.percentage_of_balance_to_trade) / (current_price * margin_rate)
        amount = current_price * size
        logger.info(f"enter_the_market calculated: current_price={current_price}, atr={atr}, stop_distance={stop_distance}, limit_distance={limit_distance}, size={size}, amount={amount}")

        response = self.ig_client.open_position(epic, direction, stop_distance, limit_distance)
        logger.info(response)
        self.storage.save_open_trade('foo', epic, amount, datetime.now(timezone.utc).isoformat(), current_price, comment)




def run_trader():
    scheduler = BackgroundScheduler()
    ai_trader = AiTrader([AMD, NVIDIA, SPACEX_WE])

    # this is for quick debug and not wanting to wait for the scheduler.
    ai_trader.run()
    return

    scheduler.add_job(ai_trader.fetch_prices_last_14_days, CronTrigger.from_crontab("0 03 * * *"))
    scheduler.add_job(ai_trader.fetch_prices_last_3_days, CronTrigger.from_crontab("0 03 * * *"))
    scheduler.add_job(ai_trader.fetch_prices_last_12_hours, CronTrigger.from_crontab("*/15 * * * *"))
    scheduler.add_job(ai_trader.fetch_prices_last_1_hour, CronTrigger.from_crontab("* * * * *"))

    scheduler.add_job(ai_trader.run, CronTrigger.from_crontab("* * * * *"))

    scheduler.start()
