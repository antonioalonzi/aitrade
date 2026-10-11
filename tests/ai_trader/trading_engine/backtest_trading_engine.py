import logging
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_engine.openai_engine import OpenAIEngine
from ai_trader.trading_engine.trader import Trader

logger = logging.getLogger(__name__)

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping test in CI/GitHub Actions")
def test_trading_engine(back_testing_trade_repository: TradeRepository, real_market_data_repository: MarketDataRepository):
    # given
    epic = "IX.D.SPTRD.DAILY.IP"
    real_market_data_repository.backtest_datetime = datetime.fromisoformat("2026-10-07T16:00:00")
    max_iterations = 20

    ig_trading_client = MagicMock()
    ig_trading_client.open_position.return_value.get.side_effect = lambda key: {
        "dealId": "DEAL_001",
        "level": real_market_data_repository.get_latest_market_data(epic).iloc[-1]['offer_close'],
    }[key]
    ig_trading_client.close_position.return_value = {
        "level": real_market_data_repository.get_latest_market_data(epic).iloc[-1]['offer_close'],
        "profit": 0, # don't care to calculate it now
    }

    trading_engine = OpenAIEngine('http://server:9402', 'deepseek-r1:32b', None, 16384, 0.1, 240)

    trader_config = {
        'epics': [epic],
        'confidence_threshold': 50,
        'percentage_of_balance_to_trade': 50,
        'use_indicator_to_decide': True,
        'evaluate_enter_the_market_interval_in_minutes': 1,
        'evaluate_exit_the_market_interval_in_minutes': 1,
    }

    trader = Trader(trading_engine, ig_trading_client, back_testing_trade_repository, real_market_data_repository, trader_config)
    trader.balance = 10_000

    # when
    iteration = 0
    open_position = None
    while iteration < max_iterations:
        iteration += 1
        real_market_data_repository.backtest_datetime += timedelta(minutes=4)
        logger.info(f"backtest_datetime: {real_market_data_repository.backtest_datetime} - Iteration {iteration}")
        trader._execute_trade_decision(open_position=None)
        trades = back_testing_trade_repository.get_all_trades()
        if trades:
            trade = trades[0]
            open_position = {"epic": trade.epic, "dealId": trade.id, "direction": trade.direction, "size": trade.size}
            logger.info(f"OPENED TRADE: {trade} (open_position: {open_position})")
            break

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"backtest_datetime: {real_market_data_repository.backtest_datetime} - Iteration {iteration}")
        real_market_data_repository.backtest_datetime += timedelta(minutes=2)
        trader._execute_trade_decision(open_position)
        trade = back_testing_trade_repository.get_all_trades()[0]
        if trade.closed_at is not None:
            logger.info(f"CLOSED TRADE: {trade}")
            break