import argparse
import requests
import time
import hashlib
import hmac
import uuid
import json

def generate_signature(secret, timestamp, method, request_path, body):
    string_to_sign = f"{timestamp}{method.upper()}{request_path}{body}"
    sign = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    return sign

def modify_order(api_key, api_secret, passphrase, order_id=None, client_oid=None, symbol=None, product_type=None, new_tp=None, new_client_oid=None):
    # Validate that either order_id or client_oid is provided
    if order_id is None and client_oid is None:
        raise ValueError("Either order_id or client_oid must be provided.")
    
    # Generate new_client_oid if not provided
    if new_client_oid is None:
        new_client_oid = str(uuid.uuid4())
    
    # Construct request body
    body = {
        "symbol": symbol,
        "productType": product_type,
        "newClientOid": new_client_oid,
        "newPresetStopSurplusPrice": new_tp
    }
    if order_id:
        body["orderId"] = order_id
    if client_oid:
        body["clientOid"] = client_oid
    
    body_str = json.dumps(body)
    
    # Prepare API request
    timestamp = str(int(time.time() * 1000))
    method = "POST"
    request_path = "/api/v2/mix/order/modify-order"
    sign = generate_signature(api_secret, timestamp, method, request_path, body_str)
    
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": sign,
        "ACCESS-PASSPHRASE": passphrase,
        "ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    
    url = "https://api.bitget.com/api/v2/mix/order/modify-order"
    response = requests.post(url, headers=headers, data=body_str)
    
    # Handle response
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Modify the take-profit (TP) of a pending order on Bitget.")
    parser.add_argument('--api-key', required=True, help="API key")
    parser.add_argument('--api-secret', required=True, help="API secret")
    parser.add_argument('--passphrase', required=True, help="API passphrase")
    parser.add_argument('--order-id', required=False, help="Order ID")
    parser.add_argument('--client-oid', required=False, help="Client Order ID")
    parser.add_argument('--symbol', required=True, help="Trading pair, e.g., ETHUSDT")
    parser.add_argument('--product-type', required=True, help="Product type, e.g., usdt-futures")
    parser.add_argument('--new-tp', required=True, help="New take-profit price, e.g., 2000.00")
    parser.add_argument('--new-client-oid', required=False, help="New client order ID (optional)")

    args = parser.parse_args()

    if not args.order_id and not args.client_oid:
        print("Error: Either --order-id or --client-oid must be provided.")
        exit(1)

    try:
        result = modify_order(
            api_key=args.api_key,
            api_secret=args.api_secret,
            passphrase=args.passphrase,
            order_id=args.order_id,
            client_oid=args.client_oid,
            symbol=args.symbol,
            product_type=args.product_type,
            new_tp=args.new_tp,
            new_client_oid=args.new_client_oid
        )
        if result["code"] == "00000":
            print("Order TP modified successfully.")
            print(f"Order ID: {result['data']['orderId']}")
            print(f"Client OID: {result['data']['clientOid']}")
        else:
            print(f"API Error: {result['msg']}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
