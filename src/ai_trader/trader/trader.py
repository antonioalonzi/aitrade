from datetime import datetime, timezone, timedelta
import time
import logging
import pandas as pd

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade, TradeDirection
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_strategy.openai_client import OpenPositionRecommendation, CloseDecision
from ai_trader.trading_strategy.strategy import CloseStrategy, OpenStrategy
from ai_trader.trading_platform.ig_trading_client import IGTradingClient
from ai_trader.trading_utils.market_times import only_open_epics, is_epic_open

logger = logging.getLogger(__name__)

class Trader:
    def __init__(
            self,
            ai_open_strategy: OpenStrategy,
            ai_close_strategy: CloseStrategy,
            ig_trading_client: IGTradingClient,
            trade_repository: TradeRepository,
            market_data_repository: MarketDataRepository,
            config: dict
    ):
        self.ai_open_strategy = ai_open_strategy
        self.ai_close_strategy = ai_close_strategy
        self.ig_trading_client = ig_trading_client
        self.trade_repository = trade_repository
        self.market_data_repository = market_data_repository
        self.config = config
        self.backtest_datetime = None

    def run(self):
        if not self._connect_if_required():
            return

        open_position = self.ig_trading_client.get_first_open_position()

        # wait 5 secs to make sure the data has been downloaded for this minute
        time.sleep(5)

        self._execute_trade_decision(open_position)


    def _execute_trade_decision(self, open_position):
        if open_position:
            if self._now().minute % self.config['evaluate_exit_the_market_interval_in_minutes'] > 0:
                return

            logger.info(f"Evaluating exit for open position: {open_position['dealId']}, {open_position['epic']}")

            tradable_epics = self._get_tradable_epics('close')

            if open_position['epic'] in tradable_epics:
                open_trade = self.trade_repository.get_trade_by_id(open_position['dealId'])
                if open_trade:
                    if not is_epic_open(open_position['epic'], self._now() + timedelta(minutes=5)):
                        logger.info(f"5 minutes before end of market and position {open_position['dealId']} is still open. Forcing a close.")
                        close_recommendation = CloseDecision(should_close=True, reasoning='5 minutes before end of market and position is still open. Forcing a close.')
                    else:
                        close_recommendation = self.ai_close_strategy.evaluate(self._now(), self.config, open_position, open_trade)

                    if close_recommendation.should_close:
                        self._exit_the_market(open_position, close_recommendation.reasoning or '-')

        else:
            if self._now().minute % self.config['evaluate_enter_the_market_interval_in_minutes'] > 0:
                return

            logger.info(f"Evaluating entering the market for epics: {self.config['epics']}")

            tradable_epics = self._get_tradable_epics('open')
            trading_recommendations = []

            for epic in tradable_epics:
                trading_recommendation = self.ai_open_strategy.evaluate(self._now(), epic)
                if trading_recommendation and trading_recommendation.direction != TradeDirection.NONE:
                    trading_recommendations.append({"epic": epic, "recommendation": trading_recommendation})

            if trading_recommendations:
                sorted_trading_recommendations = sorted(
                    trading_recommendations,
                    key=lambda item: item['recommendation'].confidence,
                    reverse=True
                )

                best_trading_recommendation = sorted_trading_recommendations[0]
                if best_trading_recommendation['recommendation'].confidence >= self.config['confidence_threshold']:
                    self._enter_the_market(best_trading_recommendation['epic'], best_trading_recommendation['recommendation'])


    def _connect_if_required(self):
        if not self.ig_trading_client.is_connected():
            try:
                self.ig_trading_client.connect()
                logger.info("IG client connected successfully.")

            except Exception as e:
                logger.error(f"Could not connect to IG: {str(e)}")
                return False

        return True

    def _get_tradable_epics(self, trade_type: str) -> list:
        oldest_allowed_time = self._now() - timedelta(minutes=5)
        last_ticks = self.market_data_repository.get_last_ticks(self.config['epics'])
        tradable_epics = []

        for epic in self.config['epics']:
            epic_str = str(epic)
            epic_row = last_ticks[last_ticks['epic'].astype(str) == epic_str]
            
            if epic_row.empty:
                logger.info(f"Epic {epic_str} excluded: No tick data found.")
                continue
                
            row = epic_row.iloc[0]
            
            tick_time = pd.to_datetime(row['datetime'], utc=True)
            if tick_time < oldest_allowed_time:
                logger.warning(f"Epic {epic_str} excluded: Last tick is stale ({row['datetime']}).")
                continue
            
            if row['market_state'] not in ['DEAL']:
                # logger.info(f"Epic {epic_str} excluded: Market state is '{row['market_state']}' (required: 'DEAL').")
                continue
                
            tradable_epics.append(epic_str)

        now = self._now()
        open_now = only_open_epics(tradable_epics, now)
        # for epic in set(tradable_epics) - set(open_now):
            # logger.info(f"Epic {epic} excluded: Market is closed right now.")
        tradable_epics = open_now

        if trade_type == 'close':
            return tradable_epics

        else:
            future_time = now + timedelta(minutes=30)
            open_later_epics = only_open_epics(tradable_epics, future_time)
            #for epic in set(tradable_epics) - set(open_later_epics):
                # logger.info(f"Epic {epic} excluded: Market will close within the next 30 minutes.")
            return open_later_epics


    def _enter_the_market(self, epic: str, recommendation: OpenPositionRecommendation):
        market_data = self.market_data_repository.get_latest_market_data(epic, 1, self._now())
        if market_data.empty:
            logger.warning(f"No market data available for epic={epic}. Exiting early.")
            return

        balance = self.ig_trading_client.fetch_account_balance()
        logger.info(f"Available Balance is: {balance}")

        current_price = (market_data.iloc[0]['bid_close'] + market_data.iloc[0]['ask_close']) / 2
        # todo make stop loss and limit configurable
        stop_distance = current_price * 0.05
        limit_distance = current_price * 0.10
        size = round((balance * self.config['leverage']) / current_price, 2)
        amount = current_price * size
        logger.info(f"enter_the_market calculated: current_price={current_price}, stop_distance={stop_distance}, limit_distance={limit_distance}, size={size}, amount={amount}")

        response = self.ig_trading_client.open_position(epic, recommendation.direction, size, stop_distance, limit_distance)
        logger.info(f"Opened position: {response}")
        trade = Trade(id=response.get('dealId'), epic=epic, amount=amount, direction=recommendation.direction, confidence=recommendation.confidence or 0, size=size,
                      opened_at=self._now(), open_price=response.get('level'), open_comment=recommendation.reasoning or '', balance_at_opening=balance)
        self.trade_repository.insert_trade(trade)

    def _exit_the_market(self, position, comment: str):
        close_direction = TradeDirection.SELL if position['direction'] == TradeDirection.BUY else TradeDirection.BUY
        response = self.ig_trading_client.close_position(position['dealId'], close_direction, position['epic'], position['size'])
        logger.info(f"Closed position: {response}")

        self.trade_repository.close_trade(position['dealId'], self._now(), response['level'], response['profit'], comment)

    def _now(self) -> datetime:
        return self.backtest_datetime or datetime.now(timezone.utc)
