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
    now = datetime.fromisoformat("2026-10-20T13:48:05+00")
    max_iterations = 20

    ig_trading_client = MagicMock()
    ig_trading_client.open_position.return_value.get.side_effect = lambda key: {
        "dealId": "DEAL_001",
        "level": real_market_data_repository.get_latest_market_data(epic).iloc[-1]['ask_close'],
    }[key]

    ig_trading_client.close_position.return_value = {
        "level": real_market_data_repository.get_latest_market_data(epic).iloc[-1]['ask_close'],
        "profit": 0, # don't care to calculate it now
    }
    ig_trading_client.fetch_account_balance.return_value = 10_000

    trading_engine = OpenAIEngine('http://server:9402', 'deepseek-r1:32b', None, 16384, 0.1, 240)

    trader_config = {
        'epics': [epic],
        'confidence_threshold': 50,
        'percentage_of_balance_to_trade': 50,
        'use_indicator_to_decide': True,
        'evaluate_enter_the_market_interval_in_minutes': 4,
        'evaluate_exit_the_market_interval_in_minutes': 2,
    }

    trader = Trader(trading_engine, ig_trading_client, back_testing_trade_repository, real_market_data_repository, trader_config)
    trader.backtest_datetime = now

    # when
    iteration = 0
    open_position = None
    while iteration < max_iterations:
        real_market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        trader._execute_trade_decision(open_position=None)
        trades = back_testing_trade_repository.get_all_trades()
        if trades:
            trade = trades[0]
            open_position = {"epic": trade.epic, "dealId": trade.id, "direction": trade.direction, "size": trade.size}
            logger.info(f"OPENED TRADE: {trade} (open_position: {open_position})")
            break

        iteration += 1
        now += timedelta(minutes=1)

    while iteration < max_iterations:
        real_market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        trader._execute_trade_decision(open_position)
        trade = back_testing_trade_repository.get_all_trades()[0]
        if trade.closed_at is not None:
            logger.info(f"CLOSED TRADE: {trade}")
            break

        iteration += 1
        now += timedelta(minutes=1)
