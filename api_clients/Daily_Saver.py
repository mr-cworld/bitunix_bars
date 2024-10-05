import os, sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api_clients.api_client_bitunix import ApiBitunix
from utils.storage_manager import StorageManager


def main():
    # Define the list of symbols and timeframes 
    # Todo - fix hardcoding
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ARBUSDT']
    interval_timeframes = ['15', '30', '60', '240']  # Timeframes in minutes

    # Initialize the API client and StorageManager
    bitunix_api = ApiBitunix()
    storage_manager = StorageManager()

    # Define the date type [todo- ALWAYS TILL WE HAVE APPENDABLE DBs (ServerSide Feature)]
    date_type = 'Date'

    # Loop over each symbol and timeframe
    for symbol in symbols:
        for interval in interval_timeframes:
            print(f'Fetching data for {symbol} with interval {interval} minutes.')

            # Fetch the Kline data
            try:
                df = bitunix_api.get_kline_data(symbol=symbol, interval=interval)
            except Exception as e:
                print(f'Error fetching data for {symbol} at interval {interval}: {e}')
                continue

            # Convert 'ts' column to datetime
            df['ts'] = pd.to_datetime(df['ts'])
            df['close'] = pd.to_numeric(df['close'])
            
            ###REMOVE 1st Row - has bad data in it
            if len(df) > 1:
                df = df.drop(df.index[0])
                logging.info(f"Removed the second row for {symbol} {interval}")

            # Sort time to be Ascending

            df = df.sort_values(by='ts', ascending=True).reset_index(drop=True)
            logging.info(f"Sorted by Ascending for {symbol} {interval}")

            # (Optional) Perform additional data manipulation here
            # df has columns: ['symbol', 'open', 'high', 'low', 'close', 'volume', 'ts']


            # Get the storage path using StorageManager
            path = storage_manager.get_kline_path(
                date_type=date_type,
                symbol=symbol,
                timeframe=f'{interval}m'  # Append 'm' to indicate minutes
            )

            # Define the filename
            filename = f'{symbol}_{interval}m.parquet'

            # Save the DataFrame as a Parquet file
            file_path = path / filename
            df.to_parquet(file_path, index=False)
            print(f'Data saved to {file_path}')


            #CSV On/Off Switch
            csv_switch = True #True = On, False = Off.
            if csv_switch:
                filename = f'{symbol}_{interval}m.csv'

                file_path = path / filename
                df.to_csv(file_path, index=False)
                print(f'Data saved to {file_path} as CSV')

if __name__ == '__main__':
    main()
