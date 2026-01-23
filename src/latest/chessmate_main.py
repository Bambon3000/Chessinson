import asyncio
import chess
from stockfish import Stockfish

from chess_translator import ChessCoordinateTranslator
from move_chess_piece import Chess_Robot
from speech_recognition import listen
from Lights import Light

STOCKFISH_PATH = "/home/ubuntu/stockfish/stockfish-android-armv8/stockfish/stockfish-android-armv8"

# start venv 
# source venv/bin/activate

# start chess:
# python3 chessmate_main.py

# test without robot 
# ros2 launch interbotix_xsarm_control xsarm_control.launch.py robot_model:=wx250s use_sim:=true

# start robot (without RViz, saves RAM and frames per second)
# ros2 launch interbotix_xsarm_control xsarm_control.launch.py robot_model:=wx250s use_rviz:=false

# check if port is free: <lsof /dev/ttyUSB0> or with <lsof /dev/ttyUSB1>


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

        self.lights = Light()

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
        try:
            move = chess.Move.from_uci(uci_move)
            print(f"Chess Move: {move}")

        except (ValueError, chess.InvalidMoveError):
            print(f"❌ Invalid UCI: {uci_move}")
            self.lights.illegal()
            await asyncio.sleep(2.5)
            return False

        if move not in self.board.legal_moves:
            print(f"❌ Illegal move: {uci_move}")
            self.lights.illegal()
            await asyncio.sleep(2.5)
            return False

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

            spoken = await self.loop.run_in_executor(None, listen)
            uci = self.spoken_to_uci(spoken)

            if not uci:
                print("❌ Could not understand move. Please repeat.")
                self.lights.unknown()
                await asyncio.sleep(2.5)
                continue

            try:
                move = chess.Move.from_uci(uci)
            except (ValueError, chess.InvalidMoveError):
                print(f"❌ Invalid UCI format: {uci}")
                self.lights.illegal()
                await asyncio.sleep(2.5)
                continue

            if move in self.board.legal_moves:
                return uci

            print(f"❌ Illegal move: {uci}")
            self.lights.illegal()
            await asyncio.sleep(2.5)

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

    async def close(self):
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
    print("You play White. Say your moves.\n")

    try:
        while not controller.board.is_game_over():
            print_board(controller.board)
            print(f"\n📋 MOVE {move_number}")

            if controller.board.turn == chess.BLACK:
                print("🤖 Stockfish is thinking...")
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
        await controller.close()


if __name__ == "__main__":
    asyncio.run(main())
