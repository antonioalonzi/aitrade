from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository


def display_graph(
        market_data_repository: MarketDataRepository,
        trade_repository: TradeRepository,
        epic: str | None,
        from_param: str | None,
        to_param: str | None,
        freq: str | None) -> dict:
    active_epics = market_data_repository.get_active_epics()
    epic = epic if epic else active_epics[0]

    return {
        "active_epics": active_epics,
        "epic": epic,
        "from": from_param,
        "to": to_param,
        "freq": freq
    }
