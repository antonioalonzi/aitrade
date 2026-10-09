from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trade.trade import Trade
from datetime import datetime
from copy import copy

from ai_web.controllers.trade_summary.trade_summary import TradeSummaryType, TradeSummary
from ai_web.controllers.trade_summary.trade_summary_repository import TradeSummaryRepository


def test_get_trade_summary(trade_repository: TradeRepository, trade_summary_repository: TradeSummaryRepository, trade_fixture: Trade):
    # given
    trade_1 = copy(trade_fixture)
    trade_1.id = 'trade-001'
    trade_1.balance_at_opening = 1000
    trade_repository.insert_trade(trade_1)
    trade_repository.close_trade("trade-001", datetime.fromisoformat("2023-01-01 10:00:00"), 510.0, 10, 'Close Trade') # Sunday

    trade_2 = copy(trade_fixture)
    trade_2.id = 'trade-002'
    trade_2.balance_at_opening = 1010
    trade_repository.insert_trade(trade_2)
    trade_repository.close_trade("trade-002", datetime.fromisoformat("2023-01-01 11:00:00"), 510.0, 20, 'Close Trade') # Sunday

    trade_3 = copy(trade_fixture)
    trade_3.id = 'trade-003'
    trade_3.balance_at_opening = 1030
    trade_repository.insert_trade(trade_3)
    trade_repository.close_trade("trade-003", datetime.fromisoformat("2023-01-02 10:00:00"), 510.0, 30, 'Close Trade')  # Monday

    trade_4 = copy(trade_fixture)
    trade_4.id = 'trade-004'
    trade_4.balance_at_opening = 1060
    trade_repository.insert_trade(trade_4)
    trade_repository.close_trade("trade-004", datetime.fromisoformat("2023-01-09 10:00:00"), 510.0, 40, 'Close Trade')  # Next Monday

    trade_5 = copy(trade_fixture)
    trade_5.id = 'trade-005'
    trade_5.balance_at_opening = 1100
    trade_repository.insert_trade(trade_5)
    trade_repository.close_trade("trade-005", datetime.fromisoformat("2023-01-09 11:00:00"), 510.0, 50, 'Close Trade')  # Next Monday

    trade_6 = copy(trade_fixture)
    trade_6.id = 'trade-006'
    trade_6.balance_at_opening = 1150
    trade_repository.insert_trade(trade_6)
    trade_repository.close_trade("trade-006", datetime.fromisoformat("2023-02-01 11:00:00"), 510.0, 100, 'Close Trade')  # Next Month

    # when
    daily_summary = trade_summary_repository.get_trade_summary(TradeSummaryType.DAILY)

    # then
    assert daily_summary == [
        TradeSummary('2023-02-01', 1, 100, 8.7, 100, 1150),
        TradeSummary('2023-01-09', 2, 90, 8.49, 45, 1060),
        TradeSummary('2023-01-02', 1, 30, 2.91, 30, 1030),
        TradeSummary('2023-01-01', 2, 30, 3.0, 15, 1000),
    ]

    # when
    weekly_summary = trade_summary_repository.get_trade_summary(TradeSummaryType.WEEKLY)

    # then
    assert weekly_summary == [
        TradeSummary('2023-05', 1, 100, 8.7, 100, 1150),
        TradeSummary('2023-02', 2, 90, 8.49, 45, 1060),
        TradeSummary('2023-01', 1, 30, 2.91, 30, 1030),
        TradeSummary('2023-00', 2, 30, 3.0, 15, 1000),
    ]

    # when
    monthly_summary = trade_summary_repository.get_trade_summary(TradeSummaryType.MONTHLY)

    # then
    assert monthly_summary == [
        TradeSummary('2023-02', 1, 100, 8.7, 100, 1150),
        TradeSummary('2023-01', 5, 150, 15.0, 30, 1000),
    ]
