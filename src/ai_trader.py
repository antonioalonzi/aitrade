import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from clients.gemini_client import GeminiClient
from clients.ig_trading_client import IGTradingClient
from trading_utils import trading_utils
from market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from market_data.market_data_listener import MarketDataListener
from market_data.market_data_repository import MarketDataRepository
from trade.trade import Trade
from trade.trade_repository import TradeRepository

logger = logging.getLogger(__name__)

class AiTrader:
    def __init__(
            self,
            gemini_client: GeminiClient,
            ig_trading_client: IGTradingClient,
            trade_repository: TradeRepository,
            market_data_repository: MarketDataRepository,
            market_data_in_memory_info: MarketDataInMemoryInfo,
            market_data_listener: MarketDataListener,
            epics: list[str]
    ):
        self.gemini_client = gemini_client
        self.ig_trading_client = ig_trading_client
        self.trade_repository = trade_repository
        self.market_data_repository = market_data_repository
        self.market_data_in_memory_info = market_data_in_memory_info
        self.market_data_listener = market_data_listener
        self.epics = epics
        self.balance = 0
        self.percentage_of_balance_to_trade = 0.5

    def run(self):
        if not self._connect_if_required():
            return

        self.balance = self.ig_trading_client.fetch_account_balance()
        logger.info(f"Available Balance is: {self.balance}")

        open_position = self.ig_trading_client.get_first_open_position()
        if open_position:
            logger.info(f"An open position already exists {open_position}. Exiting early.")
            return

        self.enter_the_market(self.epics[0], "BUY", 'Manual')
        return

        # else:
        #     ai_query = self._build_ai_query()
        #     tools = [ self.enter_the_market ]
        #     self.gemini_client.create_chat(tools)
        #
        #     response = self.gemini_client.ask_to_open_a_position(ai_query)
        #
        #     while True:
        #         candidate = response.candidates[0]
        #         part = candidate.content.parts[0]
        #
        #         if part.function_call:
        #             fn_call = part.function_call
        #             fn_name = fn_call.name
        #             fn_args = dict(fn_call.args)
        #
        #             execution_result = self[fn_name](**fn_args)
        #
        #             response = self.gemini_client.send_message({
        #                 "role": "user",
        #                 "content": [{
        #                     "function_response": {
        #                         "name": fn_name,
        #                         "response": {"result": execution_result}
        #                     }
        #                 }]
        #             })
        #
        #         elif part.text:
        #             logger.info(f"Final Execution Assessment: {part.text}")
        #             break

    def _connect_if_required(self):
        if not self.ig_trading_client.is_connected():
            try:
                self.ig_trading_client.connect()
                logger.info("IG client connected successfully.")

            except Exception as e:
                logger.error(f"Could not connect to IG: {str(e)}")
                return False

        return True

    def _build_ai_query(self) -> str:
        ai_query = ""
        for epic in self.epics:
            epic_data = self.market_data_repository.get_latest_market_data(epic)
            if not epic_data.empty:
                avg_epic_data = trading_utils.avg_bid_offer(epic_data)
                ai_query += (
                    f"### {epic} ###\n"
                    f"{trading_utils.aggregate_for_ai(avg_epic_data)}\n\n"
                    f"----------------------------------\n\n"
                )
        return ai_query




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

        current_price = self.market_data_in_memory_info.get_current_price(epic)
        if not current_price:
            logger.warning(f"Could not get current price for epic={epic}. Exiting early.")
            return

        market_data = self.market_data_repository.get_latest_market_data(epic)
        if market_data.empty:
            logger.warning(f"No market data available for epic={epic}. Exiting early.")
            return

        margin_rate = 0.2
        avg_market_data = trading_utils.avg_bid_offer(market_data)
        atr = trading_utils.atr(avg_market_data, 14)
        stop_distance = atr * 2.5
        limit_distance = stop_distance * 2.0
        size = (self.balance * self.percentage_of_balance_to_trade) / (current_price * margin_rate)
        amount = current_price * size
        logger.info(f"enter_the_market calculated: current_price={current_price}, atr={atr}, stop_distance={stop_distance}, limit_distance={limit_distance}, size={size}, amount={amount}")

        response = self.ig_trading_client.open_position(epic, direction, stop_distance, limit_distance)
        logger.info(response)
        trade = Trade(id="foo", epic=epic, amount=amount, opened_at=datetime.now(timezone.utc).isoformat(), open_price=current_price, comment=comment)
        self.trade_repository.insert_trade(trade)




def run_trader(
        gemini_client: GeminiClient,
        ig_client: IGTradingClient,
        trade_repository: TradeRepository,
        market_data_repository: MarketDataRepository,
        market_data_in_memory_info: MarketDataInMemoryInfo,
        market_data_listener: MarketDataListener,
        epics: list[str]
):
    ai_trader = AiTrader(gemini_client, ig_client, trade_repository, market_data_repository, market_data_in_memory_info, market_data_listener, epics)

    scheduler = BackgroundScheduler()
    scheduler.add_job(ai_trader.run, CronTrigger.from_crontab("* * * * *"))
    scheduler.start()
