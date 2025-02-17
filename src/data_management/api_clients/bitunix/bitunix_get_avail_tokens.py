import requests
import time
import hmac
import hashlib
import json
import random
import string

# Import API keys from yaml config
import yaml
from pathlib import Path

# Load API keys from yaml file
try:
    # Navigate from current file location to the keys
    # Go up to api_clients, then up to data_management, then to config/keys
    keys_path = Path(__file__).resolve().parent.parent.parent / 'config' / 'keys' / 'bitunix_keys.yaml'
    
    print(f"Attempting to access keys at: {keys_path}")
    
    if not keys_path.exists():
        print(f"Keys file not found at: {keys_path}")
        exit(1)
    
    with open(keys_path) as f:
        keys = yaml.safe_load(f)

except Exception as e:
    print(f"Error loading keys file: {str(e)}")
    exit(1)

api_key = keys['api_key']
api_secret = keys['secret_key']

# Function to generate a random nonce
def generate_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to create the signature
def create_signature(api_secret, timestamp, nonce, method, endpoint, query_string=''):
    message = f'{timestamp}{nonce}{method}{endpoint}{query_string}'
    return hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

# Function to make authenticated requests
def make_request(method, endpoint, params=None):
    base_url = 'https://openapi.bitunix.com'
    url = f'{base_url}{endpoint}'
    timestamp = str(int(time.time() * 1000))  # Current timestamp in milliseconds
    nonce = generate_nonce()
    query_string = ''
    if params:
        query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
        if method == 'GET':
            url += f'?{query_string}'
    signature = create_signature(api_secret, timestamp, nonce, method, endpoint, query_string)
    headers = {
        'api-key': api_key,
        'nonce': nonce,
        'timestamp': timestamp,
        'sign': signature,
        'Content-Type': 'application/json'
    }
    if method == 'GET':
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, json=params)
    return response.json()

# Retrieve all available symbols
'''
def get_all_symbols():
    endpoint = '/api/v1/futures/market/trading_pairs'
    response = make_request('GET', endpoint)
    try:
        if response.get('code') == 0 and 'data' in response:
            symbols = [item['symbol'] for item in response['data']]
            return symbols
        else:
            print(f"Error fetching symbols: {response.get('msg', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Exception occurred while fetching symbols: {str(e)}")
        return []
    '''

def get_all_symbols():
    endpoint = '/api/v1/futures/market/trading_pairs'
    response = make_request('GET', endpoint)
    print("Raw API Response:", json.dumps(response, indent=4))  # Print full response for debugging
    try:
        if response.get('code') == 0 and 'data' in response:
            symbols = [item['symbol'] for item in response['data']]
            return symbols
        else:
            print(f"Error fetching symbols: {response.get('msg', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Exception occurred while fetching symbols: {str(e)}")
        return []


# Retrieve all available timeframes
def get_all_timeframes():
    # According to the API documentation, the available intervals for kline data are:
    timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    return timeframes

if __name__ == '__main__':
    try:
        symbols = get_all_symbols()
        print("\nAvailable Symbols:")
        print(symbols)

        timeframes = get_all_timeframes()
        print("\nAvailable Timeframes:")
        print(timeframes)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
