from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository


def display_graph(
        market_data_repository: MarketDataRepository,
        trade_repository: TradeRepository,
        epic: str,
        from_param: str,
        to_param: str,
        freq: str) -> dict:
    return {
        "epic": epic,
        "from": from_param,
        "to": to_param,
        "freq": freq
    }
