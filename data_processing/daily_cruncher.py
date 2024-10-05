import os, sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.storage_manager import StorageManager
from data_processing.indicators import Indicator

# Define the list of symbols and timeframes
# Todo - fix this everywhere
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ARBUSDT']
timeframes = ['15m', '30m', '60m', '240m'] #timeframes with m to match foldernames

def get_todays_date():
    target_date = datetime.now()
    formatted_date = target_date.strftime('%m-%d-%Y')
    return formatted_date

def get_yesterday_date():
    target_date = datetime.now()
    target_date -= timedelta(days=1)
    formatted_date = target_date.strftime('%m-%d-%Y')
    return formatted_date

def main():
    # Initialize the StorageManager
    storage_manager = StorageManager()
    
    # Get the target date
    date = get_todays_date()
    
    # Loop over each symbol and timeframe
    for symbol in symbols:
        for timeframe in timeframes:
            print(f'Processing data for {symbol} with timeframe {timeframe} on date {date}.')
            
            # Construct the path to the stored Parquet file
            kline_path = storage_manager.get_kline_path(
                date_type='Date',
                date=date,
                symbol=symbol,
                timeframe=timeframe
            )
            filename = f'{symbol}_{timeframe}.parquet'
            file_path = kline_path / filename
            
            # Check if the file exists
            if not file_path.exists():
                print(f'File not found: {file_path}')
                continue
            
            # Load the data
            df = pd.read_parquet(file_path)
            
            # Initialize the Indicator object
            indicator = Indicator(df)
            
            # Compute RSI indicators with periods 3, 5, 8, 13, 21
            periods = [3, 5, 8, 13, 21]
            for period in periods:
                df[f'RSI_{period}'] = indicator.rsi(period)
            
            # (Optional) Perform additional data manipulation here
            
            # Get the storage path for processed data
            processed_path = storage_manager.get_processed_path(
                date=date,
                symbol=symbol,
                timeframe=timeframe
            )
            
            # Define the filename
            processed_filename = f'{symbol}_{timeframe}_processed.csv'
            processed_file_path = processed_path / processed_filename
            
            # Save the processed DataFrame as a CSV file
            df.to_csv(processed_file_path, index=False)
            print(f'Processed data saved to {processed_file_path}')

if __name__ == '__main__':
    main()