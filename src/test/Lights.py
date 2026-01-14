# lights.py
import time
import threading
from typing import Optional

import serial
from serial.tools import list_ports


class Light:
    """
    Sendet LED-States via USB-Serial an den ESP32.
    ESP32 kümmert sich um Blinken/Leuchten (State-Machine).
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        auto_connect: bool = True,
    ):
        self.baudrate = baudrate
        self.port = port
        self.ser: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._last_state: Optional[str] = None

        if auto_connect:
            self.connect()

    # ------------------------
    # Serial Connection
    # ------------------------
    def _auto_detect_port(self) -> Optional[str]:
        """
        Versucht einen passenden Serial-Port zu finden.
        Typisch am Raspberry Pi: /dev/ttyUSB0 oder /dev/ttyACM0
        """
        candidates = []
        for p in list_ports.comports():
            dev = p.device  # z.B. /dev/ttyUSB0
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()

            # Häufige ESP32 USB-UART Chips: CP210x, CH340, FTDI
            if any(x in desc for x in ["cp210", "ch340", "usb serial", "uart", "ftdi"]) or \
               any(x in hwid for x in ["cp210", "ch340", "ftdi"]):
                candidates.append(dev)

        # Fallback: wenn nix erkannt wurde, nimm typische Namen falls vorhanden
        if not candidates:
            for dev in ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyUSB1", "/dev/ttyACM1"]:
                candidates.append(dev)

        # Nimm den ersten, der sich öffnen lässt
        for dev in candidates:
            try:
                s = serial.Serial(dev, self.baudrate, timeout=0.2)
                s.close()
                return dev
            except Exception:
                continue

        return None

    def connect(self) -> None:
        if self.ser and self.ser.is_open:
            return

        port = self.port or self._auto_detect_port()
        if not port:
            raise RuntimeError(
                "Kein ESP32-Serial-Port gefunden. "
                "Setze port='/dev/ttyUSB0' oder prüfe `ls /dev/tty*`."
            )

        self.ser = serial.Serial(port, self.baudrate, timeout=0.2)
        self.port = port

        # Kurz warten, damit ESP32 nach Serial-Open stabil ist
        time.sleep(0.2)

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()

    # ------------------------
    # State Commands
    # ------------------------
    def _send(self, line: str) -> None:
        """
        Sendet eine Zeile inkl. Newline an den ESP32.
        Dedupe: wenn State gleich bleibt, wird nicht erneut gesendet.
        """
        with self._lock:
            if line == self._last_state:
                return

            if not self.ser or not self.ser.is_open:
                self.connect()

            data = (line + "\n").encode("utf-8")

            try:
                self.ser.write(data)
                self.ser.flush()
                self._last_state = line
            except Exception:
                # Reconnect 1x
                try:
                    self.close()
                except Exception:
                    pass
                self.connect()
                self.ser.write(data)
                self.ser.flush()
                self._last_state = line

    def off(self) -> None:
        self._send("STATE OFF")

    def ready(self) -> None:
        # Grün dauerhaft: bereit für Spracheingabe
        self._send("STATE READY")

    def move(self) -> None:
        # Grün blinkt: Arm bewegt sich
        self._send("STATE MOVE")

    def illegal(self) -> None:
        # Rot blinkt: illegaler Zug
        self._send("STATE ILLEGAL")

    def unknown(self) -> None:
        # Gelb blinkt: Spracheingabe nicht verstanden
        self._send("STATE UNKNOWN")
