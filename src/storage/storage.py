import sqlite3

db_name = "aitrader.db"


class Storage():
    def __init__(self):
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id TEXT PRIMARY KEY,
                    epic TEXT NOT NULL,
                    amount REAL NOT NULL,
                    opened_at TEXT NOT NULL,
                    open_price REAL NOT NULL,
                    closed_at TEXT,
                    close_price REAL,
                    profit_or_loss REAL,
                    comments TEXT NOT NULL
                )
                """)
            conn.commit()

    def save_open_trade(self, id: str, epic: str, amount: float, opened_at: str, open_price: float, comment: str):
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trade_history (id, epic, amount, opened_at, open_price, comments) VALUES (?, ?, ?, ?, ?, ?)",
                (id, epic, amount, opened_at, open_price, comment)
            )
            conn.commit()

    def save_trade_as_closed(self, id: str, closed_at: str, close_price: float, profit_or_loss: float):
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE trade_history
                SET closed_at = ?,
                    close_price = ?,
                    profit_or_loss = ?
                WHERE id = ?
                """,
                (closed_at, close_price, profit_or_loss, id)
            )
            conn.commit()

    def get_all_trades(self) -> list[dict]:
        with sqlite3.connect(db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trade_history ORDER BY opened_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
