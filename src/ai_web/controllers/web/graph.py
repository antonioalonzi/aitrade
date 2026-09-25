from datetime import datetime, timedelta

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository

DISPLAY_OFFSET = timedelta(minutes=10)


def display_graph(
        market_data_repository: MarketDataRepository,
        trade_repository: TradeRepository,
        trade_id: str | None,
        epic: str | None,
        from_param: str | None,
        to_param: str | None,
        freq: str | None) -> dict:
    active_epics = market_data_repository.get_active_epics()
    trade = trade_repository.get_trade_by_id(trade_id)

    trade_opened_at = None
    trade_closed_at = None
    if trade:
        epic = trade.epic
        trade_opened_at = datetime.fromisoformat(trade.opened_at)
        if not from_param:
            from_param = (trade_opened_at - DISPLAY_OFFSET).strftime("%Y-%m-%d %H:%M:%S")
        if trade.closed_at:
            trade_closed_at = datetime.fromisoformat(trade.closed_at)
            if not to_param and trade.closed_at:
                to_param = (trade_closed_at + DISPLAY_OFFSET).strftime("%Y-%m-%d %H:%M:%S")

    epic = epic or active_epics[0]
    from_param = from_param or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    to_param = to_param or "2100-01-01 00:00:00"
    freq = freq or "1min"

    return {
        "active_epics": active_epics,
        "epic": epic,
        "from": from_param,
        "to": to_param,
        "freq": freq,
        "trade_opened_at": trade_opened_at.strftime("%Y-%m-%d %H:%M:%S") if trade_opened_at else None,
        "trade_closed_at": trade_closed_at.strftime("%Y-%m-%d %H:%M:%S") if trade_closed_at else None,
    }
