import ccxt
import logging
import math
from config import symbol, product_type, margin_coin
from api import api_key, api_secret, api_passphrase

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Bitget-Client initialisieren
client = ccxt.bitget({
    'apiKey': api_key,           # API-Schlüssel
    'secret': api_secret,        # Secret
    'password': api_passphrase,  # Passphrase
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},  # Standardmäßig Futures
})

def truncate_decimal(value, decimals):
    """
    Schneidet Dezimalstellen auf die angegebene Anzahl ab, ohne zu runden.
    
    Args:
        value (float): Der zu kürzende Wert.
        decimals (int): Anzahl der Dezimalstellen, die beibehalten werden.
    
    Returns:
        float: Abgeschnittener Wert.
    """
    factor = 10 ** decimals
    return math.floor(value * factor) / factor

def fetch_market_precision(symbol):
    """
    Fragt die Präzision für das angegebene Symbol ab.
    
    Args:
        symbol (str): Handelspaar, z.B. "BTCUSDT".
    
    Returns:
        dict: Präzisionsinformationen (price_precision, amount_precision, size_multiplier).
    """
    try:
        markets = client.load_markets()
        market = markets[symbol]
        price_precision = int(market['info']['pricePlace'])  # z.B. 1 für BTCUSDT
        amount_precision = int(market['info']['volumePlace'])  # z.B. 3 für BTCUSDT
        size_multiplier = float(market['info']['sizeMultiplier'])  # z.B. 0.001 für BTCUSDT
        return {
            'price_precision': price_precision,
            'amount_precision': amount_precision,
            'size_multiplier': size_multiplier
        }
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Marktpräzision: {e}")
        raise

def set_leverage(leverage, symbol):
    """
    Setzt den Hebel für das angegebene Symbol (z.B. 100x).
    """
    try:
        logging.info(f"Setze Hebel auf {leverage}x für {symbol}")
        client.set_leverage(leverage, symbol, params={'marginMode': 'isolated'})
    except Exception as e:
        logging.error(f"Fehler beim Setzen des Hebels: {e}")
        raise

def place_market_order(symbol, side, amount):
    """
    Platziert eine Marktorder auf Bitget mit Berücksichtigung der Präzision (Abschneiden statt Runden).
    
    Args:
        symbol (str): Handelspaar, z.B. "BTCUSDT".
        side (str): "buy" oder "sell".
        amount (float): Menge in USDT (Quote-Währung).
    
    Returns:
        dict: Details der platzierten Order.
    """
    try:
        # Hebel auf 100 setzen
        set_leverage(100, symbol)

        # Marktpräzision abfragen
        precision = fetch_market_precision(symbol)
        price_precision = precision['price_precision']
        amount_precision = precision['amount_precision']
        size_multiplier = precision['size_multiplier']

        # Aktuellen Preis abrufen, um die Menge in Kontrakten zu berechnen
        ticker = client.fetch_ticker(symbol)
        price = ticker['last']
        price = truncate_decimal(price, price_precision)  # Preis abschneiden, z.B. 84725.43 -> 84725.4

        # Berechne die Anzahl der Kontrakte: amount / price = Menge in Base-Währung (z.B. BTC)
        # Dann auf size_multiplier anpassen
        base_amount = amount / price  # Menge in BTC
        contracts = base_amount / size_multiplier  # Anzahl der Kontrakte
        contracts = truncate_decimal(contracts, amount_precision)  # Abschneiden auf amount_precision, z.B. 0.123456 -> 0.123

        # Prüfen, ob der Notionalwert (amount) den Mindestanforderungen entspricht (min. 5 USDT)
        notional_value = contracts * size_multiplier * price
        if notional_value < 5:
            logging.error(f"Notionalwert {notional_value} USDT ist unter dem Minimum von 5 USDT.")
            raise ValueError("Orderwert unter dem Minimum von 5 USDT.")

        params = {
            'productType': product_type,  # z.B. "USDT-FUTURES"
            'marginMode': 'isolated',     # Isolierten Margin-Modus
            'marginCoin': margin_coin,    # z.B. "USDT"
            'size': str(contracts),       # Anzahl der Kontrakte
            'side': side,                 # "buy" oder "sell"
            'orderType': 'market',        # Marktorder
        }
        order = client.create_order(symbol, 'market', side, contracts, params=params)
        logging.info(f"Marktorder erfolgreich platziert: {order}")
        return order
    except Exception as e:
        logging.error(f"Fehler beim Platzieren der Marktorder: {e}")
        raise


