import sqlite3
from storage.models import Trade

class SQLiteDb:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    epic TEXT NOT NULL,
                    amount REAL NOT NULL,
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
                INSERT INTO trades (id, epic, amount, opened_at, open_price, comments)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    trade.id,
                    trade.epic,
                    trade.amount,
                    trade.opened_at,
                    trade.open_price,
                    trade.comment,
                )
            )
            conn.commit()

    def update_trade(self, trade: Trade):
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
                (trade.closed_at, trade.close_price, trade.profit_or_loss, trade.id)
            )
            conn.commit()

    def get_all_trades(self) -> list[Trade]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY opened_at DESC")
            rows = cursor.fetchall()
            return [Trade.from_row(row) for row in rows]
