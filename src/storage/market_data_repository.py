import sqlite3
import pandas as pd

class MarketDataRepository:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp TEXT NOT NULL,
                    epic TEXT NOT NULL,
                    bid_high REAL NOT NULL,
                    bid_low REAL NOT NULL,
                    bid_open REAL NOT NULL,
                    bid_close REAL NOT NULL,
                    ask_high REAL NOT NULL,
                    ask_low REAL NOT NULL,
                    ask_open REAL NOT NULL,
                    ask_close REAL NOT NULL
                )
                """)
            conn.commit()

    def insert_market_data(self, df: pd.DataFrame) -> None:
        """Appends a Pandas DataFrame directly to the market_data table."""
        with sqlite3.connect(self.db_name) as conn:
            df.to_sql(
                name="market_data",
                con=conn,
                if_exists="append",
                index=False,
            )

    def get_market_data(self, epic: str) -> pd.DataFrame:
        """Retrieves market data for a given epic as a Pandas DataFrame sorted chronologically."""
        with sqlite3.connect(self.db_name) as conn:
            query = """
                    SELECT * \
                    FROM market_data
                    WHERE epic = ?
                    ORDER BY timestamp ASC \
                    """
            return pd.read_sql_query(
                sql=query,
                con=conn,
                params=(epic),
            )
