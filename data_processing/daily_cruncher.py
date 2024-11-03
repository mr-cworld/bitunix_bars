import os, sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import logging
from multiprocessing import Pool



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.storage_manager import StorageManager
from data_processing.indicators import Indicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def process_symbol_timeframe(args):
    symbol, timeframe = args
    # Initialize the StorageManager
    storage_manager = StorageManager()
    
    # Get the target date
    date = get_todays_date()
    
    logger.info(f'Processing data for {symbol} with timeframe {timeframe} on date {date}.')
    
    # Construct the path to the stored Parquet file
    kline_path = Path(storage_manager.get_kline_path(
        date_type='Date',
        date=date,
        symbol=symbol,
        timeframe=timeframe
    ))
    filename = f'{symbol}_{timeframe}.parquet'
    file_path = kline_path / filename
    
    # Check if the file exists
    if not file_path.exists():
        logger.info(f'File not found: {file_path}')
        return
    
    try:
        # Load the data
        df = pd.read_parquet(file_path)
        # Initialize the Indicator object
        indicator = Indicator(df)
    except Exception as e:
        logger.info(f'Error loading data from {file_path}: {e}')
        return

    # Compute RSI indicators with periods 3, 5, 8, 13, 21
    periods = [3, 5, 8, 13, 21]
    for period in periods:
        df[f'RSI_{period}'] = indicator.rsi(period)
    
    # Weighted Moving Average
    # Todo - naming upgrade, if i enter WMA_20 i need column name below 'WMA_10' to reflect that
    df[f'WMA_10'] = indicator.wma(window=10)
    #wma_10 = indicator.wma(window=10)
    #indicator.add_indicator('WMA10', wma_10)

    # Hull Moving Average
    df[f'HMA_20'] = indicator.hma(window=20)
    #hma_20 = indicator.hma(window=20)
    #indicator.add_indicator('HMA20', hma_20)

    
    
    ma, upper_env, lower_env = indicator.moving_average_envelopes(window=20, percentage=0.02, ma_type='ema')
    #indicator.add_indicator('EMA20', ma)
    #indicator.add_indicator('UpperEnvelope', upper_env)
    #indicator.add_indicator('LowerEnvelope', lower_env)

    # Moving Average Envelopes
    df[f'EMA20'] = ma
    df[f'UpperEnvelope'] = upper_env
    df[f'LowerEnvelope'] = lower_env


    # Stochastic RSI
    stoch_rsi_df = indicator.stocastic_rsi(periods=14, smooth_k=3, smooth_d=3)
    df[f'Stoch_RSI_%K'] = stoch_rsi_df['StochRSI_%K']
    df[f'Stoch_RSI_%D'] = stoch_rsi_df['StochRSI_%D']

    #indicator.add_indicator('StochRSI_%K', stoch_rsi_df['StochRSI_%K'])
    #indicator.add_indicator('StochRSI_%D', stoch_rsi_df['StochRSI_%D'])


    # (Optional) Perform additional data manipulation here
    
    # Get the storage path for processed data
    processed_path = storage_manager.get_processed_path(
        date=date,
        symbol=symbol,
        timeframe=timeframe
    )
    
    # Define the filename
    #todo - do i want to add the indicator name to the processed? so RSI, EMA, etc have different files, or just one mega one?
    processed_filename = f'{symbol}_{timeframe}'
    processed_file_path = processed_path / f'{processed_filename}_processed.csv'
    processed_file_path_parquet = processed_path / f'{processed_filename}.parquet'
    
    # Save the processed DataFrame as a CSV file
    df.to_csv(processed_file_path, index=False)
    df.to_parquet(processed_file_path_parquet, index=False)
    logger.info(f'Processed data saved to {processed_file_path}')

def main():
    with Pool() as pool:
        pool.map(process_symbol_timeframe, [(s, t) for s in symbols for t in timeframes])

if __name__ == '__main__':
    main()