import sqlite3

from ai_web.controllers.trade_summary.trade_summary import TradeSummary, TradeSummaryType


class TradeSummaryRepository:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name

    def get_trade_summary(self, type: TradeSummaryType) -> list[TradeSummary]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime(?, closed_at) AS timeframe,
                    COUNT(id) AS total_trades,
                    SUM(profit_or_loss) AS net_pnl,
                    (SUM(profit_or_loss) / FIRST_VALUE(balance_at_opening) OVER (
                        PARTITION BY strftime(?, closed_at) 
                        ORDER BY opened_at ASC
                    )) * 100 AS net_pnl_perc,
                    AVG(profit_or_loss) AS avg_pnl,
                    FIRST_VALUE(balance_at_opening) OVER (
                        PARTITION BY strftime(?, closed_at) 
                        ORDER BY opened_at ASC
                    ) AS balance_at_opening
                FROM trades
                WHERE closed_at IS NOT NULL
                GROUP BY timeframe
                ORDER BY timeframe DESC;
            """, (type.value, type.value, type.value))
            row = cursor.fetchall()
            return [TradeSummary.from_row(r) for r in row]
