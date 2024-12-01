import logging
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Dict, Optional
import signal
import sys
from pathlib import Path
import pandas as pd

# Add the src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from config.trading_config import TradingConfig
from api_clients.bitunix_api import ApiBitunix
from storage.storage_manager import StorageManager
from database.crypto_db_handler import CryptoDBHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpdateTracker:
    def __init__(self):
        self.last_updates: Dict[str, datetime] = {}
        self.update_counts: Dict[str, int] = {}
        self.errors: Dict[str, tuple] = {}
        
    def should_update(self, symbol: str, interval: str, update_interval: int) -> bool:
        key = f"{symbol}_{interval}"
        last_update = self.last_updates.get(key)
        
        if last_update is None:
            return True
            
        elapsed_minutes = (datetime.now() - last_update).total_seconds() / 60
        return elapsed_minutes >= update_interval
        
    def record_update(self, symbol: str, interval: str):
        key = f"{symbol}_{interval}"
        self.last_updates[key] = datetime.now()
        self.update_counts[key] = self.update_counts.get(key, 0) + 1
        
    def record_error(self, symbol: str, interval: str, error: str):
        key = f"{symbol}_{interval}"
        self.errors[key] = (datetime.now(), error)
        
    def print_stats(self):
        logger.info("\n=== Update Statistics ===")
        for key, count in self.update_counts.items():
            last_update = self.last_updates.get(key, "Never")
            error = self.errors.get(key, (None, None))[1]
            logger.info(f"{key}: Updates: {count}, Last update: {last_update}, Last error: {error}")

class DataCollector:
    def __init__(self):
        self.config = TradingConfig()
        self.bitunix_api = ApiBitunix()
        self.storage_manager = StorageManager()
        self.db_handler = CryptoDBHandler()
        self.tracker = UpdateTracker()
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        logger.info("Received shutdown signal. Cleaning up...")
        self.running = False
        self.tracker.print_stats()
        sys.exit(0)

    def process_symbol_timeframe(self, symbol: str, interval: str, settings: dict):
        try:
            if not self.tracker.should_update(symbol, interval, settings['update_interval']):
                return

            logger.info(f'Starting to process {symbol} with interval {interval}')
            
            # Get data from API and add explicit logging
            logger.info(f'Requesting data from API for {symbol} {interval}')
            klines_data = self.bitunix_api.get_kline_data(symbol.lower(), interval)
            
            if klines_data is None:
                logger.error(f'Received None response from API for {symbol} {interval}')
                return
            if len(klines_data) == 0:
                logger.error(f'Received empty dataset from API for {symbol} {interval}')
                return
            
            logger.info(f'Received {len(klines_data)} records for {symbol} {interval}')
            
            # Clean and prepare the data
            required_columns = ['symbol', 'ts', 'open', 'high', 'low', 'close']
            df_clean = klines_data[required_columns].copy()
            
            # Convert timestamps and ensure proper types
            df_clean['ts'] = pd.to_datetime(df_clean['ts'])
            df_clean['ts'] = df_clean['ts'].dt.tz_convert('UTC').dt.tz_localize(None)
            df_clean['close'] = pd.to_numeric(df_clean['close'], errors='coerce')
            df_clean.dropna(subset=['ts', 'close'], inplace=True)
            
            logger.info(f'Cleaned data for {symbol} {interval}, {len(df_clean)} records remaining')
            
            # Sort by timestamp
            df_clean = df_clean.sort_values(by='ts', ascending=True).reset_index(drop=True)
            
            # Get the current date for storage
            current_date = datetime.now().strftime('%m-%d-%Y')
            
            # Save to filesystem
            storage_path = self.storage_manager.get_kline_path(
                date_type='Date',
                date=current_date,
                symbol=symbol.upper(),
                timeframe=interval
            )
            
            filename = f"{symbol.upper()}_{interval}_{current_date}.csv"
            logger.info(f'Saving {symbol} {interval} to {storage_path / filename}')
            
            self.storage_manager.save_dataframe(
                df=df_clean,
                filename=filename,
                path=storage_path
            )
            
            # Save to database
            logger.info(f'Creating/verifying table for {symbol} {interval}')
            self.db_handler.create_crypto_table(symbol, interval)
            
            # Check latest timestamp in database
            latest_ts = self.db_handler.get_latest_timestamp(symbol, interval)
            logger.info(f'Latest timestamp in DB for {symbol} {interval}: {latest_ts}')
            
            if latest_ts:
                # Convert latest_ts to naive datetime if it's timezone-aware
                latest_ts = latest_ts.tz_localize(None) if latest_ts.tzinfo else latest_ts
                # Only insert data newer than what's in the database
                new_data = df_clean[df_clean['ts'] > latest_ts].copy()
                logger.info(f'Found {len(new_data)} new records for {symbol} {interval}')
            else:
                new_data = df_clean.copy()
                logger.info(f'No existing data found, inserting all {len(new_data)} records for {symbol} {interval}')
                
            if not new_data.empty:
                self.db_handler.insert_kline_data(new_data, symbol, interval)
                logger.info(f"Successfully inserted {len(new_data)} records for {symbol} {interval}")
            else:
                logger.info(f"No new data to insert for {symbol} {interval}")
            
            self.tracker.record_update(symbol, interval)
            logger.info(f'Completed processing {symbol} {interval}')
            
        except Exception as e:
            logger.error(f"Error processing {symbol} {interval}: {e}")
            logger.exception("Full traceback:")
            self.tracker.record_error(symbol, interval, str(e))

    def run(self):
        logger.info("Starting data collector...")
        
        try:
            self.db_handler.connect()
            
            while self.running:
                try:
                    symbols = self.config.get_symbols()
                    timeframes = self.config.get_timeframes()
                    timeframe_config = {
                        tf: {
                            'update_interval': int(tf) if tf.isdigit() else {
                                'D': 1440,  # daily
                                'W': 10080, # weekly
                                'M': 43200  # monthly
                            }.get(tf, 1440)
                        }
                        for tf in timeframes
                    }
                    
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        futures = []
                        for symbol in symbols:
                            for interval, settings in timeframe_config.items():
                                futures.append(
                                    executor.submit(
                                        self.process_symbol_timeframe,
                                        symbol,
                                        interval,
                                        settings
                                    )
                                )
                    
                    # Print stats every hour
                    if datetime.now().minute == 0:
                        self.tracker.print_stats()
                        
                    # Sleep for a short period before next check
                    time.sleep(30)  # Adjust as needed
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(60)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.db_handler.disconnect()
            logger.info("Data collector stopped")

def main():
    collector = DataCollector()
    collector.run()

if __name__ == "__main__":
    main()