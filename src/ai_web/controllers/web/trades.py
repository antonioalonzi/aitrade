from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository


def display_trades(market_data_repository: MarketDataRepository, trade_repository: TradeRepository):
    trades = trade_repository.get_all_trades()

    return {
        "trades": trades
    }
