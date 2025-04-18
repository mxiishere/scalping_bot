import logging
from decimal import Decimal
from config import symbol  # Symbol aus config.py (z. B. "BTCUSDT")
from balance import get_usdt_balance  # Funktion aus balance.py
from trade import place_market_order, client  # Funktion und Client aus trade.py

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def get_open_positions_count(symbol, direction):
    """
    Prüft die Anzahl offener Positionen für die angegebene Richtung (LONG oder SHORT).
    
    Args:
        symbol (str): Handelspaar, z.B. "BTCUSDT".
        direction (str): "LONG" oder "SHORT".
    
    Returns:
        int: Anzahl offener Positionen für die Richtung.
    """
    try:
        positions = client.fetch_positions([symbol], params={'productType': 'USDT-FUTURES'})
        count = 0
        side = 'long' if direction == 'LONG' else 'short'
        for position in positions:
            if position['side'] == side and float(position['contracts']) > 0:
                count += 1
        logging.info(f"Anzahl offener {direction}-Positionen für {symbol}: {count}")
        return count
    except Exception as e:
        logging.error(f"Fehler beim Abrufen offener Positionen: {e}")
        raise

def execute_trade(direction):
    """
    Führt einen Trade (LONG oder SHORT) aus, wenn weniger als 3 Positionen offen sind.
    Nutzt 1% des USDT-Saldos aus balance.py.
    """
    try:
        logging.info(f"Starte Trade-Ausführung: {direction}")
        
        # Prüfen, ob maximale Anzahl an Positionen pro Seite erreicht ist
        open_positions = get_open_positions_count(symbol, direction)
        if open_positions >= 3:
            logging.warning(f"Maximal 3 {direction}-Positionen erlaubt. Trade wird übersprungen.")
            return

        # USDT-Saldo aus balance.py abrufen
        available_usdt = get_usdt_balance()
        logging.info(f"Verfügbares USDT: {available_usdt}")

        # 1% des Kapitals berechnen
        usdt_amount = available_usdt * Decimal('0.01')
        logging.info(f"Trade-Menge: {usdt_amount} USDT (1% des Kapitals)")

        # Prüfen, ob genügend USDT verfügbar ist
        if usdt_amount <= 0:
            logging.error("USDT-Menge ist 0 oder negativ.")
            raise ValueError("Ungültige USDT-Menge für den Trade")

        # Seite bestimmen (buy für LONG, sell für SHORT)
        side = 'buy' if direction == 'LONG' else 'sell'

        # Marktorder über trade.py platzieren
        logging.info(f"Platzieren einer {direction}-Marktorder für {usdt_amount} USDT")
        order = place_market_order(symbol, side, usdt_amount)
        logging.info(f"Order platziert: {order}")

    except Exception as e:
        logging.error(f"Fehler bei der Trade-Ausführung: {e}")
        raise
