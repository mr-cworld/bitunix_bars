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
            self.create_tables()
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
                    
                    -- Price Data
                    open DECIMAL NOT NULL,
                    high DECIMAL NOT NULL,
                    low DECIMAL NOT NULL,
                    close DECIMAL NOT NULL,
                    price_change DECIMAL,
                    price_change_pct DECIMAL,
                    
                    -- Moving Averages
                    ema_14 DECIMAL,
                    
                    -- Momentum Indicators
                    rsi_14 DECIMAL,
                    roc_12 DECIMAL,
                    momentum_14 DECIMAL,
                    williams_r_14 DECIMAL,
                    
                    -- Volatility Indicators
                    bb_upper DECIMAL,
                    bb_middle DECIMAL,
                    bb_lower DECIMAL,
                    atr_14 DECIMAL,
                    atr_10 DECIMAL,
                    volatility_14 DECIMAL,
                    
                    -- Channel Indicators
                    keltner_upper DECIMAL,
                    keltner_middle DECIMAL,
                    keltner_lower DECIMAL,
                    donchian_upper_20 DECIMAL,
                    donchian_middle_20 DECIMAL,
                    donchian_lower_20 DECIMAL,
                    price_channel_upper_20 DECIMAL,
                    price_channel_middle_20 DECIMAL,
                    price_channel_lower_20 DECIMAL,
                    
                    -- Oscillators
                    stoch_rsi_5 DECIMAL,
                    stoch_rsi_3_k DECIMAL,
                    stoch_rsi_3_d DECIMAL,
                    stoch_rsi_14 DECIMAL,
                    stoch_rsi_14_k DECIMAL,
                    stoch_rsi_14_d DECIMAL,
                    cci_20 DECIMAL,
                    
                    -- Ichimoku Components
                    ichimoku_tenkan DECIMAL,
                    ichimoku_kijun DECIMAL,
                    ichimoku_senkou_a DECIMAL,
                    ichimoku_senkou_b DECIMAL,
                    ichimoku_chikou DECIMAL,
                    
                    -- Pivot Points
                    pivot_standard DECIMAL,
                    r1_standard DECIMAL,
                    r2_standard DECIMAL,
                    r3_standard DECIMAL,
                    s1_standard DECIMAL,
                    s2_standard DECIMAL,
                    s3_standard DECIMAL,
                    
                    -- Fibonacci Levels
                    fib_0_0 DECIMAL,
                    fib_0_236 DECIMAL,
                    fib_0_382 DECIMAL,
                    fib_0_5 DECIMAL,
                    fib_0_618 DECIMAL,
                    fib_0_786 DECIMAL,
                    fib_1_0 DECIMAL,
                    
                    -- Other Indicators
                    psar DECIMAL,
                    psar_trend DECIMAL,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timeframe, timestamp)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_indicator_symbol_time 
                ON indicator_data(symbol, timeframe, timestamp)
            """)
            
            self.conn.commit()
            cursor.close()
            self.logger.info("Indicator tables created successfully.")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to create indicator tables: {e}")
            raise

    def insert_indicator_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """
        Inserts calculated indicator data into the database.
        
        Args:
            df (DataFrame): DataFrame containing all indicator calculations
            symbol (str): Trading pair symbol
            timeframe (str): Timeframe of the data
        """
        try:
            cursor = self.conn.cursor()
            
            # Prepare the column names and placeholders for the SQL query
            columns = list(df.columns)
            placeholders = ', '.join(['%s'] * (len(columns) + 2))  # +2 for symbol and timeframe
            column_names = 'symbol, timeframe, ' + ', '.join(columns)
            
            # Replace dots with underscores in column names for SQL compatibility
            column_names = column_names.replace('.', '_')
            
            for _, row in df.iterrows():
                values = [symbol, timeframe] + [row[col] if col in row else None for col in columns]
                
                insert_query = f"""
                    INSERT INTO indicator_data ({column_names})
                    VALUES ({placeholders})
                    ON CONFLICT (symbol, timeframe, timestamp)
                    DO UPDATE SET
                        {', '.join(f"{col} = EXCLUDED.{col}" for col in columns)}
                """
                
                cursor.execute(insert_query, values)
            
            self.conn.commit()
            cursor.close()
            self.logger.info(f"Indicator data inserted for {symbol} {timeframe}")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to insert indicator data: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Closed connection to indicator database.")

# Ensure the class is properly defined before the end of the file
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
