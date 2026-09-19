from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository


def display_index(market_data_repository: MarketDataRepository, trade_repository: TradeRepository):
    active_epics = market_data_repository.get_active_epics()
    last_trade = trade_repository.get_open_trade()

    return {
        "active_epics": active_epics,
        "last_trade": last_trade
    }
