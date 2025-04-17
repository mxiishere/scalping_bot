import uuid
import requests
from decimal import Decimal, ROUND_DOWN, getcontext
from balance import get_usdt_balance
from trade import place_order
from data import fetch_bitget_klines, calculate_vwap_last_60

# Setze globale Genauigkeit für Decimal
getcontext().prec = 10

# === Position Tracking (max. 3 Trades pro Richtung) ===
long_trade_count = 0
short_trade_count = 0
MAX_TRADES_PER_DIRECTION = 3

def get_market_price(symbol):
    url = f"https://api.bitget.com/api/mix/v1/market/ticker?symbol={symbol}"
    res = requests.get(url).json()
    return Decimal(res["data"]["last"])

def calculate_sl_and_vwap_tp(entry_price: Decimal, direction: str):
    sl_distance = Decimal("0.006")  # 0.6 %

    # 📊 Daten holen & VWAP berechnen
    df = fetch_bitget_klines(symbol="BTCUSDT", granularity="1m", num_candles=60)
    if df is None:
        raise Exception("Fehler beim Abrufen der Candles für VWAP")

    vwap_tp = Decimal(str(calculate_vwap_last_60(df)))

    # 🔻 SL auf Basis von Prozent
    if direction == "LONG":
        stop_loss = entry_price * (Decimal("1") - sl_distance)
    else:
        stop_loss = entry_price * (Decimal("1") + sl_distance)

    stop_loss = stop_loss.quantize(Decimal("0.01"))
    vwap_tp = vwap_tp.quantize(Decimal("0.01"))

    return stop_loss, vwap_tp

def execute_trade(direction: str, symbol="BTCUSDT"):
    global long_trade_count, short_trade_count

    # Prüfen auf aktives Limit
    if direction == "LONG" and long_trade_count >= MAX_TRADES_PER_DIRECTION:
        print("⚠️ Max. 3 LONG-Positionen erreicht – kein neuer Trade.")
        return None
    if direction == "SHORT" and short_trade_count >= MAX_TRADES_PER_DIRECTION:
        print("⚠️ Max. 3 SHORT-Positionen erreicht – kein neuer Trade.")
        return None

    usdt_balance = get_usdt_balance()
    if usdt_balance is None:
        print("❗ Kein USDT-Guthaben verfügbar – Trade wird abgebrochen.")
        return

    capital_to_use = usdt_balance * Decimal("0.01")
    leverage = Decimal("100")
    order_value = capital_to_use * leverage

    current_price = get_market_price(symbol)
    size = (order_value / current_price).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)

    stop_loss, vwap_tp = calculate_sl_and_vwap_tp(current_price, direction)

    side = "buy" if direction == "LONG" else "sell"
    client_oid = str(uuid.uuid4())

    print(f"\n📢 Executing {direction} | Size: {size} | SL: {stop_loss} | TP (VWAP): {vwap_tp} | Entry: {current_price}")

    place_order(
        symbol=symbol,
        product_type="USDT-FUTURES",
        margin_mode="isolated",
        margin_coin="USDT",
        size=str(size),
        side=side,
        order_type="market",
        client_oid=client_oid,
        preset_sl=str(stop_loss),
        preset_tp=str(vwap_tp),
    )

    # Zähler hochsetzen
    if direction == "LONG":
        long_trade_count += 1
    elif direction == "SHORT":
        short_trade_count += 1

    return client_oid

def reset_trade_counts():
    global long_trade_count, short_trade_count
    long_trade_count = 0
    short_trade_count = 0
