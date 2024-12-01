import sys
print("Python path:", sys.executable)
print("sys.path:", sys.path)

#TODO: Post Phase 2 Potential update - better optimization with processing bar data for 1m/3m/5m more frequently but could be fine in practice. Wait and see after phase 2.

import os, sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import logging

#internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api_clients.bitunix_api import ApiBitunix
from storage.storage_manager import StorageManager
from database.crypto_db_handler import CryptoDBHandler
from config.trading_config import TradingConfig

#from logging_config import setup_logging

#setup_logging()

def main():
    config = TradingConfig()
    symbols = config.get_symbols()
    
    # Get timeframes directly from trading config
    bitunix_timeframes = config.config['bitunix_timeframes']
    
    # Map Bitunix timeframes to standardized format for storage
    timeframe_mapping = {
        1: '1m', 3: '3m', 5: '5m', 15: '15m', 30: '30m',
        60: '1h', 120: '2h', 240: '4h', 360: '6h', 720: '12h',
        'D': '1d', 'W': '1w', 'M': '1M'
    }
    
    bitunix_api = ApiBitunix()
    storage_manager = StorageManager()
    db_handler = CryptoDBHandler()

    try:
        db_handler.connect()
        
        for symbol in symbols:
            for tf in bitunix_timeframes:
                print(f'Fetching data for {symbol} with interval {tf}')
                
                try:
                    # Convert numeric timeframes to int for mapping
                    tf_key = int(tf) if str(tf).isdigit() else tf
                    
                    # Get data from Bitunix using raw timeframe format
                    df = bitunix_api.get_kline_data(symbol=symbol, interval=tf)
                    logging.debug(f"Raw data from Bitunix: {df.head() if df is not None else None}")
                    if df is None or df.empty:
                        print(f'No data fetched for {symbol} at interval {tf}')
                        continue
                        
                    # Clean and process DataFrame
                    required_columns = ['symbol', 'ts', 'open', 'high', 'low', 'close']
                    df_clean = df[required_columns].copy()
                    
                    # Convert timestamps
                    df_clean['ts'] = pd.to_datetime(df_clean['ts'])
                    df_clean['ts'] = df_clean['ts'].dt.tz_convert('UTC').dt.tz_localize(None)
                    
                    # Convert numeric columns
                    for col in ['open', 'high', 'low', 'close']:
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                    
                    df_clean.dropna(subset=['ts'] + ['open', 'high', 'low', 'close'], inplace=True)
                    
                    # Remove first row if needed and sort
                    if len(df_clean) > 1:
                        df_clean = df_clean.iloc[1:].copy()
                    df_clean = df_clean.sort_values(by='ts', ascending=True).reset_index(drop=True)
                    
                    # Save to storage using mapped timeframe format
                    storage_tf = timeframe_mapping[tf_key]
                    path = storage_manager.get_kline_path(
                        date_type='Date',
                        symbol=symbol,
                        timeframe=storage_tf
                    )
                    
                    # Save files
                    parquet_filename = f'{symbol}_{storage_tf}.parquet'
                    parquet_file_path = path / parquet_filename
                    df_clean.to_parquet(parquet_file_path, index=False)
                    
                    # Optional: Save as CSV
                    csv_switch = True
                    if csv_switch:
                        csv_filename = f'{symbol}_{storage_tf}.csv'
                        csv_file_path = path / csv_filename
                        df_clean.to_csv(csv_file_path, index=False)
                    
                    # Database operations - use raw timeframe for DB operations
                    try:
                        db_handler.create_crypto_table(symbol, tf)  # Use raw timeframe
                        latest_ts = db_handler.get_latest_timestamp(symbol, tf)
                        
                        if latest_ts:
                            latest_ts = latest_ts.tz_localize(None)
                            new_data = df_clean[df_clean['ts'] > latest_ts].copy()
                        else:
                            new_data = df_clean.copy()
                            
                        if not new_data.empty:
                            db_handler.insert_kline_data(new_data, symbol, tf)
                            
                    except Exception as e:
                        logging.error(f"Database error for {symbol} {tf}: {e}")
                        
                except Exception as e:
                    import traceback
                    logging.error(f"Processing error for {symbol} {tf}: {str(e)}")
                    logging.error(f"Full traceback: {traceback.format_exc()}")
                    
    finally:
        db_handler.close()

if __name__ == '__main__':
    main()
