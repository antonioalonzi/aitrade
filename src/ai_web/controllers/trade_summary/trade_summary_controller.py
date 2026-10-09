from ai_web.controllers.trade_summary.trade_summary import TradeSummaryType
from ai_web.controllers.trade_summary.trade_summary_repository import TradeSummaryRepository


def display_trade_summary(trade_summary_repository: TradeSummaryRepository, summary_type: TradeSummaryType):
    trade_summary = trade_summary_repository.get_trade_summary(summary_type)

    return {
        "trade_summary": trade_summary,
        "summary_type": summary_type.name
    }
