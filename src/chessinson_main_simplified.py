import asyncio
import chess
from stockfish import Stockfish

from chess_translator import ChessCoordinateTranslator
from move_chess_piece import Chess_Robot
from speech_recognition import listen
from Lights import Light

STOCKFISH_PATH = "/home/ubuntu/stockfish/stockfish-android-armv8/stockfish/stockfish-android-armv8"


class AsyncChessRobotController:
    GERMAN_NUMBERS = {
        "eins": "1",
        "zwei": "2",
        "drei": "3",
        "vier": "4",
        "fünf": "5",
        "sechs": "6",
        "sieben": "7",
        "acht": "8",
    }

    def __init__(self):
        self.loop = asyncio.get_event_loop()

        self.board = chess.Board()
        self.translator = ChessCoordinateTranslator()

        self.robot = Chess_Robot()
        self.robot.startup()

        self.stockfish = Stockfish(
            path=STOCKFISH_PATH,
            depth=18,
            parameters={
                "Threads": 2,
                "Minimum Thinking Time": 30,
            },
        )

        # ✅ Lights via ESP32 Serial
        # Wenn Auto-Detect nicht klappt: Light(port="/dev/ttyUSB0")
        self.lights = Light(auto_connect=True)

    # ------------------------------------------------------------------ #
    # Robot control
    # ------------------------------------------------------------------ #

    async def execute_robot_move(self, uci_move: str) -> None:
        move = self.translator.parse_chess_move(uci_move)
        self.robot.robot_move(
            move["from"]["x"],
            move["to"]["x"],
            move["from"]["y"],
            move["to"]["y"],
        )
        await asyncio.sleep(0.1)

    async def execute_robot_take(self, uci_move: str) -> None:
        move = self.translator.parse_chess_move(uci_move)
        self.robot.robot_take(
            move["from"]["x"],
            move["to"]["x"],
            move["from"]["y"],
            move["to"]["y"],
        )
        await asyncio.sleep(0.1)

    async def make_move(self, uci_move: str) -> bool:
        move = chess.Move.from_uci(uci_move)
        print(f"Chess Move: {move}")

        if move not in self.board.legal_moves:
            print(f"❌ Illegal move: {uci_move}")
            # 🔴 illegal -> red blink
            self.lights.illegal()
            return False

        # 🟢 move in progress -> green blink
        self.lights.move()

        chess_piece_on_target = self.board.piece_at(move.to_square) is not None

        if chess_piece_on_target:
            await self.execute_robot_take(uci_move)
        else:
            await self.execute_robot_move(uci_move)

        self.board.push(move)
        return True

    # ------------------------------------------------------------------ #
    # User input
    # ------------------------------------------------------------------ #

    def spoken_to_uci(self, spoken: str) -> str | None:
        tokens = spoken.lower().split()
        cleaned = []

        for t in tokens:
            if t in "abcdefgh":
                cleaned.append(t)
            elif t in self.GERMAN_NUMBERS:
                cleaned.append(self.GERMAN_NUMBERS[t])

        return "".join(cleaned) if len(cleaned) == 4 else None

    async def get_user_move_speech(self) -> str | None:
        while True:
            # 🟢 ready for speech
            self.lights.ready()

            spoken = await self.loop.run_in_executor(None, listen)
            uci = self.spoken_to_uci(spoken)

            if not uci:
                print("❌ Could not understand move. Please repeat.")
                # 🟡 unknown speech
                self.lights.unknown()
                continue

            move = chess.Move.from_uci(uci)
            if move in self.board.legal_moves:
                return uci

            print(f"❌ Illegal move: {uci}")
            # 🔴 illegal
            self.lights.illegal()

    # ------------------------------------------------------------------ #
    # Stockfish
    # ------------------------------------------------------------------ #

    async def get_stockfish_move(self) -> str | None:
        def _get_best():
            self.stockfish.set_fen_position(self.board.fen())
            return self.stockfish.get_best_move()

        best = await self.loop.run_in_executor(None, _get_best)
        if not best:
            return None

        move = chess.Move.from_uci(best)
        if move not in self.board.legal_moves:
            return None

        print(f"🤖 Stockfish plays: {best}")
        return best

    # ------------------------------------------------------------------ #
    # Cleanup
    # ------------------------------------------------------------------ #

    def close(self):
        try:
            self.lights.off()
            self.lights.close()
        except Exception:
            pass

        self.robot.shutdown()
        del self.stockfish


def print_board(board: chess.Board):
    print("\n" + "-" * 33)
    for i, row in enumerate(str(board).splitlines()):
        print(f"{8 - i} | {row}")
    print("    " + "-" * 29)
    print("    a b c d e f g h")
    print("-" * 33)


async def main():
    controller = AsyncChessRobotController()
    move_number = 1

    print("\n🎮 ASYNC CHESS ROBOT GAME")
    print("You play White. Speak your moves.\n")

    try:
        while not controller.board.is_game_over():
            print_board(controller.board)
            print(f"\n📋 MOVE {move_number}")

            if controller.board.turn == chess.BLACK:
                print("🤖 Stockfish thinking...")
                move = await controller.get_stockfish_move()
            else:
                print("👤 Your turn...")
                move = await controller.get_user_move_speech()

            if not move:
                print("❌ No valid move. Game over.")
                break

            ok = await controller.make_move(move)
            if not ok:
                continue

            move_number += 1

        print("\n🏁 GAME OVER")
        print_board(controller.board)
        print(f"📊 Result: {controller.board.result()}")

    finally:
        controller.close()


if __name__ == "__main__":
    asyncio.run(main())

Dan pass den code an.

und passe auch mein Light.py an 
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
