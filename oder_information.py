import requests
import time
import hmac
import hashlib
import base64
from api import api_passphrase, api_key, api_secret
from logik import reset_position_flags  # <-- Wichtig!

API_KEY = api_key
API_SECRET = api_secret
PASSPHRASE = api_passphrase

def generate_signature(api_key, api_secret, timestamp, query_string):
    message = f"{timestamp}GET/api/v2/mix/order/detail?{query_string}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')

def get_order_status(api_key, api_secret, passphrase, symbol, product_type, order_id=None, client_oid=None):
    base_url = "https://api.bitget.com/api/v2/mix/order/detail"

    if not order_id and not client_oid:
        return "Error: Either orderId or clientOid is required"

    params = {
        "symbol": symbol.upper(),
        "productType": product_type
    }
    if order_id:
        params["orderId"] = order_id
    if client_oid:
        params["clientOid"] = client_oid

    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(api_key, api_secret, timestamp, query_string)

    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-PASSPHRASE": passphrase,
        "ACCESS-TIMESTAMP": timestamp,
        "locale": "en-US",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"{base_url}?{query_string}", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == "00000":
            return data["data"]
        else:
            return f"Error: {data.get('msg', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Error: Request failed: {str(e)}"


def monitor_trade_status(symbol, product_type, client_oid):
    """Überwacht den Trade-Status anhand der client_oid."""
    print(f"👀 Überwache Order: {client_oid}")
    while True:
        result = get_order_status(
            api_key=API_KEY,
            api_secret=API_SECRET,
            passphrase=PASSPHRASE,
            symbol=symbol,
            product_type=product_type,
            client_oid=client_oid
        )

        if isinstance(result, dict):
            status = result.get("status", "unknown")
            print(f"📊 Order-Status: {status}")

            if status.lower() in ["filled", "cancelled", "closed", "fail"]:
                print(f"✅ Order abgeschlossen – Rücksetzen der Position-Flags.")
                reset_position_flags()
                break
        else:
            print(result)  # Fehler anzeigen

        time.sleep(10)  # Alle 10s prüfen
