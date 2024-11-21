from crypto_db_handler import CryptoDBHandler
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_crypto_db():
    db = CryptoDBHandler()
    
    try:
        # Connect to database
        db.connect()
        
        # Test symbol and timeframe
        symbol = "BTCUSDT"
        timeframe = "15m"
        
        # Create table
        db.create_crypto_table(symbol, timeframe)
        
        # Create some test data
        test_data = pd.DataFrame({
            'ts': [datetime.now() - timedelta(minutes=i*15) for i in range(5)],
            'open': [50000.0 + i for i in range(5)],
            'high': [51000.0 + i for i in range(5)],
            'low': [49000.0 + i for i in range(5)],
            'close': [50500.0 + i for i in range(5)]
        })
        
        # Test initial insertion
        logger.info("Testing initial data insertion...")
        db.insert_kline_data(test_data, symbol, timeframe)
        
        # Test duplicate handling by inserting overlapping data with different values
        modified_data = test_data.copy()
        modified_data['close'] = modified_data['close'] + 100  # Modify some values
        logger.info("Testing duplicate handling...")
        db.insert_kline_data(modified_data, symbol, timeframe)
        
        # Get latest timestamp
        latest_ts = db.get_latest_timestamp(symbol, timeframe)
        logger.info(f"Latest timestamp: {latest_ts}")
        
        # Retrieve and verify data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        df = db.get_data_in_range(symbol, timeframe, start_time, end_time)
        logger.info(f"Retrieved {len(df)} rows of data")
        logger.info("\nSample of retrieved data:")
        logger.info(df.head())
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_crypto_db() 