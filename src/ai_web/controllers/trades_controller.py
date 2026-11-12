import json

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade
from ai_web.controllers.web_utils.models import to_ui_trade


def get_trade_by_id(trade_repository: TradeRepository, trade_id: str) -> str | None:
    trade = trade_repository.get_trade_by_id(trade_id)
    if trade is None:
        return None

    trade_data = to_ui_trade(trade)
    return json.dumps(trade_data)


def get_trade_by_date_and_epic(trade_repository: TradeRepository, trading_day: str, epic: str) -> str | None:
    trades = trade_repository.get_trades_opened_at_like(trading_day)

    trade_data = [to_ui_trade(trade) for trade in trades if trade.epic == epic]
    return json.dumps(trade_data)


def display_trades(market_data_repository: MarketDataRepository, trade_repository: TradeRepository, opened_at_like: str):
    if opened_at_like:
        trades = trade_repository.get_trades_opened_at_like(opened_at_like)
    else:
        trades = trade_repository.get_all_trades()

    last_trade = trades[0] if trades else None
    last_price = get_last_price_for_trade(market_data_repository, last_trade)

    return {
        "trades": [to_ui_trade(t, last_price) for t in trades],
    }
