# lights.py
import time
import threading
from typing import Optional

import serial
from serial.tools import list_ports


class Light:
    """
    ESP32 LED Controller via USB-Serial.

    ESP32 versteht:
      red_on / red_off
      yellow_on / yellow_off
      green_on / green_off
      all_off

    Logik:
      READY    -> grün dauerhaft (solltest du NUR während "listen" setzen)
      MOVE     -> grün blinkt (non-blocking)
      ILLEGAL  -> rot dauerhaft (X Sekunden), dann OFF
      UNKNOWN  -> gelb dauerhaft (X Sekunden), dann OFF
      OFF      -> alles aus
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        auto_connect: bool = True,
        boot_wait: float = 1.5,
        hold_seconds: float = 2.5,  # ⏱️ Dauer für rot/gelb
    ):
        self.port = port
        self.baudrate = baudrate
        self.boot_wait = boot_wait
        self.hold_seconds = hold_seconds

        self.ser: Optional[serial.Serial] = None
        self._lock = threading.Lock()

        # Blink-Thread
        self._blink_thread: Optional[threading.Thread] = None
        self._stop_blink = threading.Event()

        # Timer für rot/gelb
        self._timer: Optional[threading.Timer] = None

        if auto_connect:
            self.connect()

    # ------------------------------------------------------------------
    # Serial Connection
    # ------------------------------------------------------------------

    def _auto_detect_port(self) -> Optional[str]:
        candidates = []

        for p in list_ports.comports():
            dev = p.device
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()

            if any(x in desc for x in ["cp210", "ch340", "usb serial", "uart", "ftdi"]) or \
               any(x in hwid for x in ["cp210", "ch340", "ftdi"]):
                candidates.append(dev)

        # Fallback
        if not candidates:
            candidates = [
                "/dev/ttyUSB0",
                "/dev/ttyACM0",
                "/dev/ttyUSB1",
                "/dev/ttyACM1",
            ]

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
                "Setze port='/dev/ttyUSB0' oder prüfe `ls -l /dev/ttyUSB* /dev/ttyACM*`."
            )

        self.ser = serial.Serial(port, self.baudrate, timeout=0.2)
        self.port = port

        # Reset vermeiden
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
        self._cancel_timer()
        if self.ser and self.ser.is_open:
            self.ser.close()

    # ------------------------------------------------------------------
    # Low-level send
    # ------------------------------------------------------------------

    def _send(self, cmd: str) -> None:
        with self._lock:
            if not self.ser or not self.ser.is_open:
                self.connect()

            try:
                self.ser.write((cmd + "\n").encode("utf-8"))
                self.ser.flush()
            except Exception:
                # einmal reconnect versuchen
                self.close()
                self.connect()
                self.ser.write((cmd + "\n").encode("utf-8"))
                self.ser.flush()

    # ------------------------------------------------------------------
    # Blink handling (non-blocking)
    # ------------------------------------------------------------------

    def _stop_blinking(self):
        self._stop_blink.set()
        if self._blink_thread and self._blink_thread.is_alive():
            self._blink_thread.join(timeout=1.0)
        self._blink_thread = None
        self._stop_blink.clear()

    def _start_blink(
        self,
        on_cmd: str,
        off_cmd: str,
        on_time: float = 0.15,
        off_time: float = 0.15,
    ):
        self._stop_blinking()

        def worker():
            while not self._stop_blink.is_set():
                self._send(on_cmd)
                if self._stop_blink.wait(on_time):
                    break
                self._send(off_cmd)
                if self._stop_blink.wait(off_time):
                    break

        self._blink_thread = threading.Thread(target=worker, daemon=True)
        self._blink_thread.start()

    # ------------------------------------------------------------------
    # Timer handling (rot/gelb halten -> dann OFF)
    # ------------------------------------------------------------------

    def _cancel_timer(self):
        if self._timer:
            try:
                self._timer.cancel()
            except Exception:
                pass
            self._timer = None

    def _hold_then_off(self):
        self._cancel_timer()

        def back_to_off():
            self.off()

        self._timer = threading.Timer(self.hold_seconds, back_to_off)
        self._timer.daemon = True
        self._timer.start()

    # ------------------------------------------------------------------
    # Public States
    # ------------------------------------------------------------------

    def off(self) -> None:
        self._stop_blinking()
        self._cancel_timer()
        self._send("all_off")

    def ready(self) -> None:
        # Grün dauerhaft (nur setzen, wenn wirklich gesprochen werden kann)
        self._stop_blinking()
        self._cancel_timer()
        self._send("all_off")
        self._send("green_on")

    def move(self) -> None:
        # Grün blinkt
        self._cancel_timer()
        self._send("all_off")
        self._start_blink("green_on", "green_off")

    def illegal(self) -> None:
        # Rot dauerhaft für X Sekunden, dann OFF
        self._stop_blinking()
        self._cancel_timer()
        self._send("all_off")
        self._send("red_on")
        self._hold_then_off()

    def unknown(self) -> None:
        # Gelb dauerhaft für X Sekunden, dann OFF
        self._stop_blinking()
        self._cancel_timer()
        self._send("all_off")
        self._send("yellow_on")
        self._hold_then_off()
