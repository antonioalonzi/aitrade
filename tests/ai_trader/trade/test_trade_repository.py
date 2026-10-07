from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trade.trade import Trade
from datetime import datetime
from copy import copy


def test_insert_trade(trade_repository: TradeRepository, trade_fixture: Trade):
    # given
    trade = copy(trade_fixture)
    trade.id = 'trade-001'

    # when
    trade_repository.insert_trade(trade)

    # then
    saved_trade = trade_repository.get_trade_by_id(trade.id)

    assert saved_trade is not None, "Trade with ID 'trade-001' was not saved"
    assert saved_trade == trade


def test_update_trade(trade_repository: TradeRepository, trade_fixture: Trade):
    # given
    trade = copy(trade_fixture)
    trade.id = 'trade-002'
    trade_repository.insert_trade(trade)

    # when
    trade_repository.close_trade("trade-002", datetime.fromisoformat("2023-01-01 15:00:00"), 510.0, 10, 'Close Trade')

    # then
    saved_trade = trade_repository.get_trade_by_id(trade.id)

    assert saved_trade is not None, "Trade with ID 'trade-002' was not saved"
    assert saved_trade.closed_at == datetime.fromisoformat("2023-01-01 15:00:00")
    assert saved_trade.close_price == 510.0
    assert saved_trade.profit_or_loss == 10
    assert saved_trade.close_comment == 'Close Trade'


def test_get_all_trades(trade_repository: TradeRepository, trade_fixture: Trade):
    # given
    trade_1 = copy(trade_fixture)
    trade_1.id = 'trade-001'
    trade_repository.insert_trade(trade_1)

    trade_2 = copy(trade_fixture)
    trade_2.id = 'trade-002'
    trade_repository.insert_trade(trade_2)

    # when
    trades = trade_repository.get_all_trades()

    # then
    assert len(trades) == 2
    assert trades[0].id == 'trade-001'
    assert trades[1].id == 'trade-002'


def test_get_last_trade(trade_repository: TradeRepository, trade_fixture: Trade):
    # given
    trade_1 = copy(trade_fixture)
    trade_1.id = 'trade-001'
    trade_1.opened_at = datetime.fromisoformat("2023-01-01 10:00:00")
    trade_repository.insert_trade(trade_1)

    trade_2 = copy(trade_fixture)
    trade_2.id = 'trade-002'
    trade_2.opened_at = datetime.fromisoformat("2023-01-01 11:00:00")
    trade_repository.insert_trade(trade_2)

    # when
    last_trade = trade_repository.get_last_trade()

    # then
    assert last_trade.id == "trade-002"
