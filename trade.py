import time
import hmac
import hashlib
import requests
from typing import Optional
from api import api_key, api_passphrase, api_secret
import json
from decimal import Decimal, InvalidOperation

API_KEY = api_key 
API_SECRET = api_secret
API_PASSPHRASE = api_passphrase

BASE_URL = "https://api.bitget.com"

def generate_signature(timestamp: str, method: str, request_path: str, body: str) -> str:
    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(API_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return mac.hexdigest()

def safe_decimal(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        return str(Decimal(value))
    except (InvalidOperation, ValueError):
        return None

def place_order(
    symbol: str,
    product_type: str,
    margin_mode: str,
    margin_coin: str,
    size: str,
    side: str,
    order_type: str,
    trade_side: Optional[str] = None,
    price: Optional[str] = None,
    force: Optional[str] = "gtc",
    client_oid: Optional[str] = None,
    reduce_only: Optional[str] = None,
    preset_tp: Optional[str] = None,
    preset_sl: Optional[str] = None,
    stp_mode: Optional[str] = None
) -> dict:
    """Sendet eine Order an Bitget mit Decimal-Handling."""
    timestamp = str(int(time.time() * 1000))
    path = "/api/v2/mix/order/place-order"
    url = BASE_URL + path

    body = {
        "symbol": symbol,
        "productType": product_type,
        "marginMode": margin_mode,
        "marginCoin": margin_coin,
        "size": safe_decimal(size),
        "side": side,
        "orderType": order_type
    }

    if trade_side: body["tradeSide"] = trade_side
    if price: body["price"] = safe_decimal(price)
    if force: body["force"] = force
    if client_oid: body["clientOid"] = client_oid
    if reduce_only: body["reduceOnly"] = reduce_only
    if preset_tp: body["presetStopSurplusPrice"] = safe_decimal(preset_tp)
    if preset_sl: body["presetStopLossPrice"] = safe_decimal(preset_sl)
    if stp_mode: body["stpMode"] = stp_mode

    body_str = json.dumps(body)
    sign = generate_signature(timestamp, "POST", path, body_str)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_str)
    return response.json()
