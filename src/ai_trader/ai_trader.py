import logging
from datetime import datetime, timezone

from ai_trader.trading_engine.abstract_trading_engine import AbstractTradingEngine
from ai_trader.trade.trade import TradeDirection
from ai_trader.trading_platform.ig_trading_client import IGTradingClient
from ai_trader.trading_utils import trading_utils
from ai_data_downloader.market_data.market_data_in_memory_info import MarketDataInMemoryInfo
from ai_data_downloader.market_data.market_data_listener import MarketDataListener
from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade
from ai_trader.trade.trade_repository import TradeRepository

logger = logging.getLogger(__name__)

class AiTrader:
    def __init__(
            self,
            trading_engine: AbstractTradingEngine,
            ig_trading_client: IGTradingClient,
            trade_repository: TradeRepository,
            market_data_repository: MarketDataRepository,
            market_data_in_memory_info: MarketDataInMemoryInfo,
            market_data_listener: MarketDataListener,
            epics: list[str]
    ):
        self.trading_engine = trading_engine
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

        # todo do not call engine if not tradable

        if open_position:
            prompt_ai_data = self._build_prompt_ai_market_data([open_position['epic']])
            # logger.info(f"Trading Engine: ask_to_close_a_position -> {json.dumps(prompt_ai_data)}")
            should_close = self.trading_engine.ask_to_close_a_position(prompt_ai_data)
            # logger.info(f"Trading Engine: ask_to_close_a_position <- should_close: {should_close}")
            if should_close:
                self._exit_the_market(open_position)

        else:
            prompt_ai_data = self._build_prompt_ai_market_data(self.epics)
            # logger.info(f"Trading Engine: ask_to_open_a_position -> {json.dumps(prompt_ai_data)}")
            trading_recommendation = self.trading_engine.ask_to_open_a_position(prompt_ai_data)
            # logger.info(f"Trading Engine: ask_to_open_a_position <-: {trading_recommendation}")
            if trading_recommendation.direction != TradeDirection.HOLD:
                self._enter_the_market(trading_recommendation.epic, trading_recommendation.direction, trading_recommendation.reasoning)


    def _connect_if_required(self):
        if not self.ig_trading_client.is_connected():
            try:
                self.ig_trading_client.connect()
                logger.info("IG client connected successfully.")

            except Exception as e:
                logger.error(f"Could not connect to IG: {str(e)}")
                return False

        return True

    def _build_prompt_ai_market_data(self, epics: list) -> dict:
        ai_data = {}

        for epic in epics:
            epic_data = self.market_data_repository.get_latest_market_data(epic)
            if not epic_data.empty:
                avg_epic_data = trading_utils.avg_bid_offer(epic_data)
                atr = trading_utils.atr(avg_epic_data, 14)
                ticks = trading_utils.aggregate_for_ai(avg_epic_data)

                ai_data[epic] = {
                    "ticks": ticks,
                    "oscillators": {
                        "atr": atr
                    }
                }

        return ai_data

    def _enter_the_market(self, epic: str, direction: TradeDirection, comment: str):
        logger.info(f"enter_the_market(epic={epic}, direction={direction}, comment={comment})")

        current_price = self.market_data_in_memory_info.get_current_avg_price(epic)
        if not current_price:
            logger.warning(f"Could not get current price for epic={epic}. Exiting early.")
            return

        market_data = self.market_data_repository.get_latest_market_data(epic)
        if market_data.empty:
            logger.warning(f"No market data available for epic={epic}. Exiting early.")
            return

        margin_rate = 0.2 # hold 20% of the total position value in available margin
        avg_market_data = trading_utils.avg_bid_offer(market_data)
        atr = trading_utils.atr(avg_market_data, 14) # 14 days atr (volatility)
        stop_distance = atr * 2.5 # 2.5 times the ATR for stop loss
        limit_distance = stop_distance * 2.0 # 2 times the ATR for stop distance
        size = round((self.balance * self.percentage_of_balance_to_trade) / (current_price * margin_rate), 2)
        amount = current_price * size
        logger.info(f"enter_the_market calculated: current_price={current_price}, atr={atr}, stop_distance={stop_distance}, limit_distance={limit_distance}, size={size}, amount={amount}")

        response = self.ig_trading_client.open_position(epic, direction, size, stop_distance, limit_distance)
        logger.info(f"Opened position: {response}")
        trade = Trade(id=response.get('dealId'), epic=epic, amount=amount, direction=direction, size=size, opened_at=datetime.now(timezone.utc).isoformat(), open_price=response.get('level'), comment=comment)
        self.trade_repository.insert_trade(trade)

    def _exit_the_market(self, position):
        logger.info(f"exit_the_market(position={position})")

        close_direction = TradeDirection.SELL if position['direction'] == TradeDirection.BUY else TradeDirection.BUY
        response = self.ig_trading_client.close_position(position['dealId'], close_direction, position['epic'], position['size'])
        logger.info(f"Closed position: {response}")

        self.trade_repository.close_trade(position['dealId'], datetime.now(timezone.utc).isoformat(), response['level'], response['profit'])
