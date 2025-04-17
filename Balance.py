import requests
import time
import hmac
import hashlib
import base64
from api import api_key, api_secret, api_passphrase
# ✅ Trage hier deine API-Daten ein
API_KEY = api_key
API_SECRET = api_secret
API_PASSPHRASE = api_passphrase

BASE_URL = 'https://api.bitget.com'
ENDPOINT = '/api/v2/mix/account/account'
symbol = 'BTCUSDT'
product_type = 'USDT-FUTURES'
margin_coin = 'usdt'

def get_timestamp():
    return str(int(time.time() * 1000))

def generate_signature(timestamp, method, request_path, query_string):
    if query_string:
        request_path += '?' + query_string
    pre_hash = timestamp + method + request_path
    hmac_key = bytes(API_SECRET, encoding='utf-8')
    signature = hmac.new(hmac_key, pre_hash.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

from decimal import Decimal

def get_usdt_balance():
    method = 'GET'
    query = f'symbol={symbol}&productType={product_type}&marginCoin={margin_coin}'
    timestamp = get_timestamp()
    sign = generate_signature(timestamp, method, ENDPOINT, query)

    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': sign,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': API_PASSPHRASE,
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }

    url = f'{BASE_URL}{ENDPOINT}?{query}'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data['code'] == '00000':
            available = data['data']['available']
            print(f"✅ Verfügbares USDT: {available}")
            return Decimal(str(available))  # wichtig: als Decimal zurückgeben
        else:
            print(f"❌ Fehler: {data['msg']}")
            return None
    else:
        print(f"❌ HTTP Fehler: {response.status_code} – {response.text}")
        return None
if __name__ == '__main__':
    get_usdt_balance()
