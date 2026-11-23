import logging
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trader.trader import Trader
from ai_trader.trading_strategy.indicator_strategy import IndicatorOpenStrategy, IndicatorCloseStrategy

logger = logging.getLogger(__name__)

@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping test in CI/GitHub Actions")
def test_trading_engine(back_testing_trade_repository: TradeRepository, real_market_data_repository: MarketDataRepository):
    # given
    epic = "IX.D.SPTRD.DAILY.IP"
    now = datetime.fromisoformat("2026-11-23T14:30:05+00")
    max_iterations = 60 * 7

    ig_trading_client = MagicMock()
    ig_trading_client.fetch_account_balance.return_value = 3_000


    trader_config = {
        'epics': [epic],
        'leverage': 1.2,
        'ai_strategy_decision_mode': 'INDICATORS_ONLY',
        'indicator_ema_fast': 10,
        'indicator_ema_slow': 30,
        'indicator_ema_trend': 120,
        'evaluate_enter_the_market_interval_in_minutes': 2,
        'evaluate_exit_the_market_interval_in_minutes': 1,
        'trade_minimum_length_in_minutes': 4,
    }

    # openai_engine = OpenAIClient('http://server:9402', 'qwen2.5-coder:32b', None, 16384, 0.1, 240)
    # open_strategy_bean = AiOpenStrategy(openai_engine, real_market_data_repository, trader_config)
    # close_strategy_bean = AiCloseStrategy(openai_engine, real_market_data_repository, trader_config)

    open_strategy_bean = IndicatorOpenStrategy(real_market_data_repository, trader_config)
    close_strategy_bean = IndicatorCloseStrategy(real_market_data_repository, trader_config)

    trader = Trader(open_strategy_bean, close_strategy_bean, ig_trading_client, back_testing_trade_repository, real_market_data_repository, trader_config)
    trader.backtest_datetime = now

    next_deal_id = 1

    def mock_open_position(epic, direction, size, stop_distance, limit_distance):
        nonlocal next_deal_id
        market_data = real_market_data_repository.get_latest_market_data(epic, 1, now).iloc[-1]
        level = market_data['ask_close'] if direction == 'BUY' else market_data['bid_close']
        deal_id = f"DEAL_{next_deal_id:03d}"
        next_deal_id += 1
        return {
            "dealId": deal_id,
            "level": float(level),
            "createdDate": now.strftime('%Y-%m-%dT%H:%M:%S'),
        }

    def mock_close_position(deal_id, direction, epic_arg, size):
        open_trade = back_testing_trade_repository.get_trade_by_id(deal_id)
        market_data = real_market_data_repository.get_latest_market_data(epic_arg, 1, now).iloc[-1]
        if open_trade.direction == 'BUY':
            level = market_data['bid_close']
            diff = level - open_trade.open_price
        else:
            level = market_data['ask_close']
            diff = open_trade.open_price - level
        return {
            "level": float(level),
            "profit": diff * size,
        }

    ig_trading_client.open_position.side_effect = mock_open_position
    ig_trading_client.close_position.side_effect = mock_close_position

    # when
    iteration = 0
    open_position = None
    while iteration < max_iterations:
        iteration += 1
        now += timedelta(minutes=1)
        real_market_data_repository.backtest_datetime = now
        trader.backtest_datetime = now
        logger.info(f"backtest_datetime: {now} - Iteration {iteration}")

        trader._execute_trade_decision(open_position)

        trades = back_testing_trade_repository.get_all_trades()
        active_trades = [trade for trade in trades if trade.closed_at is None]
        open_position = None
        if active_trades:
            trade = active_trades[0]
            open_position = {
                "epic": trade.epic,
                "dealId": trade.id,
                "direction": trade.direction,
                "size": trade.size,
                "level": trade.open_price,
                "createdDate": trade.opened_at.strftime('%Y-%m-%dT%H:%M:%S'),
            }

    trades = back_testing_trade_repository.get_all_trades()
    for trade in reversed(trades):
        logger.info(
            "TRADE: id=%s direction=%s opened_at=%s open_price=%s closed_at=%s "
            "close_price=%s profit_or_loss=%s",
            trade.id,
            trade.direction,
            trade.opened_at,
            trade.open_price,
            trade.closed_at,
            trade.close_price,
            round(trade.profit_or_loss or 0, 2),
        )

    assert iteration == max_iterations
    assert [trade.id for trade in reversed(trades)] == [
        f"DEAL_{deal_number:03d}" for deal_number in range(1, len(trades) + 1)
    ]
