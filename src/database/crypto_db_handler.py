import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import logging
from pathlib import Path
import yaml
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoDBHandler:
    def __init__(self):
        self.config = self._load_config()
        self.conn = None
        self.cur = None

    def _load_config(self) -> dict:
        """Load database configuration from yaml file"""
        config_path = Path("config/database_config.yaml")
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                dbname=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port']
            )
            self.cur = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def _get_table_name(self, symbol: str, timeframe: str) -> str:
        """Generate standardized table name"""
        return f"{symbol}_{timeframe}".lower()

    def create_crypto_table(self, symbol: str, timeframe: str) -> None:
        """Create table for specific crypto and timeframe if it doesn't exist"""
        table_name = self._get_table_name(symbol, timeframe)
        
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                ts TIMESTAMP NOT NULL,
                open NUMERIC(20, 8) NOT NULL,
                high NUMERIC(20, 8) NOT NULL,
                low NUMERIC(20, 8) NOT NULL,
                close NUMERIC(20, 8) NOT NULL,
                UNIQUE(symbol, ts)
            )
        """).format(sql.Identifier(table_name))

        try:
            self.cur.execute(create_table_query)
            
            # Create index on timestamp for faster queries
            index_query = sql.SQL("""
                CREATE INDEX IF NOT EXISTS {}
                ON {} (ts DESC)
            """).format(
                sql.Identifier(f"{table_name}_ts_idx"),
                sql.Identifier(table_name)
            )
            self.cur.execute(index_query)
            
            self.conn.commit()
            logger.info(f"Table {table_name} created/verified successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating table {table_name}: {e}")
            raise

    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """Get the most recent timestamp for a symbol/timeframe"""
        table_name = self._get_table_name(symbol, timeframe)
        
        query = sql.SQL("""
            SELECT MAX(ts) FROM {}
        """).format(sql.Identifier(table_name))
        
        try:
            self.cur.execute(query)
            result = self.cur.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting latest timestamp for {table_name}: {e}")
            return None

    def insert_kline_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> None:
        """Insert kline data while avoiding duplicates"""
        if df.empty:
            logger.info("No data to insert")
            return

        table_name = self._get_table_name(symbol, timeframe)
        
        # Prepare data for insertion
        data_to_insert = [
            (symbol, row.ts, row.open, row.high, row.low, row.close)
            for _, row in df.iterrows()
        ]

        insert_query = sql.SQL("""
            INSERT INTO {} (
                symbol, ts, open, high, low, close
            )
            VALUES %s
            ON CONFLICT (symbol, ts) DO UPDATE
            SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close
        """).format(sql.Identifier(table_name))

        try:
            execute_values(self.cur, insert_query, data_to_insert)
            self.conn.commit()
            logger.info(f"Successfully inserted/updated {len(data_to_insert)} rows for {table_name}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting data into {table_name}: {e}")
            raise

    def get_data_in_range(self, symbol: str, timeframe: str, 
                         start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Retrieve data for a specific time range"""
        table_name = self._get_table_name(symbol, timeframe)
        
        query = sql.SQL("""
            SELECT * FROM {}
            WHERE ts BETWEEN %s AND %s
            ORDER BY ts ASC
        """).format(sql.Identifier(table_name))
        
        try:
            self.cur.execute(query, (start_time, end_time))
            columns = [desc[0] for desc in self.cur.description]
            data = self.cur.fetchall()
            return pd.DataFrame(data, columns=columns)
        except Exception as e:
            logger.error(f"Error retrieving data from {table_name}: {e}")
            return pd.DataFrame() 