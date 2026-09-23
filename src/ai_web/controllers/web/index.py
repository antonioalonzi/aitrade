from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository
from ai_trader.trading_utils.last_price_service import get_last_price_for_trade


def display_index(market_data_repository: MarketDataRepository, trade_repository: TradeRepository):
    active_epics = market_data_repository.get_active_epics()
    last_trade = trade_repository.get_last_trade()
    last_price = get_last_price_for_trade(market_data_repository, last_trade)

    return {
        "active_epics": active_epics,
        "last_trade": last_trade,
        "last_price": last_price
    }
