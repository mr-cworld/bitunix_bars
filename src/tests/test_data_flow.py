import sys
from pathlib import Path
import pandas as pd
import logging
import psycopg2

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from database.crypto_db_handler import CryptoDBHandler
from database.indicator_db_handler import IndicatorDBHandler
from config.indicator_db_config import SOURCE_DB_CONFIG, INDICATOR_DB_CONFIG

def setup_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def fetch_sample_data():
    """Fetch a sample of data from the crypto database"""
    db_handler = CryptoDBHandler()
    try:
        db_handler.connect()
        # Modify this query based on your actual table structure
        query = """
            SELECT id, symbol, ts, open, high, low, close 
            FROM arbusdt_1
            WHERE symbol = 'ARBUSDT' 
            ORDER BY ts DESC 
            LIMIT 50
        """
        cursor = db_handler.conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        
        # Convert to DataFrame
        columns = ['id', 'symbol', 'ts', 'open', 'high', 'low', 'close']
        df = pd.DataFrame(data, columns=columns)
        #TODO: Find a smarter way to figure out timeframe
        df['timeframe'] = '1m'
        
        return df
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return None
    finally:
        db_handler.close()

def process_data(df):
    """Perform some sample calculations on the data"""
    if df is not None and not df.empty:
        # Add your calculations here
        df['price_change'] = df['close'] - df['open']
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open']) * 100
        return df
    return None

def save_to_indicator_db(df):
    """Save processed data to the indicator database"""
    if df is not None and not df.empty:
        indicator_db = IndicatorDBHandler(INDICATOR_DB_CONFIG)
        try:
            indicator_db.connect()
            
            # Create test table if it doesn't exist
            cursor = indicator_db.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_indicator_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open DECIMAL NOT NULL,
                    high DECIMAL NOT NULL,
                    low DECIMAL NOT NULL,
                    close DECIMAL NOT NULL,
                    price_change DECIMAL,
                    price_change_pct DECIMAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            indicator_db.conn.commit()
            # Insert data
            for _, row in df.iterrows():
                
                cursor.execute("""
                    INSERT INTO test_indicator_data 
                    (symbol, timeframe, timestamp, open, high, low, close, 
                     price_change, price_change_pct)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['symbol'],
                    row['timeframe'],
                    row['ts'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['price_change'],
                    row['price_change_pct']
                ))
            
            indicator_db.conn.commit()
            logger.info("Test data successfully saved to indicator database")
            
        except Exception as e:
            logger.error(f"Error saving to indicator DB: {e}")
        finally:
            indicator_db.close()

def main():
    # 1. Fetch data
    logger.info("Fetching sample data from crypto database...")
    df = fetch_sample_data()
    
    if df is not None:
        # 2. Display original data
        logger.info("\nOriginal Data:")
        print(df)
        
        # 3. Process data
        logger.info("\nProcessing data...")
        processed_df = process_data(df)
        
        if processed_df is not None:
            # 4. Display processed data
            logger.info("\nProcessed Data:")
            print(processed_df)
            
            # 5. Save to indicator database
            logger.info("\nSaving to indicator database...")
            save_to_indicator_db(processed_df)

if __name__ == "__main__":
    logger = setup_logging()
    main() 