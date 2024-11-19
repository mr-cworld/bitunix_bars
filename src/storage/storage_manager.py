import os
from datetime import datetime
from pathlib import Path
import logging
import pandas as pd

class StorageManager:
    """
    A class to manage storage of data files, organizing them into a directory.
    """

    def __init__(self, base_path='storage'):
        """
        Initializes the StorageManager with a base_path

        Args:
            base_path (str): The base directory for storing files.
        """

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def get_kline_path(self, date_type=None, date=None, symbol=None, timeframe=None):
        #todo - switch this date(str) to be in YYYY-MM-DD format
        #bring in a global list of symbols to parse for - 
        """
        Constructs the directory path for Kline data

        Args:
            date_type (str): 'Date' or 'Historical' folder
            date(str): The date string in MM-DD-YYYY format
            symbol (str): The trading symbol, e.g. 'BTCUSDT'
            timeframe (str): The timeframe, '1', '3', M

        Returns:
            Path: the full directory path
        """
        if date_type == 'Date':
            path = self.base_path / 'Kline' / 'Date'
            if date is None:
                date = datetime.now().strftime('%m-%d-%Y')
            path = path / date

        elif date_type == 'Historical':
            path = self.base_path / 'Kline' / 'Historical'
        else:
            raise ValueError('date_type must be "Date" or "Historical (Line 47 of storage_manager.py)')
        
        if symbol:
            path = path / symbol
        if timeframe:
            path = path / timeframe

        path.mkdir(parents=True, exist_ok=True)
        return path
    




    def get_indicator_path(self, date=None, symbol=None, timeframe=None):
        """
        Constructs the directory path for Indicator object data
        
        Args:
            date(str): The date string in 'MM-DD-YYYY' format
            symbol (str): The trading symbol
            timeframe (str): The timeframe

        Returns:
            Path: the full directory path
        """

        path = self.base_path / 'Indicator'

        if date is None:
            date = datetime.now().strftime('%m-%d-%Y')
        path = path / date 
        
        if symbol:
            path = path / symbol
        if timeframe:
            path = path / timeframe

        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def save_dataframe(self, df, filename, path):
        """
        Saves a DataFrame to a CSV File.

        Args:
            df (DataFrame): The DataFrame to save.
            filename (str): The name of the file
            path (Path): The directory path where the file will be saved
        """

        file_path = path/filename
        df.to_csv(file_path, index=False)
        self.logger.info(f"Data saved to {file_path}")
    
    def save_figure(self, fig, filename, path):
        """
        Saves a Matplotlib figure.

        Args:
            fig (Figure): The Matplotlib figure to save.
            filename(str): The name of the file
            path (Path): The directory path where the file will be saved.
        """
        file_path = path / filename
        fig.savefig(file_path)
        self.logger.info(f"Figure saved to {file_path}")


    def load_dataframe(self,filename,path):
        """
        Loads a DataFrame from a CSV file.

        Args:
            filename (str): The name of the file.
            path(Path): The directory path where the file is located

        Returns:
            DataFrame: The loaded DataFrame.
        """
        file_path = path / filename
        if file_path.exists():
            df = pd.read_csv(file_path)
            self.logger.info(f"Data loaded from {file_path}")
            return df
        else:
            self.logger.error(f"File not found: {file_path}")
            return None

    def get_processed_path(self, date=None, symbol=None, timeframe=None):
        """
        Constructs the directory path for processed data
        
        Args:
            date (str): The date string in 'MM-DD-YYYY' format
            symbol (str): the trading symbol
            timeframe (str): The TimeFrame
        
        Returns:
            Path: The full directory
        """
        path = self.base_path / 'processed'

        if date is None:
            date = datetime.now().strftime('%m-%d-%Y')

        if date:
            path=path/date

        if symbol:
            path = path / symbol
        
        if timeframe:
            path = path / timeframe

        path.mkdir(parents=True, exist_ok=True)
        return path