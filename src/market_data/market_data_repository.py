import sqlite3

import pandas as pd


class MarketDataRepository:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    datetime TEXT NOT NULL,
                    epic TEXT NOT NULL,
                    bid_high REAL,
                    bid_low REAL,
                    bid_open REAL,
                    bid_close REAL,
                    offer_high REAL,
                    offer_low REAL,
                    offer_open REAL,
                    offer_close REAL,
                    close_spread REAL,
                    volume REAL,
                    PRIMARY KEY (datetime, epic)
                )
                """)
            conn.commit()

    def insert_market_data(self, epic: str, candle: dict) -> None:
        query = """
                INSERT INTO market_data (datetime, epic, bid_open, bid_high, bid_low, bid_close, offer_open, offer_high, offer_low, offer_close, close_spread, volume) \
                VALUES (:datetime, :epic, :bid_open, :bid_high, :bid_low, :bid_close, :offer_open, :offer_high, :offer_low, :offer_close, :close_spread, :volume) \
                """

        payload = {"epic": epic, **candle}

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, payload)
            conn.commit()

    def get_market_data(self, epic: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_name) as conn:
            query = "SELECT * FROM market_data WHERE epic = ? ORDER BY datetime ASC"
            return pd.read_sql_query(
                sql=query,
                con=conn,
                params=[epic],
            )

    def get_latest_datetime(self, epic: str) -> str | None:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = "SELECT MAX(datetime) FROM market_data WHERE epic = ?"
            result = cursor.execute(query, (epic,)).fetchone()

            return result[0] if result and result[0] is not None else None
