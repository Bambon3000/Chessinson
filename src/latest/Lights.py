# lights.py
import time
import threading

from typing import Optional

import serial
from serial.tools import list_ports


class Light:
    """
    Steuert den ESP32 LED Controller über USB-Serial.

    ESP32 Commands (laut Boot Output):
      red_on/red_off, yellow_on/yellow_off, green_on/green_off, all_off

    READY  -> green_on (dauerhaft)
    MOVE   -> green blink (Hintergrund-Thread)
    ILLEGAL-> red blink   (Hintergrund-Thread)
    UNKNOWN-> yellow blink( Hinterg.-Thread)
    OFF    -> all_off
    """

    def __init__(
        self,
        port: str= "/dev/ttyUSB1",
        baudrate: int = 115200,
        auto_connect: bool = True,
        boot_wait: float = 1.5,
    ):
        self.baudrate = baudrate
        self.port = port
        self.boot_wait = boot_wait

        self.ser: Optional[serial.Serial] = None
        self._lock = threading.Lock()

        # Blink worker
        self._blink_thread: Optional[threading.Thread] = None
        self._stop_blink = threading.Event()

        if auto_connect:
            self.connect()

    # ------------------------
    # Serial Connection
    # ------------------------
    def _auto_detect_port(self) -> Optional[str]:
        candidates = []
        for p in list_ports.comports():
            dev = p.device
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()

            if any(x in desc for x in ["cp210", "ch340", "usb serial", "uart", "ftdi"]) or \
               any(x in hwid for x in ["cp210", "ch340", "ftdi"]):
                candidates.append(dev)

        # Fallback typische Namen
        if not candidates:
            for dev in ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyUSB1", "/dev/ttyACM1"]:
                candidates.append(dev)

        for dev in candidates:
            try:
                ser = serial.Serial(port, self.baudrate, timeout=0.2)
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
                "Setze port='/dev/ttyUSB0' oder prüfe `ls -l /dev/ttyUSB* /dev/ttyACM*`."
            )

        self.ser = serial.Serial(port, self.baudrate, timeout=0.2)
        self.port = port

        # Reset vermeiden (bei vielen ESP32 Boards relevant)
        try:
            self.ser.setDTR(False)
            self.ser.setRTS(False)
        except Exception:
            pass

        time.sleep(self.boot_wait)
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except Exception:
            pass

    def close(self) -> None:
        self._stop_blinking()
        if self.ser and self.ser.is_open:
            self.ser.close()

    # ------------------------
    # Low-level send
    # ------------------------
    def _send(self, cmd: str) -> None:
        """
        Sendet einen Command an den ESP32.
        """
        with self._lock:
            if not self.ser or not self.ser.is_open:
                self.connect()

            data = (cmd + "\n").encode("utf-8")
            try:
                self.ser.write(data)
                self.ser.flush()
            except Exception:
                # Reconnect 1x
                try:
                    self.close()
                except Exception:
                    pass
                self.connect()
                self.ser.write(data)
                self.ser.flush()

    # ------------------------
    # Blinking (non-blocking)
    # ------------------------
    def _stop_blinking(self):
        self._stop_blink.set()
        t = self._blink_thread
        if t and t.is_alive():
            t.join(timeout=1.0)
        self._blink_thread = None
        self._stop_blink.clear()

    def _start_blink(self, on_cmd: str, off_cmd: str, on: float = 0.15, off: float = 0.15):
        self._stop_blinking()

        def worker():
            while not self._stop_blink.is_set():
                self._send(on_cmd)
                if self._stop_blink.wait(on):
                    break
                self._send(off_cmd)
                if self._stop_blink.wait(off):
                    break

        self._blink_thread = threading.Thread(target=worker, daemon=True)
        self._blink_thread.start()

    # ------------------------
    # Public high-level states
    # ------------------------
    def off(self) -> None:
        self._stop_blinking()
        self._send("all_off")

    def speach_ready(self) -> None:

        self._stop_blinking()
        self._send("all_off")
        self._send("green_on")
        
    def ready(self) -> None:
        # Grün dauerhaft
        self._stop_blinking()
        self._send("all_off")
        self._send("yellow_on")

    def move(self) -> None:
        # Grün blinkt
        self._send("all_off")
        self._start_blink("green_on", "green_off")

    def illegal(self) -> None:
        # Rot 
        self._stop_blinking()
        self._send("all_off")
        self._send("red_on")

    def unknown(self) -> None:
        # Gelb 
        self._stop_blinking()
        self._send("all_off")
        self._send("yellow_on")
