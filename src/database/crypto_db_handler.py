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
import pytz
import numpy as np
import traceback

#from logging_config import setup_logging

#setup_logging()
#OLD LOGGING TODO: FIX LOGGING APP WIDE 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoDBHandler:
    def __init__(self):
        self.config = self._load_config()
        self.trading_config = self._load_trading_config()
        self.conn = None
        self.cur = None

    def _load_config(self) -> dict:
        """Load database configuration from yaml file"""
        config_path = Path(__file__).parent.parent / "config/database_config.yaml"
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    def _load_trading_config(self) -> dict:
        """Load trading configuration from yaml file"""
        trading_config_path = Path(__file__).parent.parent / "config/trading_config.yaml"
        try:
            with open(trading_config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading trading config: {e}")
            raise

    def _validate_timeframe(self, timeframe: str) -> str:
        """Validate timeframe"""
        # Convert timeframe to string if it's an integer
        timeframe = str(timeframe)
        
        # Convert to lowercase and remove underscores
        timeframe = timeframe.lower().replace("_","")

        # Get valid timeframes from trading config
        valid_timeframes = set(str(tf) for tf in self.trading_config.get('bitunix_timeframes', []))
        
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {sorted(valid_timeframes)}")
            
        return timeframe

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
        """Generate table name from symbol and timeframe"""
        # Convert timeframe to string if it's an integer
        timeframe = str(timeframe).lower()
        return f"{symbol}_{timeframe}"

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

    def get_latest_timestamp(self, symbol: str, timeframe: str) -> pd.Timestamp:
        """Get the latest timestamp from the database"""
        table_name = self._get_table_name(symbol, timeframe)
        try:
            query = sql.SQL("SELECT MAX(ts) FROM {}").format(sql.Identifier(table_name))
            self.cur.execute(query)
            result = self.cur.fetchone()[0]
            
            if result:
                # Convert to timezone-aware timestamp
                return pd.Timestamp(result).tz_localize('UTC')
            return None
        except Exception as e:
            logger.error(f"Error getting latest timestamp: {e}")
            raise

    def insert_kline_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> None:
        """Insert kline data into the database"""
        if df.empty:
            logger.info("No data to insert")
            return

        try:
            # Create a clean copy with required columns
            df_clean = df[['symbol', 'ts', 'open', 'high', 'low', 'close']].copy()
            
            # Convert timestamps using the new recommended approach
            df_clean['ts'] = pd.to_datetime(df_clean['ts']).dt.tz_localize(None)
            df_clean['ts'] = np.array(df_clean['ts'])
            
            # Convert numeric columns all at once
            numeric_columns = ['open', 'high', 'low', 'close']
            df_clean[numeric_columns] = df_clean[numeric_columns].apply(pd.to_numeric, errors='coerce')
            
            # Drop any rows with NaN values
            df_clean.dropna(inplace=True)
            
            if df_clean.empty:
                logger.warning(f"No valid data to insert after cleaning for {symbol} {timeframe}")
                return

            # Create values list for insertion
            values = [tuple(x) for x in df_clean.to_numpy()]
            
            # Create the table
            table_name = self._get_table_name(symbol, timeframe)
            
            # Create the INSERT query
            insert_query = sql.SQL(
                "INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING"
            ).format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, ['symbol', 'ts', 'open', 'high', 'low', 'close']))
            )
            
            # Execute the query using execute_values
            execute_values(self.cur, insert_query, values)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(df_clean)} rows into {table_name}")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting data: {e}")
          
            logger.error(f"Full error: {traceback.format_exc()}")
            raise