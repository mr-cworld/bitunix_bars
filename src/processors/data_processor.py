import psycopg2
import select
import logging
import pandas as pd
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from database.crypto_db_handler import CryptoDBHandler
from database.indicator_db_handler import IndicatorDBHandler

# Rest of your code remains the same...
class DataProcessor:
    """
    Listens to PostgreSQL notifications, processes data, and saves results to another DB.
    """

    def __init__(self, listen_channel, source_db_config, indicator_db_config):
        self.listen_channel = listen_channel
        self.source_conn = psycopg2.connect(**source_db_config)
        self.source_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.indicator_db = IndicatorDBHandler(indicator_db_config)
        self.logger = logging.getLogger(__name__)

    def listen(self):
        """Starts listening to the specified PostgreSQL channel."""
        cursor = self.source_conn.cursor()
        cursor.execute(f"LISTEN {self.listen_channel};")
        self.logger.info(f"Listening to channel '{self.listen_channel}'")

        try:
            while True:
                if select.select([self.source_conn], [], [], 5) == ([], [], []):
                    continue
                self.source_conn.poll()
                while self.source_conn.notifies:
                    notify = self.source_conn.notifies.pop(0)
                    self.logger.info(f"Received NOTIFY: {notify.payload}")
                    self.handle_notification(notify.payload)
        except KeyboardInterrupt:
            self.logger.info("Stopping listener.")
        finally:
            cursor.close()
            self.source_conn.close()

    def handle_notification(self, payload):
        """
        Handles the notification by fetching data, processing it, and saving results.
        
        Args:
            payload (str): The payload sent with the NOTIFY.
        """
        self.logger.info(f"Handling notification with payload: {payload}")
        data = self.fetch_data(payload)
        if data is not None:
            df = self.save_data_to_dataframe(data)
            processed_df = self.perform_calculations(df)
            self.save_to_target_db(processed_df)

    def fetch_data(self, identifier):
        """
        Fetches data from the source database based on the notification payload.
        
        Args:
            identifier (str): Identifier to fetch specific data.
        
        Returns:
            list of tuples: Retrieved data.
        """
        db_handler = CryptoDBHandler()
        try:
            db_handler.connect()
            data = db_handler.fetch_data(identifier)
            db_handler.close()
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data: {e}")
            return None

    def save_data_to_dataframe(self, data):
        """
        Converts fetched data to a pandas DataFrame.
        
        Args:
            data (list of tuples): Data fetched from the database.
        
        Returns:
            DataFrame: Pandas DataFrame containing the data.
        """
        try:
            df = pd.DataFrame(data, columns=['column1', 'column2', 'ts', 'open', 'high', 'low', 'close'])
            self.logger.info("Data converted to DataFrame.")
            return df
        except Exception as e:
            self.logger.error(f"Error converting data to DataFrame: {e}")
            return pd.DataFrame()

    def perform_calculations(self, df):
        """
        Performs simple calculations on the DataFrame.
        
        Args:
            df (DataFrame): The DataFrame to process.
        
        Returns:
            DataFrame: Processed DataFrame with new calculations.
        """
        try:
            df['price_change'] = df['close'] - df['open']
            self.logger.info("Performed price change calculation.")
            return df
        except Exception as e:
            self.logger.error(f"Error performing calculations: {e}")
            return df

    def save_to_target_db(self, df):
        """
        Saves the processed DataFrame to the indicator PostgreSQL database.
        
        Args:
            df (DataFrame): The DataFrame to save.
        """
        try:
            self.indicator_db.connect()
            symbol = 'BTCUSDT'
            timeframe = '1m'
            self.indicator_db.insert_data(df, symbol, timeframe)
            self.indicator_db.close()
            self.logger.info("Processed data saved to indicator database.")
        except Exception as e:
            self.logger.error(f"Error saving data to indicator DB: {e}")