import sqlite3

from trade.trade import Trade


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
                    size REAL NOT NULL,
                    opened_at TEXT NOT NULL,
                    open_price REAL NOT NULL,
                    comments TEXT NOT NULL,
                    closed_at TEXT,
                    close_price REAL,
                    profit_or_loss REAL
                )
                """)
            conn.commit()

    def insert_trade(self, trade: Trade) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO trades (id, epic, amount, direction, size, opened_at, open_price, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade.id,
                    trade.epic,
                    trade.amount,
                    trade.direction,
                    trade.size,
                    trade.opened_at,
                    trade.open_price,
                    trade.comment,
                )
            )
            conn.commit()

    def close_trade(self, trade_id: str, closed_at: str, closed_price: float, profit_or_loss: float) -> None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE trades
                SET closed_at = ?,
                    close_price = ?,
                    profit_or_loss = ?
                WHERE id = ?
                """,
                (closed_at, closed_price, profit_or_loss, trade_id)
            )
            conn.commit()

    def get_all_trades(self) -> list[Trade]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY opened_at DESC")
            rows = cursor.fetchall()
            return [Trade.from_row(row) for row in rows]
