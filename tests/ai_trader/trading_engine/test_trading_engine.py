import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import TradeDirection
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_engine.openai_engine import OpenPositionRecommendation, CloseDecision
from ai_trader.trading_engine.trader import Trader

logger = logging.getLogger(__name__)

def test_trading_engine(trade_repository: TradeRepository, market_data_repository: MarketDataRepository, market_data_fixture: dict):
    # given
    epic = "IX.D.SPTRD.DAILY.IP"
    now = datetime.fromisoformat("2026-10-20T13:47:05+00")
    max_iterations = 60

    ig_trading_client = MagicMock()
    ig_trading_client.fetch_account_balance.return_value = 10_000

    openai_engine = MagicMock()

    trader_config = {
        'epics': [epic],
        'confidence_threshold': 50,
        'percentage_of_balance_to_trade': 50,
        'use_indicator_to_decide': True,
        'evaluate_enter_the_market_interval_in_minutes': 4,
        'evaluate_exit_the_market_interval_in_minutes': 2,
    }

    trader = Trader(openai_engine, ig_trading_client, trade_repository, market_data_repository, trader_config)
    trader.backtest_datetime = now

    # when
    iteration = 0
    open_position = None
    while iteration < max_iterations:
        iteration += 1
        now += timedelta(minutes=1)
        market_data_repository.insert_market_data(epic, market_data_fixture | {"datetime": now.strftime('%Y-%m-%d %H:%M:%S')})
        market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        def mock_ask_to_open_a_position(now: datetime, config: dict, epic: str, data: str):
            if iteration >= 20:
                return OpenPositionRecommendation(direction=TradeDirection.BUY, reasoning='Test', confidence=90)
            else:
                return OpenPositionRecommendation(direction=TradeDirection.NONE, reasoning=None, confidence=None)
        openai_engine.ask_to_open_a_position.side_effect = mock_ask_to_open_a_position

        def mock_open_position(epic, direction, size, stop_distance, limit_distance):
            market_data = market_data_repository.get_latest_market_data(epic).iloc[-1]
            level = market_data['ask_close'] if direction == 'BUY' else market_data['bid_close']
            return {
                "dealId": "DEAL_001",
                "level": float(level)
            }
        ig_trading_client.open_position.side_effect = mock_open_position

        trader._execute_trade_decision(open_position=None)
        trades = trade_repository.get_all_trades()
        if trades:
            trade = trades[0]
            open_position = {"epic": trade.epic, "dealId": trade.id, "direction": trade.direction, "size": trade.size, "open_price": trade.open_price}
            logger.info(f"OPENED TRADE: {trade} (open_position: {open_position})")
            break


    while iteration < max_iterations:
        iteration += 1
        now += timedelta(minutes=1)
        market_data_repository.insert_market_data(epic, market_data_fixture | {"datetime": now.strftime('%Y-%m-%d %H:%M:%S')})
        market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        def mock_ask_to_close_a_position(now: datetime, config: dict, open_position, profit_or_loss: float | None, data: str):
            if iteration >= 40:
                return CloseDecision(should_close=False, reasoning=None)
            else:
                return CloseDecision(should_close=True, reasoning='Test')
        openai_engine.ask_to_close_a_position.side_effect = mock_ask_to_close_a_position

        def mock_close_position(deal_id, direction, epic_arg, size, repo=market_data_repository):
            market_data = repo.get_latest_market_data(epic_arg).iloc[-1]
            level = market_data['ask_close'] if direction == 'BUY' else market_data['bid_close']
            diff = level - open_position['open_price'] if open_position['direction'] == 'BUY' else open_position['open_price'] - level
            return {
                "level": level,
                "profit": diff * size,
            }
        ig_trading_client.close_position.side_effect = mock_close_position

        trader._execute_trade_decision(open_position)
        trade = trade_repository.get_all_trades()[0]
        if trade.closed_at is not None:
            logger.info(f"CLOSED TRADE: {trade}")
            break

    assert len(trade_repository.get_all_trades()) > 0