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
                    ask_high REAL,
                    ask_low REAL,
                    ask_open REAL,
                    ask_close REAL,
                    PRIMARY KEY (datetime, epic)
                )
                """)
            conn.commit()

    def insert_market_data(self, df: pd.DataFrame) -> None:
        with sqlite3.connect(self.db_name) as conn:
            df.to_sql(
                name="market_data",
                con=conn,
                if_exists="append",
                index=False,
            )

    def get_market_data(self, epic: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_name) as conn:
            query = "SELECT * FROM market_data WHERE epic = ? ORDER BY datetime ASC"
            return pd.read_sql_query(
                sql=query,
                con=conn,
                params=[epic],
            )
