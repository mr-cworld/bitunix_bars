#this file will use pandas and mathplot lib to start plotting the data, and saving the csv. 

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.storage_manager import StorageManager

# initialize the storage manager
storage_manager = StorageManager()

# Define the list of symbols and timeframes
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ARBUSDT']
timeframes = ['15m', '30m', '60m', '240m']

# Get the target date
date = datetime.now().strftime('%m-%d-%Y')

# Loop over each symbol and timeframe

for symbol in symbols:
    for timeframe in timeframes:
        # Construct the path to the stored Parquet file

        processed_data_path = Path(storage_manager.get_processed_path(
            date_type='Date',
            date=date,
            symbol=symbol,
            timeframe=timeframe
        ))

        kline_path = Path(storage_manager.get_kline_path(
            date_type='Date',
            date=date,
            symbol=symbol,
            timeframe=timeframe
        ))
        filename = f'{symbol}_{timeframe}.parquet'
        processed_file_path = processed_data_path / filename

        # Check if the file exists
        if not  processed_file_path.exists():
            print(f'File not found: { processed_file_path }')
            continue

        # Load the data
        df = pd.read_parquet( processed_file_path )

        # Plot the data
        plt.plot(df['ts'], df['close'])
        plt.title(f'{symbol} {timeframe} Close Prices')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot
        plot_path = processed_file_path / f'{symbol}_{timeframe}_plot.png'
        plt.savefig(plot_path)
        print(f'Plot saved to {plot_path}')

        # Show the plot
        plt.show()
        plt.close()