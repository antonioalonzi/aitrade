from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade


def display_trades(market_data_repository: MarketDataRepository, trade_repository: TradeRepository):
    trades = trade_repository.get_all_trades()
    last_trade = trades[0] if trades else None
    last_price = get_last_price_for_trade(market_data_repository, last_trade)

    return {
        "trades": trades,
        "last_price": last_price,
    }
