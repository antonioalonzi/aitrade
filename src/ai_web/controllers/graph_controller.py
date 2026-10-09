from datetime import datetime, timedelta, timezone

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade
from ai_web.controllers.utils.models import to_ui_trade
from ai_web.controllers.utils.time_utils import to_localised_time

DISPLAY_OFFSET = timedelta(hours=3)


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
    last_price = get_last_price_for_trade(market_data_repository, trade)

    trade_opened_at = None
    trade_closed_at = None
    if trade:
        epic = trade.epic
        # trade_opened_at = to_localised_time(datetime.fromisoformat(trade.opened_at))
        if not from_param:
            from_param = (trade.opened_at - DISPLAY_OFFSET).strftime("%Y-%m-%d %H:%M:%S")
        if trade.closed_at:
            # trade_closed_at = to_localised_time(datetime.fromisoformat(trade.closed_at))
            if not to_param and trade.closed_at:
                to_param = (trade.closed_at + DISPLAY_OFFSET).strftime("%Y-%m-%d %H:%M:%S")

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
        "trade": to_ui_trade(trade),
        "last_price": last_price,
    }

def opposite_direction(direction: str) -> str | None:
    if direction == "SELL":
        return "BUY"
    elif direction == "BUY":
        return "SELL"
    else:
        return None
