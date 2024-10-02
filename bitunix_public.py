import requests
import pandas as pd
import time
import hashlib
import hmac
import random
import string
import json

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