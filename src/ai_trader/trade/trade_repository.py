import sqlite3

from ai_trader.trade.trade import Trade


class TradeRepository:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    epic TEXT NOT NULL,
                    amount REAL NOT NULL,
                    direction TEXT NOT NULL,
                    confidence INT NOT NULL,
                    size REAL NOT NULL,
                    opened_at TEXT NOT NULL,
                    open_price REAL NOT NULL,
                    open_comment TEXT NOT NULL,
                    closed_at TEXT,
                    close_price REAL,
                    close_comment TEXT,
                    profit_or_loss REAL,
                    balance_at_opening REAL
                )
                """)
            conn.commit()

    def insert_trade(self, trade: Trade) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO trades (id, epic, amount, direction, confidence, size, opened_at, open_price, open_comment, balance_at_opening)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade.id,
                    trade.epic,
                    trade.amount,
                    trade.direction,
                    trade.confidence,
                    trade.size,
                    trade.opened_at,
                    trade.open_price,
                    trade.open_comment,
                    trade.balance_at_opening,
                )
            )
            conn.commit()

    def close_trade(self, trade_id: str, closed_at: str, closed_price: float, profit_or_loss: float, close_comment: str) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE trades
                SET closed_at = ?,
                    close_price = ?,
                    profit_or_loss = ?,
                    close_comment = ?
                WHERE id = ?
                """,
                (closed_at, closed_price, profit_or_loss, close_comment, trade_id)
            )
            conn.commit()

    def get_trade_by_id(self, trade_id) -> Trade | None:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
            row = cursor.fetchone()

            if row:
                return Trade.from_row(row)

            return None


    def get_all_trades(self) -> list[Trade]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY opened_at DESC")
            rows = cursor.fetchall()
            return [Trade.from_row(row) for row in rows]

    def get_last_trade(self) -> Trade | None:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY opened_at DESC LIMIT 1")
            row = cursor.fetchone()
            return Trade.from_row(row) if row else None
