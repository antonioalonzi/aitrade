from ai_trader.trade.trade_repository import TradeRepository
from ai_web.controllers.utils.models import to_ui_trade


def display_trade_summary(trade_repository: TradeRepository):
    trades = trade_repository.get_all_trades()

    return {
        "trades": [to_ui_trade(t) for t in trades],
    }
