from .base_api_client import BaseApiClient
import requests
import pandas as pd
import time, json, hashlib, hmac, random, string, os, logging
from pathlib import Path


class ApiBitunix(BaseApiClient):
    """
    Client for interacting with the BitUnix API
    """

    BASE_URL = "https://openapi.bitunix.com/api/spot/v1/market"

    def __init__(self, api_key=None, secret_key=None):
        """
        Initaliazes the BitUnix APiClient with Credentials
        
        Args:
            api_key (str): Your BitUnix API key.
            secret_key (str): our Bitunix secret key.
        """
        self.api_key = api_key or os.getenv('BITUNIX_API_KEY')
        self.secret_key = secret_key or os.getenv("BITUNIX_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError("API key and Secret Key must be valid")
        
        #Configure Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        #Ensure storage directory exists
        self.storage_path = Path('Storage')
        self.storage_path.mkdir(exist_ok=True)

    def create_nonce(self, length=32):
        """Creates a random nonce"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def create_timestamp(self):
        """Creates a timestamp in milliseconds"""
        return str(int(time.time()*1000))
    
    def create_signature(self, nonce, timestamp):
        message = self.api_key + nonce + timestamp
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def get_headers(self):
        """ Constructs headers required for API requests """
        nonce = self.create_nonce()
        timestamp = self.create_timestamp()
        signature = self.create_signature(nonce, timestamp)
        return {
            'api-key': self.api_key,
            'nonce': nonce,
            'timestamp':timestamp,
            'signature':signature,
            'Content-Type':'application/json'
        }
    
    def get_latest_price(self, symbol):
        """
        Getches latest price for a given symbol.

        Args:
            symbol (str): The trading pair symbol, e.g., 'BTCUSDT'

        Returns:
            dict: Latest price data
        """
        url = f'{self.BASE_URL}/last_price'
        headers = self.get_headers()
        params = {'symbol':symbol}

        try:
            response = requests.get(url, headers=headers, params = params)
            data = response.json()

            if data['code'] == '0':
                self.logger.info(f'Fetched latest price for {symbol}')
                return data['data']
            else:
                self.logger.error(f'Error: {data['msg']}')
                return None
        
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            return None
        

    def get_kline_data(self, symbol, interval='1'):
        """
        Fetches K-Line (candlestick) data.

        Args:
            symbol (str): The trading pair symbol.
            interval (str): The interval for candlesticks.

        Returns:
            DataFrame: Pandas DataFrame containing K-Line data
        """

        url = f'{self.BASE_URL}/kline'
        headers = self.get_headers()
        params = {'symbol': symbol, 'interval': interval}

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if data['code'] == '0':
                df = pd.DataFrame(data['data'])
                self.logger.info(f"Fetched K-Line data for {symbol} at interval {interval}")
                return df
            else:
                self.logger.error(f"Error: {data['msg']}")
                return None
        except Exception as e:
            self.logger.error(f"An error occured: {e}")
            return None
        
    def save_dataframe_to_csv(self, df, filename):
        """
        Saves a DataFrame to a CSV file in the storage directory.

        Args:
            df (DataFrame): The DataFrame to save.
            filename (str): The filename for the CSV File
        """    

        file_path = self.storage_path / filename
        df.to_csv(file_path, index=False)
        self.logger.info(f"Data saved to {file_path}")

    def fetch_and_save_latest_price(self, symbol):
        """
        Fetches the latest price and saves it to a CSV File.

        Args:
            symbol (str): The trading pair symbol
        """
        data = self.get_latest_price(symbol)
        if data:
            df = pd.DataFrame([{'symbol':symbol, 'latest_price': data}])
            self.save_dataframe_to_csv(df, "f(symbol)_latest_price.csv")
        
        #todo - do i want this to save this in a smarter way? like create a new csv each time based on timestamp?

    def fetch_and_save_kline_data(self, symbol, interval='1'):
        """
        Fetches K-Line data and saves it to a CSV file.

        Args:
            symbol (str): The trading pair symbol.
            interval (str): The interval for candlesticks.
        """
        df = self.get_kline_data(symbol, interval)
        if df is not None:
            filename = f"{symbol}_kline_{interval}.csv"
            self.save_dataframe_to_csv(df, filename)

        #todo - same as above, do i want this to save in a smarter way based on timestamp?

        








###########


    def fetch_data(self):
        #implementation for this api
        pass

    def process_data(self,data):
        #specific processing for API One
        pass


#Define API Key and Secret Key (todo: Temporary API Key)
API_KEY = "b478e55cb996264f8ade2cd9450d453b"
SECRET_KEY = "7d2d3b78c073b3669537cf8651102e1c"

#Create a None (Random String)
def create_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

#Create a Timestamp (in Milliseconds)
def create_timestamp():
    return str(int(time.time()*1000))

#Create the signature using HMAC SHA256
def create_signature(api_key, secret_key, nonce, timestamp):
    message = api_key + nonce + timestamp
    return hmac.new(secret_key.encode(), message.enconde(), hashlib.sha256).hexdigest()

#Fetch latest price data from the API
def get_latest_price(symbol):
    url = "https://openapi.bitunix.com/api/spot/v1/market/last_price"
    headers = {
        'api-key': API_KEY,
        'nonce': create_nonce(),
        'timestamp': create_timestamp(),
        'Content-Type': 'application/json'
    }

    params = {
        'symbol': symbol
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        #DEBUGGING CODE todo - remove later
        print("**Printing JSON from def get_latest_price() **")
        print(data)
        print("**JSON DUMPS from def get latest_price() ***")
        print(json.dumps(data, indent=2))

        if data['code'] == str(0):
            return data['data']
        else:
            print(f'Error: {data["msg"]}, Your data[code] should have been 0, but instead it was {data["code"]}')
            return None
    except Exception as e:
        print(f"An Error occurred: {e}")
        return None

#Fetch K-Line (Candlestick) Data
def get_kline_data(symbol, interval='1'):
    url = "https://openapi.bitunix.com/api/spot/v1/market/kline"
    headers = {
        'api-key': API_KEY,
        'nonce': create_nonce(),
        'timestamp': create_timestamp(),
        'Content-Type': 'application/json'
    }

    params = {
        'symbol':symbol,
        'interval':interval
    }

    try:
        response = requests.get(url,headers=headers, params=params)
        data = response.json()

        if data['code'] == str(0):
            return data['data']
        else:
            print(f"Error on get_kline_data with {symbol} for symbol and {interval} for interval, datacode = {data['code']}")
            return None
    except Exception as e:
        print(f"An Exception Error Occurred on get_kline_data. Symbol {symbol}, Interval {interval}, Exception: {e}")
        return None


## TESTING 

# Example: Fetch the latest price and save to a DataFrame
symbol = 'BTCUSDT'  # Example trading pair
interval = "1"
kline_data = get_kline_data(symbol, interval)

if kline_data:
    df = pd.DataFrame(kline_data)
    print(df)



#Testing 2

#API CALL
latest_price = get_latest_price(symbol)

# Create a DataFrame
if latest_price:
    df = pd.DataFrame([{'symbol': symbol, 'latest_price': latest_price}])
    print(df)

    # Save to CSV file
    df.to_csv('latest_price.csv', index=False)



