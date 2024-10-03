import pandas as pd

class Indicator:
    """
    A class to calculate various technical indicators on a given DataFrame.
    """

    def __init__(self,df):
        """
        Initializes the Indicator class with a DataFrame.
        Base Columns Available: 
        ['open']['high']['low']['close']['volume']['ts']

        Args:
            df (DataFrame): The input DataFrame containing market data

        """
        self.df = df.copy()
        if 'close' not in self.df.columns:
            raise ValueError ("DataFrame must contain a close column for indicator calculations.")
        
    def ema (self, span, adjust=False):
        """
        Calculates the Exponential Moving Average (EMA).

        Args:
            span (int): The number of periods to calculate the EMA over.
            adjust  (bool): Use adjust parameter as inpandas ewm method.

        Returns:
            Series: A Pandas Series containing the EMA Values.

        """
        #Todo - need to think about changing the return type to be a DataFrame instead of a Series where DF holds the bar's charts percise Bar Time not Number

        ema_series = self.df['close'].ewm(span=span, adjust=adjust).mean()
        return ema_series
    
    def sma (self, window):
        """
        Calculates the Simple Moving Average (SMA).

        Args:
            window (int): The number of periods to calculate the SMA over.

        Returns:
            SEries: A Pandas Series containing the SMA values.
        """
        sma_series = self.df['close'].rolling(window=window).mean()
        return sma_series
    
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


### Day 2 of Adding Indicators:

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