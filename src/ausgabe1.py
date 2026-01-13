import serial
import time

PORT = "/dev/ttyUSB1"  # Dein ESP32-Port
BAUDRATE = 115200      # Muss mit ESP32 übereinstimmen
TIMEOUT = 1            # Sekunden

try:
    # Serielle Verbindung öffnen
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
    time.sleep(2)  # ESP32 braucht kurz, um bereit zu sein
    print(f"✓ Verbindung hergestellt zu {PORT}")

    print("Starte Datenempfang... (Strg+C zum Beenden)")
    while True:
        if ser.in_waiting:
            print("wir sind in waiting")
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
               print("Hier sind wir in IF ")
               print(f"ESP32: {line}")

except serial.SerialException as e:
    print(f"Fehler bei der seriellen Verbindung: {e}")

except KeyboardInterrupt:
    print("\nBeendet durch Benutzer")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serielle Verbindung geschlossen")
