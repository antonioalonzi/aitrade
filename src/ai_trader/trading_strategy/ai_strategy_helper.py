import json
import logging

from ai_data_downloader.market_data.market_data_repository import MarketDataRepository
from ai_trader.trading_utils import trading_utils, trading_indicators

logger = logging.getLogger(__name__)


def _build_prompt_ai_market_data(market_data_repository: MarketDataRepository, config: dict, epic: str) -> str | None:
    epic_data = market_data_repository.get_latest_market_data(epic)
    if not epic_data.empty:
        avg_epic_data = trading_utils.avg_bid_offer(epic_data)
        ticks = trading_utils.aggregate_for_ai(avg_epic_data)

        if config['use_indicator_to_decide']:
            data = {
                "ticks": ticks,
                "indicators": {
                    "atr": trading_indicators.atr(avg_epic_data, 14),
                    "adx": trading_indicators.adx(avg_epic_data, 14),
                    #"rsi": trading_indicators.rsi(avg_epic_data, 14),
                    "ema_10": trading_indicators.window_exponential_average(avg_epic_data, 10, 5),
                    "ema_30": trading_indicators.window_exponential_average(avg_epic_data, 30, 5),
                    "ema_120": trading_indicators.window_exponential_average(avg_epic_data, 120, 5),
                }
            }
            logger.info(f"indicators: {json.dumps(data['indicators'])}")
            return json.dumps(data)

        else:
            return json.dumps(ticks)

    return None
