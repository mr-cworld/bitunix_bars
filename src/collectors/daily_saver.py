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
    # Define the list of symbols and timeframes 
    # TODO: Replace hardcoding with configuration or dynamic inputs
    config = TradingConfig()

    symbols = config.get_symbols()
    interval_timeframes = config.get_timeframes()
    #symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ARBUSDT']
    #interval_timeframes = ['15', '30', '60', '240']  # Timeframes in minutes
    date_type = 'Date'
    # Initialize the API client, StorageManager, and CryptoDBHandler
    bitunix_api = ApiBitunix()
    storage_manager = StorageManager()
    db_handler = CryptoDBHandler()


    # Connect to the database
    try:
        db_handler.connect()
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        sys.exit(1)

    # Loop over each symbol and timeframe
    for symbol in symbols:
        for interval in interval_timeframes:
            print(f'Fetching data for {symbol} with interval {interval} minutes.')

            try:
                df = bitunix_api.get_kline_data(symbol=symbol, interval=interval)
                if df is None or df.empty:
                    print(f'No data fetched for {symbol} at interval {interval}.')
                    continue

                # Create clean DataFrame with only required columns
                required_columns = ['symbol', 'ts', 'open', 'high', 'low', 'close']
                df_clean = df[required_columns].copy()

                # Convert 'ts' column to datetime and ensure numeric types
                try:
                    # First convert to datetime with timezone
                    df_clean['ts'] = pd.to_datetime(df_clean['ts'])
                    
                    # Convert to UTC and remove timezone info for PostgreSQL compatibility
                    df_clean['ts'] = df_clean['ts'].dt.tz_convert('UTC').dt.tz_localize(None)
                    
                    df_clean['close'] = pd.to_numeric(df_clean['close'], errors='coerce')
                    df_clean.dropna(subset=['ts', 'close'], inplace=True)

                    # Debug print to verify conversion
                    print(f"DataFrame types after conversion: {df_clean.dtypes}")
                    print(f"Sample timestamp after conversion: {df_clean['ts'].iloc[0]}")

                except Exception as e:
                    logging.error(f"Error converting data types for {symbol} {interval}: {e}")
                    continue

                # Remove the first row if it has bad data
                if len(df_clean) > 1:
                    df_clean = df_clean.iloc[1:].copy()
                    logging.info(f"Removed the first row for {symbol} {interval}")

                # Sort data by timestamp in ascending order
                df_clean = df_clean.sort_values(by='ts', ascending=True).reset_index(drop=True)
                logging.info(f"Sorted data for {symbol} {interval} in ascending order")
                # df has columns: ['symbol', 'open', 'high', 'low', 'close', 'ts']
                # Get the storage path using StorageManager
                path = storage_manager.get_kline_path(
                    date_type='Date',
                    symbol=symbol,
                    timeframe=f'{interval}m'
                )

                # Save files
                parquet_filename = f'{symbol}_{interval}m.parquet'
                csv_filename = f'{symbol}_{interval}m.csv'
                
                parquet_file_path = path / parquet_filename
                df_clean.to_parquet(parquet_file_path, index=False)
                print(f'Data saved to {parquet_file_path}')

                # Optional: Save as CSV
                csv_switch = True  # Toggle CSV saving
                if csv_switch:
                    csv_file_path = path / csv_filename
                    df_clean.to_csv(csv_file_path, index=False)
                    print(f'Data saved to {csv_file_path} as CSV')

                # Database Insertion
                try:
                    db_handler.create_crypto_table(symbol, interval)
                    latest_ts = db_handler.get_latest_timestamp(symbol, interval)
                    
                    if latest_ts:
                        # Convert latest_ts to naive datetime64[ns] by removing timezone
                        latest_ts = latest_ts.tz_localize(None)
                        
                        # Debug prints
                        print(f"Latest timestamp from DB (naive): {latest_ts}")
                        print(f"Sample df timestamp: {df_clean['ts'].iloc[0]}")
                        
                        # Create new DataFrame for filtered data
                        new_data = df_clean[df_clean['ts'] > latest_ts].copy()
                    else:
                        new_data = df_clean.copy()

                    print(f"New data types before insertion: {new_data.dtypes}")
                    print(f"Sample new data timestamp: {new_data['ts'].iloc[0] if not new_data.empty else 'No data'}")

                    if not new_data.empty:
                        db_handler.insert_kline_data(new_data, symbol, interval)
                        
                except Exception as e:
                    logging.error(f"Failed to insert data into database for {symbol} {interval}: {e}")
                    if 'latest_ts' in locals():
                        logging.error(f"Latest timestamp type: {type(latest_ts)}")
                        logging.error(f"Latest timestamp value: {latest_ts}")
                    
            except Exception as e:
                logging.error(f"Failed to fetch data from Bitunix API for {symbol} {interval}: {e}")

    # Close the database connection
    db_handler.close()

if __name__ == '__main__':
    main()
