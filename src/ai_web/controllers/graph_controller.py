from datetime import datetime, timedelta, timezone

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade
from ai_web.controllers.web_utils.models import to_ui_trade

DISPLAY_OFFSET = timedelta(hours=1)


def display_graph(
        market_data_repository: MarketDataRepository,
        trade_repository: TradeRepository,
        trade_id: str | None,
        trading_day: str | None,
        epic: str | None,
        from_param: str | None,
        to_param: str | None,
        freq: str | None) -> dict:

    active_epics = market_data_repository.get_active_epics()

    trades = fetch_trades(trade_repository, trade_id, trading_day)
    first_trade = trades[-1] if trades else None

    # trades could be from different epics, so we filter them by the epic parameter if provided
    if not epic and first_trade:
        epic = first_trade.epic
    trades = [trade for trade in trades if trade.epic == epic]

    last_trade = trades[0] if trades else None
    last_price = get_last_price_for_trade(market_data_repository, last_trade)

    if trades:
        if not from_param:
            from_param = (first_trade.opened_at - DISPLAY_OFFSET).strftime("%Y-%m-%d %H:%M:%S")
        if last_trade.closed_at:
            if not to_param and last_trade.closed_at:
                to_param = (last_trade.closed_at + DISPLAY_OFFSET).strftime("%Y-%m-%d %H:%M:%S")

    epic = epic or active_epics[0]
    from_param = from_param or (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    to_param = to_param or "2100-01-01 00:00:00"
    freq = freq or "1min"

    return {
        "active_epics": active_epics,
        "epic": epic,
        "from": from_param,
        "to": to_param,
        "freq": freq,
        "trades": [to_ui_trade(t, last_price) for t in trades],
        "trade_id": trade_id,
        "trading_day": trading_day,
    }


def fetch_trades(trade_repository: TradeRepository, trade_id: str | None, trading_day: str | None) -> list[Trade]:
    trade = trade_repository.get_trade_by_id(trade_id)
    if trade:
        return [trade]
    elif trading_day:
        return trade_repository.get_trades_opened_at_like(trading_day)
    return []
