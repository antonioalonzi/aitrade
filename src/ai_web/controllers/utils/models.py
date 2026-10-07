from ai_trader.trade.trade import Trade
import copy

from ai_web.controllers.utils.time_utils import to_localised_time


def to_ui_trade(trade: Trade | None) -> Trade | None:
    if not trade:
        return None
    ui_trade = copy.copy(trade)
    ui_trade.opened_at = to_localised_time(trade.opened_at)
    ui_trade.opened_at_timestamp = ui_trade.opened_at.timestamp()
    ui_trade.open_direction = trade.direction
    ui_trade.closed_at = to_localised_time(trade.closed_at)
    ui_trade.closed_at_timestamp = ui_trade.closed_at.timestamp() if ui_trade.closed_at else None
    ui_trade.close_direction = _opposite_direction(ui_trade.direction)
    return ui_trade

def _opposite_direction(direction: str) -> str | None:
    if direction == "SELL":
        return "BUY"
    elif direction == "BUY":
        return "SELL"
    else:
        return None