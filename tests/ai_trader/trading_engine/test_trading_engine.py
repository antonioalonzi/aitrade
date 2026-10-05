import os
from unittest.mock import MagicMock

import pytest

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_engine.openai_engine import OpenAIEngine
from ai_trader.trading_engine.trader import Trader


@pytest.mark.skipif(os.getenv("CI") == "true", reason="Skipping test in CI/GitHub Actions")
def test_trader(trade_repository: TradeRepository, real_market_data_repository: MarketDataRepository):
    # given
    ig_trading_client = MagicMock()
    ig_trading_client.open_position.return_value.get.return_value = "DEAL_001"

    trading_engine = OpenAIEngine('http://server:9402', 'deepseek-r1:32b', None, 16384, 0.1, 240)

    trader_config = {
        'epics': ['IX.D.SPTRD.DAILY.IP'],
        'confidence_threshold': 50,
        'percentage_of_balance_to_trade': 50,
        'use_indicator_to_decide': False,
        'evaluate_enter_the_market_interval_in_minutes': 1
    }

    trader = Trader(trading_engine, ig_trading_client, trade_repository, real_market_data_repository, trader_config)
    trader.balance = 10_000

    # when
    trader._execute_trade_decision(open_position=None)

    # then
    print(f"All Trades: {trade_repository.get_all_trades()}")
