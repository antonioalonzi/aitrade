from datetime import datetime

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade_repository import TradeRepository


def display_index(market_data_repository: MarketDataRepository, trade_repository: TradeRepository):
    active_epics = market_data_repository.get_active_epics()
    trades = trade_repository.get_all_trades()

    return {
        "active_epics": active_epics,
        "trades": trades
    }

def parse_isodatetime(isodatetime_str: str | None) -> datetime | None:
    return datetime.fromisoformat(isodatetime_str) if isodatetime_str else None

def format_time(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else '-'


