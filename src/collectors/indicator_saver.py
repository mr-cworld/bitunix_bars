import os
import sys
import select
import psycopg2
import pandas as pd
import logging
from datetime import datetime

# Internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indicator.indicator import Indicator
from database.indicator_db_handler import IndicatorDBHandler
from database.crypto_db_handler import CryptoDBHandler
from config.trading_config import TradingConfig

class IndicatorSaver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = TradingConfig()
        
        # Initialize database handlers
        self.crypto_db = CryptoDBHandler()
        self.indicator_db = IndicatorDBHandler(self.config.get_indicator_db_config())
        
        # Connect to both databases
        self.crypto_db.connect()
        self.indicator_db.connect()
        
        # Set up LISTEN on crypto database
        self.setup_notification_listener()

    def setup_notification_listener(self):
        """Set up LISTEN for notifications from bitunix database"""
        try:
            cursor = self.crypto_db.conn.cursor()
            cursor.execute("LISTEN new_kline_data;")
            self.logger.info("Successfully set up LISTEN for new_kline_data notifications")
        except Exception as e:
            self.logger.error(f"Failed to set up notification listener: {e}")
            raise

    def fetch_latest_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Fetch the latest data for a symbol/timeframe pair"""
        try:
            query = f"""
                SELECT timestamp as ts, open, high, low, close, volume
                FROM bitunix_kline_data
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            df = pd.read_sql_query(
                query,
                self.crypto_db.conn,
                params=(symbol, timeframe, limit),
                parse_dates=['ts']
            )
            
            return df.sort_values('ts')
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """Calculate all indicators for the given data"""
        try:
            # Initialize indicator calculator
            indicator = Indicator(df, symbol=symbol, timeframe=timeframe)
            
            # Calculate all indicators
            indicator.ema(period=14)
            indicator.rsi(period=14)
            indicator.bollinger_bands()
            indicator.stoch_rsi()
            indicator.stoch_rsi(period=5, smooth_k=3, smooth_d=3)
            indicator.atr(period=14)
            indicator.atr(period=10)
            indicator.cci(period=20)
            indicator.ichimoku()
            indicator.fibonacci_retracement()
            indicator.roc(period=12)
            indicator.momentum(period=14)
            indicator.keltner_channels()
            indicator.volatility(period=14)
            indicator.price_channels(period=20)
            indicator.pivot_points()
            indicator.parabolic_sar()
            indicator.donchian_channels(period=20)
            indicator.williams_r(period=14)
            
            return indicator.get_dataframe()
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol} {timeframe}: {e}")
            return pd.DataFrame()

    def process_notification(self, notification):
        """Process a notification from the crypto database"""
        try:
            # Parse notification payload
            payload = notification.payload
            if not payload:
                return
            
            # Extract symbol and timeframe from payload
            data = eval(payload)  # Be careful with eval - ensure payload is trusted
            symbol = data.get('symbol')
            timeframe = data.get('timeframe')
            
            if not symbol or not timeframe:
                self.logger.error("Invalid notification payload")
                return
            
            # Fetch latest data
            df = self.fetch_latest_data(symbol, timeframe)
            if df.empty:
                self.logger.error(f"No data found for {symbol} {timeframe}")
                return
            
            # Calculate indicators
            indicator_df = self.calculate_indicators(df, symbol, timeframe)
            if indicator_df.empty:
                self.logger.error(f"Failed to calculate indicators for {symbol} {timeframe}")
                return
            
            # Save to indicator database
            self.indicator_db.insert_indicator_data(indicator_df, symbol, timeframe)
            self.logger.info(f"Successfully processed and saved indicators for {symbol} {timeframe}")
            
        except Exception as e:
            self.logger.error(f"Error processing notification: {e}")

    def run(self):
        """Main loop to listen for notifications"""
        try:
            self.logger.info("Starting indicator saver service...")
            
            while True:
                # Wait for notifications
                if select.select([self.crypto_db.conn], [], [], 5) == ([], [], []):
                    continue
                
                self.crypto_db.conn.poll()
                while self.crypto_db.conn.notifies:
                    notification = self.crypto_db.conn.notifies.pop()
                    self.logger.info(f"Received notification: {notification.payload}")
                    self.process_notification(notification)
                    
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up database connections"""
        try:
            self.crypto_db.close()
            self.indicator_db.close()
            self.logger.info("Cleaned up database connections")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    saver = IndicatorSaver()
    try:
        saver.run()
    except KeyboardInterrupt:
        logging.info("Shutting down indicator saver service...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        saver.cleanup()

if __name__ == "__main__":
    main()