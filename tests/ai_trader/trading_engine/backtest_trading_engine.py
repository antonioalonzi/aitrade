import logging
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_strategy.ai_strategy import AiOpenStrategy, AiCloseStrategy
from ai_trader.trading_strategy.openai_client import OpenAIClient
from ai_trader.trader.trader import Trader

logger = logging.getLogger(__name__)

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping test in CI/GitHub Actions")
def test_trading_engine(back_testing_trade_repository: TradeRepository, real_market_data_repository: MarketDataRepository):
    # given
    epic = "IX.D.SPTRD.DAILY.IP"
    now = datetime.fromisoformat("2026-10-20T13:47:05+00")
    max_iterations = 60

    ig_trading_client = MagicMock()
    ig_trading_client.fetch_account_balance.return_value = 10_000


    openai_engine = OpenAIClient('http://server:9402', 'qwen2.5-coder:32b', None, 16384, 0.1, 240)

    trader_config = {
        'epics': [epic],
        'confidence_threshold': 50,
        'leverage': 1.0,
        'ai_strategy_decision_mode': 'INDICATORS_ONLY',
        'indicator_ema_fast': 10,
        'indicator_ema_slow': 30,
        'indicator_ema_trend': 120,
        'evaluate_enter_the_market_interval_in_minutes': 2,
        'evaluate_exit_the_market_interval_in_minutes': 1,
    }

    ai_open_strategy_bean = AiOpenStrategy(openai_engine, real_market_data_repository, trader_config)
    ai_close_strategy_bean = AiCloseStrategy(openai_engine, real_market_data_repository, trader_config)

    trader = Trader(ai_open_strategy_bean, ai_close_strategy_bean, ig_trading_client, back_testing_trade_repository, real_market_data_repository, trader_config)
    trader.backtest_datetime = now

    # when
    iteration = 0
    open_position = None
    while iteration < max_iterations:
        iteration += 1
        now += timedelta(minutes=1)
        real_market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        def mock_open_position(epic, direction, size, stop_distance, limit_distance):
            market_data = real_market_data_repository.get_latest_market_data(epic, 1, now).iloc[-1]
            level = market_data['ask_close'] if direction == 'BUY' else market_data['bid_close']
            return {
                "dealId": "DEAL_001",
                "level": float(level)
            }
        ig_trading_client.open_position.side_effect = mock_open_position

        trader._execute_trade_decision(open_position=None)
        trades = back_testing_trade_repository.get_all_trades()
        if trades:
            trade = trades[0]
            open_position = {"epic": trade.epic, "dealId": trade.id, "direction": trade.direction, "size": trade.size, "open_price": trade.open_price}
            logger.info(f"OPENED TRADE: {trade} (open_position: {open_position})")
            break


    while iteration < max_iterations:
        iteration += 1
        now += timedelta(minutes=1)
        real_market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        def mock_close_position(deal_id, direction, epic_arg, size, repo=real_market_data_repository):
            market_data = repo.get_latest_market_data(epic_arg, 1, now).iloc[-1]
            level = market_data['ask_close'] if direction == 'BUY' else market_data['bid_close']
            diff = level - open_position['open_price'] if open_position['direction'] == 'BUY' else open_position['open_price'] - level
            return {
                "level": level,
                "profit": diff * size,
            }
        ig_trading_client.close_position.side_effect = mock_close_position

        trader._execute_trade_decision(open_position)
        trade = back_testing_trade_repository.get_all_trades()[0]
        if trade.closed_at is not None:
            logger.info(f"CLOSED TRADE: {trade}")
            break
