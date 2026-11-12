from ai_trader.trade.trade import Trade

from ai_web.controllers.web_utils.time_utils import to_localised_time


def to_ui_trade(trade: Trade | None, current_price: float | None = None) -> dict | None:
    if not trade:
        return None

    opened_at = to_localised_time(trade.opened_at)
    closed_at = to_localised_time(trade.closed_at)

    return {
        **trade.__dict__,
        "opened_at": opened_at.strftime('%Y-%m-%d %H:%M:%S') if opened_at else None,
        "opened_at_timestamp": opened_at.timestamp() if opened_at else None,
        "open_direction": trade.direction,
        "closed_at": closed_at.strftime('%Y-%m-%d %H:%M:%S') if closed_at else None,
        "closed_at_timestamp": closed_at.timestamp() if closed_at else None,
        "close_direction": _opposite_direction(trade.direction),
        "calculated_profit_and_loss": trade.calculate_profit_and_loss(current_price),
    }

def _opposite_direction(direction: str) -> str | None:
    if direction == "SELL":
        return "BUY"
    elif direction == "BUY":
        return "SELL"
    else:
        return None