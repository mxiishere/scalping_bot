import time
import re
from decimal import Decimal, InvalidOperation
from gmail_alert_reader import check_email_for_alerts
from logik import execute_trade
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")

def extract_trade_signal_from_email():
    """Gibt Liste der Alerts zurück, ggf. mit umgewandelten Zahlen als Decimal."""
    try:
        alerts = check_email_for_alerts()

        # Optional: Falls die Alerts Zahlen enthalten, in Decimal umwandeln
        converted_alerts = []
        for alert in alerts:
            # Beispielhafte Annahme: alert = {"direction": "BUY", "amount": "0.01"}
            if isinstance(alert, dict):
                new_alert = alert.copy()
                if "amount" in alert:
                    try:
                        new_alert["amount"] = Decimal(str(alert["amount"]))
                    except InvalidOperation:
                        log(f"⚠️ Ungültiger Dezimalwert: {alert['amount']}")
                        continue
                converted_alerts.append(new_alert)
            else:
                # Falls der Alert kein dict ist, einfach übernehmen
                converted_alerts.append(alert)

        return converted_alerts
    except Exception as e:
        log(f"Fehler beim Extrahieren des Signals: {e}")
        return None

def main_loop():
    log("🔁 Starte Hauptschleife zum E-Mail-Check und Trading...")
    while True:
        directions = extract_trade_signal_from_email()

        if directions:
            for direction in directions:
                log(f"📨 Signal erkannt: {direction}")
                execute_trade(direction)
        else:
            log("⏳ Keine neuen Signale gefunden.")

        time.sleep(5)

if __name__ == "__main__":
    main_loop()
