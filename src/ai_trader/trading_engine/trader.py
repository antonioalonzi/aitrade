from datetime import datetime, timezone
import time
import json
import logging

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade, TradeDirection
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_engine.openai_engine import OpenAIEngine, OpenPositionRecommendation
from ai_trader.trading_platform.ig_trading_client import IGTradingClient
from ai_trader.trading_utils import trading_utils, trading_indicators

logger = logging.getLogger(__name__)

class Trader:
    def __init__(
            self,
            trading_engine: OpenAIEngine,
            ig_trading_client: IGTradingClient,
            trade_repository: TradeRepository,
            market_data_repository: MarketDataRepository,
            confidence_threshold: int,
            epics: list[str]
    ):
        self.trading_engine = trading_engine
        self.ig_trading_client = ig_trading_client
        self.trade_repository = trade_repository
        self.market_data_repository = market_data_repository
        self.confidence_threshold = confidence_threshold
        self.epics = epics
        self.balance = 0
        self.percentage_of_balance_to_trade = 0.5
        self.chat_history = 0

    def run(self):
        if self.chat_history == 60:
            self.chat_history = 0
            self.trading_engine.forget_sessions()
            logging.info('Resetting all openai chats.')

        if not self._connect_if_required():
            return

        self.balance = self.ig_trading_client.fetch_account_balance()
        logger.info(f"Available Balance is: {self.balance}")

        open_position = self.ig_trading_client.get_first_open_position()

        # wait 5 secs to make sure the data has been downloaded for this minute
        time.sleep(5)

        if open_position:
            last_ticks = self.market_data_repository.get_last_ticks([open_position['epic']])
            tradable_epics = last_ticks.loc[last_ticks['market_state'] == 'T', 'epic'].tolist()
            if tradable_epics:
                prompt_type = 'initial' if self.chat_history == 0 else 'increment'
                prompt_ai_market_data = self._build_prompt_ai_market_data(open_position['epic'], prompt_type)
                if prompt_ai_market_data:
                    start = time.perf_counter()
                    should_close = self.trading_engine.ask_to_close_a_position(open_position['epic'], open_position, prompt_ai_market_data).should_close
                    end = time.perf_counter()
                    logger.info(f"Trading Engine: ask_to_close_a_position <- should_close: {should_close} (Time taken: {end - start:.2f} seconds; Prompt Length: {len(json.dumps(prompt_ai_market_data))})")
                    if should_close:
                        self._exit_the_market(open_position)

        else:
            last_ticks = self.market_data_repository.get_last_ticks(self.epics)
            tradable_epics = last_ticks.loc[last_ticks['market_state'] == 'T', 'epic'].tolist()
            trading_recommendations = []
            for epic_item in tradable_epics:
                epic: str = str(epic_item)

                prompt_type = 'initial' if self.chat_history == 0 else 'increment'
                prompt_ai_market_data = self._build_prompt_ai_market_data(epic, prompt_type)

                if prompt_ai_market_data:
                    start = time.perf_counter()
                    trading_recommendation = self.trading_engine.ask_to_open_a_position(epic, prompt_ai_market_data)
                    end = time.perf_counter()
                    logger.info(f"Trading Engine: ask_to_open_a_position({epic}) <-: {trading_recommendation} (Time taken: {end - start:.2f} seconds; Prompt Length: {len(json.dumps(prompt_ai_market_data))})")
                    trading_recommendations.append({"epic": epic, "recommendation": trading_recommendation})

            if trading_recommendations:
                sorted_trading_recommendations = sorted(
                    trading_recommendations,
                    key=lambda item: item['recommendation'].confidence,
                    reverse=True
                )

                best_trading_recommendation = sorted_trading_recommendations[0]
                if best_trading_recommendation['recommendation'].confidence >= self.confidence_threshold:
                    self._enter_the_market(best_trading_recommendation['epic'], best_trading_recommendation['recommendation'])

        self.chat_history = self.chat_history + 1


    def _connect_if_required(self):
        if not self.ig_trading_client.is_connected():
            try:
                self.ig_trading_client.connect()
                logger.info("IG client connected successfully.")

            except Exception as e:
                logger.error(f"Could not connect to IG: {str(e)}")
                return False

        return True

    def _build_prompt_ai_market_data(self, epic: str, prompt_type: str) -> dict | None:
        epic_data = self.market_data_repository.get_latest_market_data(epic)
        if not epic_data.empty:
            avg_epic_data = trading_utils.avg_bid_offer(epic_data)
            ticks = trading_utils.aggregate_for_ai(avg_epic_data) if prompt_type == 'initial' else epic_data.iloc[-1].to_dict()

            return {
                "ticks": ticks,
                "oscillators": {
                    "atr": trading_indicators.atr(avg_epic_data, 14),
                    "rsi": trading_indicators.rsi(avg_epic_data, 14)
                }
            }

        return None

    def _enter_the_market(self, epic: str, recommendation: OpenPositionRecommendation):
        logger.info(f"enter_the_market(epic={epic}, recommendation={recommendation})")

        market_data = self.market_data_repository.get_latest_market_data(epic)
        if market_data.empty:
            logger.warning(f"No market data available for epic={epic}. Exiting early.")
            return
        current_price = (market_data.iloc[0]['bid_close'] + market_data.iloc[0]['offer_close']) / 2

        margin_rate = 0.2 # hold 20% of the total position value in available margin
        stop_distance = current_price * 0.05
        limit_distance = current_price * 0.10
        size = round((self.balance * self.percentage_of_balance_to_trade) / (current_price * margin_rate), 2)
        amount = current_price * size
        logger.info(f"enter_the_market calculated: current_price={current_price}, stop_distance={stop_distance}, limit_distance={limit_distance}, size={size}, amount={amount}")

        response = self.ig_trading_client.open_position(epic, recommendation.direction, size, stop_distance, limit_distance)
        logger.info(f"Opened position: {response}")
        trade = Trade(id=response.get('dealId'), epic=epic, amount=amount, direction=recommendation.direction, confidence=recommendation.confidence, size=size,
                      opened_at=datetime.now(timezone.utc).isoformat(), open_price=response.get('level'), comment=recommendation.reasoning, balance_at_opening=self.balance)
        self.trade_repository.insert_trade(trade)

    def _exit_the_market(self, position):
        logger.info(f"exit_the_market(position={position})")

        close_direction = TradeDirection.SELL if position['direction'] == TradeDirection.BUY else TradeDirection.BUY
        response = self.ig_trading_client.close_position(position['dealId'], close_direction, position['epic'], position['size'])
        logger.info(f"Closed position: {response}")

        self.trade_repository.close_trade(position['dealId'], datetime.now(timezone.utc).isoformat(), response['level'], response['profit'])