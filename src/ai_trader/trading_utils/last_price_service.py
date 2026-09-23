from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trade.trade import Trade


def get_last_price_for_trade(market_data_repository: MarketDataRepository, last_trade: Trade | None) -> float | None:
    if last_trade and not last_trade.profit_or_loss:
        last_tick = market_data_repository.get_last_ticks([last_trade.epic])
        if last_trade.direction == "BUY":
            return last_tick['offer_close'].item()
        else:
            return last_tick['bid_close'].item()

    return None
