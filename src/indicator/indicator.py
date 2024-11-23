import pandas as pd
import numpy as np
from typing import Optional, Union, List
import logging

class Indicator:
    """
    A class to handle various technical indicators for cryptocurrency data.
    
    Attributes:
        df (pd.DataFrame): The input DataFrame containing OHLCV data
        symbol (str): The trading pair symbol (e.g., 'ARBUSDT')
        timeframe (str): The timeframe of the data (e.g., '1m', '3m', '5m')
        available_timeframes (List[str]): List of valid timeframes
    """

    def __init__(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """
        Initialize the Indicator object with a DataFrame and metadata.

        Args:
            df (pd.DataFrame): DataFrame containing columns: timestamp, open, high, low, close, volume
            symbol (str): Trading pair symbol (e.g., 'ARBUSDT')
            timeframe (str): Timeframe of the data (e.g., '1m', '3m', '5m')
        """
        self.available_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        
        # Validate timeframe
        if timeframe not in self.available_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of {self.available_timeframes}")

        # Initialize basic attributes
        self.df = df.copy()  # Create a copy to avoid modifying original data
        self.symbol = symbol
        self.timeframe = timeframe
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Validate DataFrame structure
        self._validate_dataframe()
        
        # Initialize the DataFrame with basic calculations
        self._initialize_calculations()

    def _validate_dataframe(self) -> None:
        """Validate that the DataFrame has the required columns."""
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            raise ValueError(f"DataFrame missing required columns: {missing_columns}")

    def _initialize_calculations(self) -> None:
        """Initialize basic calculations and ensure DataFrame is properly sorted."""
        # Sort DataFrame by timestamp
        self.df = self.df.sort_values('timestamp')
        
        # Add basic calculations
        self.df['price_change'] = self.df['close'] - self.df['open']
        self.df['price_change_pct'] = self.df['price_change'] / self.df['open'] * 100

    def ema(self, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            period (int): The period for EMA calculation
            column (str): The column to calculate EMA for

        Returns:
            pd.Series: EMA values
        """
        try:
            ema_values = self.df[column].ewm(span=period, adjust=False).mean()
            self.df[f'ema_{period}'] = ema_values
            return ema_values
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return pd.Series()

    def sma(self, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            period (int): The period for SMA calculation
            column (str): The column to calculate SMA for

        Returns:
            pd.Series: SMA values
        """
        try:
            sma_values = self.df[column].rolling(window=period).mean()
            self.df[f'sma_{period}'] = sma_values
            return sma_values
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            return pd.Series()

    def rsi(self, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            period (int): The period for RSI calculation

        Returns:
            pd.Series: RSI values
        """
        try:
            # Calculate price changes
            delta = self.df['close'].diff()
            
            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = gain / loss
            rsi_values = 100 - (100 / (1 + rs))
            
            self.df[f'rsi_{period}'] = rsi_values
            return rsi_values
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series()

    def macd(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            fast_period (int): The period for the fast EMA
            slow_period (int): The period for the slow EMA
            signal_period (int): The period for the signal line

        Returns:
            tuple: (MACD line, Signal line, MACD histogram)
        """
        try:
            # Calculate MACD line
            fast_ema = self.df['close'].ewm(span=fast_period, adjust=False).mean()
            slow_ema = self.df['close'].ewm(span=slow_period, adjust=False).mean()
            macd_line = fast_ema - slow_ema
            
            # Calculate Signal line
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            
            # Calculate MACD histogram
            macd_histogram = macd_line - signal_line
            
            # Store in DataFrame
            self.df['macd_line'] = macd_line
            self.df['macd_signal'] = signal_line
            self.df['macd_histogram'] = macd_histogram
            
            return macd_line, signal_line, macd_histogram
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    def bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> tuple:
        """
        Calculate Bollinger Bands.

        Args:
            period (int): The period for the moving average
            std_dev (float): Number of standard deviations for the bands

        Returns:
            tuple: (Upper band, Middle band, Lower band)
        """
        try:
            middle_band = self.df['close'].rolling(window=period).mean()
            rolling_std = self.df['close'].rolling(window=period).std()
            
            upper_band = middle_band + (rolling_std * std_dev)
            lower_band = middle_band - (rolling_std * std_dev)
            
            self.df['bb_upper'] = upper_band
            self.df['bb_middle'] = middle_band
            self.df['bb_lower'] = lower_band
            
            return upper_band, middle_band, lower_band
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    def get_dataframe(self) -> pd.DataFrame:
        """Return the DataFrame with all calculated indicators."""
        return self.df.copy()

    def get_latest_indicators(self) -> dict:
        """Return the most recent values for all calculated indicators."""
        return self.df.iloc[-1].to_dict()

# Example usage
if __name__ == "__main__":
    # Create sample data
    data = {
        'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='1min'),
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 101,
        'volume': np.random.randn(100).cumsum() + 1000
    }
    df = pd.DataFrame(data)
    
    # Create indicator instance
    arb_1m = Indicator(df, symbol='ARBUSDT', timeframe='1m')
    
    # Calculate some indicators
    arb_1m.ema(period=14)
    arb_1m.rsi(period=14)
    arb_1m.bollinger_bands()
    
    # Get the results
    print(arb_1m.get_latest_indicators()),

    