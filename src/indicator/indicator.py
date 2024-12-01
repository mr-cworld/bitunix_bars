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
        required_columns = ['ts', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            raise ValueError(f"DataFrame missing required columns: {missing_columns}")

    def _initialize_calculations(self) -> None:
        """Initialize basic calculations and ensure DataFrame is properly sorted."""
        # Sort DataFrame by timestamp
        self.df = self.df.sort_values('ts')
        
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

    def stoch_rsi(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> tuple:
        """
        Calculate Stochastic RSI.
        
        Args:
            period (int): The period for RSI calculation
            smooth_k (int): Smoothing for %K line
            smooth_d (int): Smoothing for %D line
        
        Returns:
            tuple: (Stochastic RSI, %K line, %D line)
        """
        try:
            # First calculate RSI
            if f'rsi_{period}' not in self.df.columns:
                self.rsi(period=period)
            
            # Get RSI values
            rsi_values = self.df[f'rsi_{period}']
            
            # Calculate Stochastic RSI
            rsi_min = rsi_values.rolling(window=period).min()
            rsi_max = rsi_values.rolling(window=period).max()
            
            stoch_rsi = 100 * (rsi_values - rsi_min) / (rsi_max - rsi_min)
            
            # Calculate K and D lines
            k_line = stoch_rsi.rolling(window=smooth_k).mean()
            d_line = k_line.rolling(window=smooth_d).mean()
            
            # Store in DataFrame
            self.df['stoch_rsi'] = stoch_rsi
            self.df['stoch_k'] = k_line
            self.df['stoch_d'] = d_line
            
            # Debug logging
            self.logger.info(f"Stoch RSI calculation completed with {len(rsi_values)} values")
            self.logger.info(f"Last values - RSI: {rsi_values.iloc[-1]:.4f}, "
                            f"Stoch RSI: {stoch_rsi.iloc[-1]:.4f}, "
                            f"K: {k_line.iloc[-1]:.4f}, "
                            f"D: {d_line.iloc[-1]:.4f}")
            
            return stoch_rsi, k_line, d_line
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic RSI: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    def atr(self, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR).

        Args:
            period (int): The period for ATR calculation

        Returns:
            pd.Series: ATR values
        """
        try:
            high = self.df['high']
            low = self.df['low']
            close = self.df['close']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR
            atr_values = tr.ewm(span=period, adjust=False).mean()
            
            self.df['atr'] = atr_values
            return atr_values
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return pd.Series()

    def cci(self, period: int = 20) -> pd.Series:
        """
        Calculate Commodity Channel Index (CCI).
        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)

        Args:
            period (int): The period for CCI calculation

        Returns:
            pd.Series: CCI values
        """
        try:
            # Calculate Typical Price
            tp = (self.df['high'] + self.df['low'] + self.df['close']) / 3
            
            # Calculate SMA of Typical Price
            tp_sma = tp.rolling(window=period).mean()
            
            # Calculate Mean Deviation
            # First, calculate absolute deviations from SMA
            def mad(x):
                return np.abs(x - x.mean()).mean()
            
            mean_deviation = tp.rolling(window=period).apply(mad)
            
            # Calculate CCI
            cci_values = (tp - tp_sma) / (0.015 * mean_deviation)
            
            # Store in DataFrame
            self.df[f'cci_{period}'] = cci_values
            
            return cci_values
            
        except Exception as e:
            self.logger.error(f"Error calculating CCI: {e}")
            return pd.Series()

    def ichimoku(self, tenkan_period: int = 9, kijun_period: int = 26, 
                 senkou_b_period: int = 52, displacement: int = 26) -> tuple:
        """
        Calculate Ichimoku Cloud components.

        Args:
            tenkan_period (int): Period for Tenkan-sen (Conversion Line)
            kijun_period (int): Period for Kijun-sen (Base Line)
            senkou_b_period (int): Period for Senkou Span B
            displacement (int): Displacement period for Senkou Span A/B

        Returns:
            tuple: (Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span)
        """
        try:
            # Calculate Tenkan-sen (Conversion Line)
            tenkan_high = self.df['high'].rolling(window=tenkan_period).max()
            tenkan_low = self.df['low'].rolling(window=tenkan_period).min()
            tenkan_sen = (tenkan_high + tenkan_low) / 2

            # Calculate Kijun-sen (Base Line)
            kijun_high = self.df['high'].rolling(window=kijun_period).max()
            kijun_low = self.df['low'].rolling(window=kijun_period).min()
            kijun_sen = (kijun_high + kijun_low) / 2

            # Calculate Senkou Span A (Leading Span A)
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)

            # Calculate Senkou Span B (Leading Span B)
            senkou_high = self.df['high'].rolling(window=senkou_b_period).max()
            senkou_low = self.df['low'].rolling(window=senkou_b_period).min()
            senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)

            # Calculate Chikou Span (Lagging Span)
            chikou_span = self.df['close'].shift(-displacement)

            # Store in DataFrame
            self.df['ichimoku_tenkan'] = tenkan_sen
            self.df['ichimoku_kijun'] = kijun_sen
            self.df['ichimoku_senkou_a'] = senkou_span_a
            self.df['ichimoku_senkou_b'] = senkou_span_b
            self.df['ichimoku_chikou'] = chikou_span

            return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
        except Exception as e:
            self.logger.error(f"Error calculating Ichimoku Cloud: {e}")
            return pd.Series(), pd.Series(), pd.Series(), pd.Series(), pd.Series()

    def fibonacci_retracement(self, start_price: float = None, end_price: float = None) -> dict:
        """
        Calculate Fibonacci Retracement levels.

        Args:
            start_price (float): Starting price for retracement (default: first price)
            end_price (float): Ending price for retracement (default: last price)

        Returns:
            dict: Fibonacci retracement levels
        """
        try:
            if start_price is None:
                start_price = self.df['close'].iloc[0]
            if end_price is None:
                end_price = self.df['close'].iloc[-1]

            price_diff = end_price - start_price
            
            # Calculate Fibonacci levels
            levels = {
                '0.0': start_price,
                '0.236': end_price - (price_diff * 0.236),
                '0.382': end_price - (price_diff * 0.382),
                '0.5': end_price - (price_diff * 0.5),
                '0.618': end_price - (price_diff * 0.618),
                '0.786': end_price - (price_diff * 0.786),
                '1.0': end_price
            }
            
            # Store in DataFrame as columns
            for level, value in levels.items():
                self.df[f'fib_{level}'] = value
            
            return levels
        except Exception as e:
            self.logger.error(f"Error calculating Fibonacci Retracement: {e}")
            return {}

    def get_dataframe(self) -> pd.DataFrame:
        """Return the DataFrame with all calculated indicators."""
        return self.df.copy()

    def get_latest_indicators(self) -> dict:
        """Return the most recent values for all calculated indicators."""
        return self.df.iloc[-1].to_dict()

    def roc(self, period: int = 12) -> pd.Series:
        """
        Calculate Rate of Change (ROC).
        ROC = ((Current Price - Price n periods ago) / Price n periods ago) * 100

        Args:
            period (int): The period for ROC calculation

        Returns:
            pd.Series: ROC values
        """
        try:
            roc_values = ((self.df['close'] - self.df['close'].shift(period)) / 
                         self.df['close'].shift(period)) * 100
            
            self.df[f'roc_{period}'] = roc_values
            return roc_values
        except Exception as e:
            self.logger.error(f"Error calculating ROC: {e}")
            return pd.Series()

    def momentum(self, period: int = 14) -> pd.Series:
        """
        Calculate Momentum Indicator.
        Momentum = Current Price - Price n periods ago

        Args:
            period (int): The period for momentum calculation

        Returns:
            pd.Series: Momentum values
        """
        try:
            momentum_values = self.df['close'] - self.df['close'].shift(period)
            
            self.df[f'momentum_{period}'] = momentum_values
            return momentum_values
        except Exception as e:
            self.logger.error(f"Error calculating Momentum: {e}")
            return pd.Series()

    def keltner_channels(self, ema_period: int = 20, atr_period: int = 10, 
                        atr_multiplier: float = 2.0) -> tuple:
        """
        Calculate Keltner Channels.
        
        Middle Line = EMA of typical price
        Upper Band = Middle Line + (ATR * multiplier)
        Lower Band = Middle Line - (ATR * multiplier)

        Args:
            ema_period (int): Period for the EMA calculation
            atr_period (int): Period for the ATR calculation
            atr_multiplier (float): Multiplier for the ATR

        Returns:
            tuple: (Upper Band, Middle Line, Lower Band)
        """
        try:
            # Calculate typical price
            typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
            
            # Calculate middle line (EMA of typical price)
            middle_line = typical_price.ewm(span=ema_period, adjust=False).mean()
            
            # Calculate ATR
            atr_values = self.atr(period=atr_period)
            
            # Calculate upper and lower bands
            upper_band = middle_line + (atr_values * atr_multiplier)
            lower_band = middle_line - (atr_values * atr_multiplier)
            
            # Store in DataFrame
            self.df['keltner_middle'] = middle_line
            self.df['keltner_upper'] = upper_band
            self.df['keltner_lower'] = lower_band
            
            return upper_band, middle_line, lower_band
        except Exception as e:
            self.logger.error(f"Error calculating Keltner Channels: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    def volatility(self, period: int = 14) -> pd.Series:
        """
        Calculate Historical Volatility.
        Standard deviation of price changes over a period.

        Args:
            period (int): The period for volatility calculation

        Returns:
            pd.Series: Volatility values
        """
        try:
            # Calculate daily returns
            returns = self.df['close'].pct_change()
            
            # Calculate volatility (standard deviation of returns)
            volatility = returns.rolling(window=period).std() * np.sqrt(period)
            
            self.df[f'volatility_{period}'] = volatility
            return volatility
        except Exception as e:
            self.logger.error(f"Error calculating Volatility: {e}")
            return pd.Series()

    def price_channels(self, period: int = 20) -> tuple:
        """
        Calculate Price Channels.
        
        Upper Channel = Highest high over period
        Lower Channel = Lowest low over period
        Middle Channel = (Upper Channel + Lower Channel) / 2

        Args:
            period (int): The period for channel calculation

        Returns:
            tuple: (Upper Channel, Middle Channel, Lower Channel)
        """
        try:
            upper_channel = self.df['high'].rolling(window=period).max()
            lower_channel = self.df['low'].rolling(window=period).min()
            middle_channel = (upper_channel + lower_channel) / 2
            
            self.df[f'price_channel_upper_{period}'] = upper_channel
            self.df[f'price_channel_middle_{period}'] = middle_channel
            self.df[f'price_channel_lower_{period}'] = lower_channel
            
            return upper_channel, middle_channel, lower_channel
        except Exception as e:
            self.logger.error(f"Error calculating Price Channels: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    def pivot_points(self, method: str = 'standard') -> dict:
        """
        Calculate Pivot Points and their support/resistance levels.
        
        Args:
            method (str): The calculation method ('standard', 'fibonacci', 'woodie', 'camarilla')

        Returns:
            dict: Dictionary containing pivot points and support/resistance levels
        """
        try:
            # Get previous period's high, low, close
            high = self.df['high'].shift(1)
            low = self.df['low'].shift(1)
            close = self.df['close'].shift(1)
            
            if method == 'standard':
                # Calculate standard pivot points
                pivot = (high + low + close) / 3
                r1 = (2 * pivot) - low
                s1 = (2 * pivot) - high
                r2 = pivot + (high - low)
                s2 = pivot - (high - low)
                r3 = high + 2 * (pivot - low)
                s3 = low - 2 * (high - pivot)
                
            elif method == 'fibonacci':
                # Calculate Fibonacci pivot points
                pivot = (high + low + close) / 3
                r1 = pivot + 0.382 * (high - low)
                s1 = pivot - 0.382 * (high - low)
                r2 = pivot + 0.618 * (high - low)
                s2 = pivot - 0.618 * (high - low)
                r3 = pivot + (high - low)
                s3 = pivot - (high - low)
                
            elif method == 'woodie':
                # Calculate Woodie's pivot points
                pivot = (high + low + 2 * close) / 4
                r1 = 2 * pivot - low
                s1 = 2 * pivot - high
                r2 = pivot + (high - low)
                s2 = pivot - (high - low)
                r3 = high + 2 * (pivot - low)
                s3 = low - 2 * (high - pivot)
                
            elif method == 'camarilla':
                # Calculate Camarilla pivot points
                pivot = (high + low + close) / 3
                r1 = close + ((high - low) * 1.1/12)
                s1 = close - ((high - low) * 1.1/12)
                r2 = close + ((high - low) * 1.1/6)
                s2 = close - ((high - low) * 1.1/6)
                r3 = close + ((high - low) * 1.1/4)
                s3 = close - ((high - low) * 1.1/4)
            
            else:
                raise ValueError(f"Unknown pivot point method: {method}")
            
            # Store results in DataFrame
            self.df[f'pivot_{method}'] = pivot
            self.df[f'r1_{method}'] = r1
            self.df[f'r2_{method}'] = r2
            self.df[f'r3_{method}'] = r3
            self.df[f's1_{method}'] = s1
            self.df[f's2_{method}'] = s2
            self.df[f's3_{method}'] = s3
            
            return {
                'pivot': pivot,
                'r1': r1, 'r2': r2, 'r3': r3,
                's1': s1, 's2': s2, 's3': s3
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Pivot Points: {e}")
            return {}

    def parabolic_sar(self, af_start: float = 0.02, af_step: float = 0.02, 
                      af_max: float = 0.2) -> pd.Series:
        """
        Calculate Parabolic SAR (Stop And Reverse).
        
        Args:
            af_start (float): Starting acceleration factor
            af_step (float): Acceleration factor step
            af_max (float): Maximum acceleration factor

        Returns:
            pd.Series: SAR values
        """
        try:
            high = self.df['high']
            low = self.df['low']
            close = self.df['close']
            
            # Initialize series
            sar = pd.Series(index=self.df.index)
            trend = pd.Series(index=self.df.index)
            ep = pd.Series(index=self.df.index)
            af = pd.Series(index=self.df.index)
            
            # Initialize first values
            trend[0] = 1 if close[0] > close[1] else -1
            sar[0] = high[0] if trend[0] < 0 else low[0]
            ep[0] = high[0] if trend[0] > 0 else low[0]
            af[0] = af_start
            
            # Calculate SAR values
            for i in range(1, len(self.df)):
                # Previous values
                sar_prev = sar[i-1]
                ep_prev = ep[i-1]
                af_prev = af[i-1]
                trend_prev = trend[i-1]
                
                # Current values
                if trend_prev > 0:
                    # Uptrend
                    sar[i] = sar_prev + af_prev * (ep_prev - sar_prev)
                    
                    # Ensure SAR is below low
                    sar[i] = min(sar[i], low[i-1], low[i-2] if i > 1 else low[i-1])
                    
                    # Update trend
                    if high[i] > ep_prev:
                        ep[i] = high[i]
                        af[i] = min(af_prev + af_step, af_max)
                    else:
                        ep[i] = ep_prev
                        af[i] = af_prev
                    
                    trend[i] = -1 if low[i] < sar[i] else 1
                    
                else:
                    # Downtrend
                    sar[i] = sar_prev + af_prev * (ep_prev - sar_prev)
                    
                    # Ensure SAR is above high
                    sar[i] = max(sar[i], high[i-1], high[i-2] if i > 1 else high[i-1])
                    
                    # Update trend
                    if low[i] < ep_prev:
                        ep[i] = low[i]
                        af[i] = min(af_prev + af_step, af_max)
                    else:
                        ep[i] = ep_prev
                        af[i] = af_prev
                    
                    trend[i] = 1 if high[i] > sar[i] else -1
                
                # Reverse if needed
                if trend[i] != trend_prev:
                    af[i] = af_start
                    sar[i] = ep[i]
            
            self.df['psar'] = sar
            self.df['psar_trend'] = trend
            
            return sar
            
        except Exception as e:
            self.logger.error(f"Error calculating Parabolic SAR: {e}")
            return pd.Series()

    def donchian_channels(self, period: int = 20) -> tuple:
        """
        Calculate Donchian Channels.
        
        Args:
            period (int): The period for channel calculation

        Returns:
            tuple: (Upper Channel, Middle Channel, Lower Channel)
        """
        try:
            upper_channel = self.df['high'].rolling(window=period).max()
            lower_channel = self.df['low'].rolling(window=period).min()
            middle_channel = (upper_channel + lower_channel) / 2
            
            self.df[f'donchian_upper_{period}'] = upper_channel
            self.df[f'donchian_middle_{period}'] = middle_channel
            self.df[f'donchian_lower_{period}'] = lower_channel
            
            return upper_channel, middle_channel, lower_channel
            
        except Exception as e:
            self.logger.error(f"Error calculating Donchian Channels: {e}")
            return pd.Series(), pd.Series(), pd.Series()

    def williams_r(self, period: int = 14) -> pd.Series:
        """
        Calculate Williams %R.
        
        Args:
            period (int): The lookback period

        Returns:
            pd.Series: Williams %R values
        """
        try:
            highest_high = self.df['high'].rolling(window=period).max()
            lowest_low = self.df['low'].rolling(window=period).min()
            
            wr = ((highest_high - self.df['close']) / 
                  (highest_high - lowest_low)) * -100
            
            self.df[f'williams_r_{period}'] = wr
            return wr
            
        except Exception as e:
            self.logger.error(f"Error calculating Williams %R: {e}")
            return pd.Series()

    def _validate_calculation(self, series: pd.Series, name: str) -> pd.Series:
        """Validate calculation results"""
        if series.empty:
            self.logger.error(f"{name} calculation returned empty series")
            return pd.Series()
        if series.isnull().all():
            self.logger.error(f"{name} calculation returned all null values")
            return pd.Series()
        if (series == 0).all():
            self.logger.error(f"{name} calculation returned all zeros")
            return pd.Series()
        return series

# Example usage
if __name__ == "__main__":
    # Create sample data
    data = {
        'ts': pd.date_range(start='2024-01-01', periods=100, freq='1min'),
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


    # Calculate new indicators
    stoch_rsi, k_line, d_line = arb_1m.stoch_rsi()
    atr_values = arb_1m.atr()
    cci_values = arb_1m.cci()
    ichimoku_components = arb_1m.ichimoku()
    fib_levels = arb_1m.fibonacci_retracement()

    #3RD SET OF INDICATORS
    roc_values = arb_1m.roc(period=12)
    momentum_values = arb_1m.momentum(period=14)
    keltner_upper, keltner_middle, keltner_lower = arb_1m.keltner_channels()
    volatility = arb_1m.volatility()
    price_channels = arb_1m.price_channels()

    pivot_points = arb_1m.pivot_points(method='standard')  # or 'fibonacci', 'woodie', 'camarilla'
    psar = arb_1m.parabolic_sar()
    upper_dc, middle_dc, lower_dc = arb_1m.donchian_channels(period=20)
    williams = arb_1m.williams_r(period=14)

    
        
    # Get the results
    print(arb_1m.get_latest_indicators()),

