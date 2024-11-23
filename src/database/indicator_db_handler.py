import psycopg2
import logging
import pandas as pd
from datetime import datetime

__all__ = ['IndicatorDBHandler']  # Explicitly declare what should be exported

class IndicatorDBHandler:
    """
    Handles connections and operations with the indicator PostgreSQL database.
    """

    def __init__(self, db_config):
        """
        Initializes the database handler with connection parameters.
        
        Args:
            db_config (dict): Database connection configuration.
        """
        self.db_config = db_config
        self.conn = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Establishes a connection to the target PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.create_tables()  # Ensure tables exist
            self.logger.info("Connected to the indicator PostgreSQL database.")
        except Exception as e:
            self.logger.error(f"Failed to connect to indicator DB: {e}")
            raise

    def create_tables(self):
        """Creates necessary tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Create table for storing indicator calculations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indicator_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open DECIMAL NOT NULL,
                    high DECIMAL NOT NULL,
                    low DECIMAL NOT NULL,
                    close DECIMAL NOT NULL,
                    price_change DECIMAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_indicator_symbol_time 
                ON indicator_data(symbol, timeframe, timestamp)
            """)
            
            self.conn.commit()
            cursor.close()
            self.logger.info("Tables created successfully.")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to create tables: {e}")
            raise

    def insert_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """
        Inserts processed data into the indicator database.
        
        Args:
            df (DataFrame): The DataFrame containing processed data
            symbol (str): Trading pair symbol
            timeframe (str): Timeframe of the data
        """
        try:
            cursor = self.conn.cursor()
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO indicator_data 
                    (symbol, timeframe, timestamp, open, high, low, close, price_change)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    symbol,
                    timeframe,
                    row['ts'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['price_change']
                ))
            self.conn.commit()
            cursor.close()
            self.logger.info(f"Data inserted for {symbol} {timeframe}")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to insert data: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Closed connection to indicator database.")

# Ensure the class is properly defined before the end of the file
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
