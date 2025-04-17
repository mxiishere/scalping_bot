import pandas as pd
import requests
import time
from datetime import datetime, timedelta, UTC
import logging

# Logging einrichten
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from decimal import Decimal, getcontext

# Genauigkeit erhöhen (optional)
getcontext().prec = 10

def calculate_vwap_last_60(df):
    """
    Berechnet den VWAP basierend auf den letzten 60 Kerzen im DataFrame.
    Nutzt Decimal für präzisere Berechnung.
    """
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame muss die Spalten {required_columns} enthalten.")
    
    if df[required_columns].isnull().any().any():
        raise ValueError("DataFrame enthält fehlende Werte in den erforderlichen Spalten.")
    
    if len(df) < 60:
        raise ValueError(f"Nicht genügend Daten: Weniger als 60 Kerzen verfügbar, erhalten: {len(df)}")
    
    df_last_60 = df.tail(60).copy()

    # Umwandlung in Decimal-Spalten
    df_last_60['TP'] = df_last_60.apply(
        lambda row: (Decimal(str(row['High'])) + Decimal(str(row['Low'])) + Decimal(str(row['Close']))) / Decimal('3'),
        axis=1
    )
    df_last_60['Volume'] = df_last_60['Volume'].apply(lambda x: Decimal(str(x)))
    df_last_60['TPV'] = df_last_60['TP'] * df_last_60['Volume']

    vwap = df_last_60['TPV'].sum() / df_last_60['Volume'].sum()
    return float(vwap)  # Optional: Rückgabe als float oder Decimal

def fetch_bitget_klines(symbol="BTCUSDT", granularity="1m", num_candles=60):
    """
    Ruft die neuesten historischen Kerzendaten von der Bitget API ab.
    
    Parameter:
    - symbol (str): Handelspaar, z. B. 'BTCUSDT'.
    - granularity (str): Zeitintervall, z. B. '1m' für 1 Minute.
    - num_candles (int): Anzahl der Kerzen, die abgerufen werden sollen (Standard: 60).
    
    Rückgabe:
    - pd.DataFrame: DataFrame mit den Spalten 'Open', 'High', 'Low', 'Close', 'Volume'.
    """
    base_url = "https://api.bitget.com/api/v2/mix/market/candles"
    
    # Aktuelle Zeit in UTC
    current_time = datetime.now(UTC)
    
    logging.info(f"Fetching {num_candles} candles, current time: {current_time}")
    
    params = {
        "symbol": symbol,
        "granularity": granularity,
        "productType": "usdt-futures",
        "limit": num_candles
    }
    
    try:
        logging.info(f"Making API request: {params}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != "00000":
            raise Exception(f"API-Fehler: {data.get('msg')}")
        
        klines = data.get("data", [])
        if not klines:
            raise Exception("Keine Daten von der API erhalten.")
        
        # In DataFrame umwandeln
        df = pd.DataFrame(klines, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume", "QuoteVolume"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"].astype(float), unit="ms", utc=True)
        df[["Open", "High", "Low", "Close", "Volume"]] = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
        df.set_index("Timestamp", inplace=True)
        df.sort_index(inplace=True)
        df.drop(columns=["QuoteVolume"], inplace=True)
        
        # Überprüfen, ob die Daten aktuell sind (max. 2 Minuten Verzögerung)
        latest_candle_time = df.index[-1]
        time_diff = current_time - latest_candle_time
        if time_diff > timedelta(minutes=2):
            logging.warning(f"Daten sind nicht aktuell! Neueste Kerze: {latest_candle_time}, aktuelle Zeit: {current_time}")
            return None
        
        logging.info(f"Erfolgreich {len(df)} Kerzen abgerufen. Zeitraum: {df.index[0]} bis {df.index[-1]}")
        return df
    
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Daten: {e}")
        return None

# Hauptprogramm
if __name__ == "__main__":
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    try:
        while True:
            # Kerzendaten von Bitget abrufen
            df = fetch_bitget_klines(num_candles=60)
            
            if df is not None and not df.empty:
                consecutive_errors = 0  # Zurücksetzen bei Erfolg
                try:
                    # VWAP für die letzten 60 Kerzen berechnen
                    vwap = calculate_vwap_last_60(df)
                    logging.info(f"\nVWAP der letzten 60 Kerzen: {vwap}")
                    
                    # Letzte 10 Kerzen anzeigen
                    logging.info("\nLetzte 10 Kerzen mit Close:")
                    print(df[["Close"]].tail(10))
                except Exception as e:
                    logging.error(f"Fehler bei der VWAP-Berechnung: {e}")
                    consecutive_errors += 1
            else:
                consecutive_errors += 1
                logging.error("Keine Daten verfügbar, um den VWAP zu berechnen.")
            
            # Überprüfen, ob zu viele aufeinanderfolgende Fehler
            if consecutive_errors >= max_consecutive_errors:
                logging.error(f"Zu viele aufeinanderfolgende Fehler ({consecutive_errors}). Programm wird beendet.")
                break
            
            # Warte 10 Sekunden bis zur nächsten Berechnung
            logging.info(f"Warte 10 Sekunden bis zur nächsten Berechnung... (Fehlerzähler: {consecutive_errors}/{max_consecutive_errors})")
            time.sleep(10)
            
    except KeyboardInterrupt:
        logging.info("Programm durch Benutzer gestoppt.")
