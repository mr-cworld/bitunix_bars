import pandas as pd
import numpy as np

class Indicator:
    """
    A class to calculate various technical indicators on a given DataFrame.
    """

    def __init__(self,df):
        """
        Initializes the Indicator class with a DataFrame.
        Base Columns Available: ['open']['high']['low']['close']['volume']['ts']

        Args:
            df (DataFrame): The input DataFrame containing market data
        """
        self.df = df.copy()
        if 'close' not in self.df.columns:
            raise ValueError ("DataFrame must contain a 'close' column for indicator calculations.")
    
    def add_indicator(self, indicator_name, data_series):
        """
        Adds a new indicator series to the DataFrame.

        Args:
            indicator_name(str): The name of the indicator to add as a column
            data_series (Series): The Pandas Series containing the indicator data.
        """
        self.df[indicator_name] = data_series

    def get_dataframe(self):
        """
        Returns the DataFrame with added indicators. Combo with a .copy()

        Returns:
            DataFrame: the DataFrame containing market data and indicators.
        """
        return self.df

    def ema (self, span, adjust=False):
        """
        Calculates the Exponential Moving Average (EMA).

        Args:
            span (int): The number of periods to calculate the EMA over.
            adjust (bool): Use adjust parameter as inpandas ewm method.

        Returns:
            Series: A Pandas Series containing the EMA Values.
        """

        ema_series = self.df['close'].ewm(span=span, adjust=adjust).mean()
        return ema_series
    
    def sma (self, window):
        """
        Calculates the Simple Moving Average (SMA).

        Args:
            window (int): The number of periods to calculate the SMA over.

        Returns:
            Series: A Pandas Series containing the SMA values.
        """
        sma_series = self.df['close'].rolling(window=window).mean()
        return sma_series


    def rsi(self, periods=14):
        """
        Calculates sthe Relative Strength Index (RSI).

        Args:
            periods (int): The number of periods for calculating RSI.

        Returns:
            Series: A Pandas Series containing the RSI Values
        """
        delta = self.df['close'].diff()
        gain = delta.clip(lower = 0)
        loss = -delta.clip(upper = 0)
        avg_gain = gain.rolling(window=periods).mean()
        avg_loss = loss.rolling(window=periods).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def wma(self,window):
        """
        Calculates the Weighted Moving Average (WMA).

        The WMA assigns more weight to recent data points. The weights decrease in arthmetic progression.

        Args:
            window (int): The number of periods to calculater the WMA over.

        Returns:
            Series: A Pandas Series containing the WMA values.
        """
        weights = np.arange(1, window + 1)
        wma_series = self.df['close'].rolling(window).apply(
            lambda prices: np.dot(prices,weights) / weights.sum(), raw=True)
        return wma_series
    
    def wma_on_series(self, series, window):
        """
        Calculates the Weighted Moving Average (WMA) on a given Series.

        Args:
            series (Series): The data series to calculate the WMA on.
            window (int): The number of periods to calculate the WMA over.

        Returns:
            Series: A PAndas Series containing te WMA values.
        """

        weights = np.arange(1, window + 1)
        wma_series = series.rolling(window).apply(
            lambda prices:np.dot(prices,weights) / weights.sum(), raw=True)
        return wma_series
    
    def hma(self, window):
        """
        Calculates the Hull Moving Average (HMA).

        The HMA is designed to reduce lag and improve the smoothing over a Weighted Moving Average

        Formula:
            HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
        
            Args:
                window (int): The number of periods to calculate the HMA over.

            Returns:
                Series: a Pandas Series contianing the HMA values
        """
        price = self.df['close']
        half_window = int(window / 2)
        sqrt_window = int(np.sqrt(window))

        wma_half = self.wma_on_series(price,half_window)
        wma_full = self.wma_on_series(price,window)
        diff = (2 * wma_half) - wma_full
        hma_series = self.wma_on_series(diff, sqrt_window)
        return hma_series
    
    def moving_average_envelopes(self, window, percentage=0.025, ma_type='sma'):
        """
        Calculates the Moving Average Envelopes.

        The Envelopes are percentage-based bands set above and below a moving average.

        Formula:
            -Moving Average (MA): SMA or EMA over the specified window.
            -Upper Envelope = MA + (MA * percentage)
            -Lower Envelope = MA - (MA * percentage)

        Args:
            window (int): The number of periods to calculate the moving average over.
            percentage (float): The percentage distance from the moving average to set the envelopes (e.g., 0.025 for 2.5%)
            ma_type (str): The tpe of moving average to use ('sma' or 'ema')

        Returns:
            Tuple[Series, Series, Series]: A tuple containing the MA, Upper Envelope, and Lower Envelope as Pandas Series
        """
        #Todo, have another method or way to unpack just the upper and lower envelope and add to the indicators df

        if ma_type.lower() == 'sma':
            ma = self.sma(window)
        if ma_type.lower() == 'ema':
            ma = self.ema(window)
        else:
            raise ValueError("ma_type must be 'sma' or 'ema'")
        
        upper_envelope = ma + (ma * percentage)
        lower_envelope = ma + (ma * percentage)
        return ma, upper_envelope, lower_envelope
    
    def stocastic_rsi(self, periods=14, smooth_k=3, smooth_d=3):
        """
        Calculates the Stochastic RSI.

        The Stochastic RSI is an oscillator that measures the level of RSI relative to its high-low range over a set time period.

        Formula:
            - RSI: Relative Strength Index over the specified periods.
            - Stochastic RSI = (RSI - min(RSI over periods)) / (max(RSI over periods) - min(RSI over periods))
            - %K: Smoothed Stochastic RSI over 'smooth_k' periods.
            - %D: Smoothed %K over 'smooth_d' periods.

        Args:
            periods (int): The number of periods to calculate the RSI and Stocastic RSI over.
            smooth_k (int): The %K smoothing factor (default is 3).
            smooth_d (int): The %D smoothing factor (default is 3).

        Returns:
            DataFrame: A DataFrame containing hte Stocastic RSI %K and %D values.
        """

        rsi = self.rsi(periods)
        min_rsi = rsi.rolling(window=periods).min()
        max_rsi = rsi.rolling(window=periods).max()
        stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi)

        stoch_rsi_k = stoch_rsi.rolling(window=smooth_k).mean()
        stoch_rsi_d = stoch_rsi_k.rolling(window=smooth_d).mean()

        stoch_rsi_df = pd.DataFrame({
            'StochRSI_%K': stoch_rsi_k * 100,
            'StochRSI_%D': stoch_rsi_d * 100
        })
        return stoch_rsi_df
    
