import pandas as pd
from api_clients import ApiBitunix
from data_processing import Indicator
from dotenv import load_dotenv

#Load Environment Variables
load_dotenv()

def main():
    #Initialize the API
    client = ApiBitunix()

    #Fetch K-Line data for a specific symbol and interval
    symbol = 'BTCUSDT'
    interval = '1' #1min default
    df_kline = client.get_kline_data(symbol,interval)

    if df_kline is not None:
        # df_kline has columns: ['symbol', 'open', 'high', 'low', 'close', 'volume', 'ts']
        #Confirm Data Types
        df_kline['close'] = pd.to_numeric(df_kline['close'], errors='coerce')
        df_kline['ts'] = pd.to_datetime(df_kline['ts'])


        #Initialize the Indicator with DF we just pulled
        indicators = Indicator(df_kline)

        #Calculate EMA with a span of 5
        ema5 = indicators.ema(span=5)
        indicators.add_indicator('EMA5', ema5)
        
        #Calculate the SMA 10
        sma10 = indicators.sma(window=10)
        indicators.add_indicator("SMA10", sma10)

        #Calculate the RSI
        rsi = indicators.rsi(periods=14)
        indicators.add_indicator('RSI', rsi)

        df_with_indicators = indicators.get_dataframe()

        print (df_with_indicators)

if __name__ == "__main__":
    main()