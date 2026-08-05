from trade.trade import Trade
from trade.trade_repository import TradeRepository


def test_insert_trade(trade_repository: TradeRepository):
    # given
    trade = Trade(
        id="trade-001",
        epic="NVIDIA",
        amount=100.0,
        opened_at="2023-01-01 10:00:00",
        open_price=500.0,
        comment="Test trade"
    )

    # when
    trade_repository.insert_trade(trade)

    # then
    trades = trade_repository.get_all_trades()
    saved_trade = next((t for t in trades if t.id == "trade-001"), None)

    assert saved_trade is not None, "Trade with ID 'trade-001' was not saved"
    assert saved_trade == trade


def test_update_trade(trade_repository: TradeRepository):
    # given
    trade = Trade(
        id="trade-002",
        epic="NVIDIA",
        amount=100,
        opened_at="2023-01-01 10:00:00",
        open_price=500.0,
        comment="Test trade"
    )
    trade_repository.insert_trade(trade)

    # when
    trade.closed_at = "2023-01-01 15:00:00"
    trade.close_price = 510.0
    trade.profit_or_loss = 10

    trade_repository.update_trade(trade)

    # then
    trades = trade_repository.get_all_trades()
    saved_trade = next((t for t in trades if t.id == "trade-002"), None)

    assert saved_trade is not None, "Trade with ID 'trade-002' was not saved"
    assert saved_trade == trade
