import asyncio
import chess
from stockfish import Stockfish
from chess_translator import ChessCoordinateTranslator
from move_chess_piece import Chess_Robot
from speech_recognition import listen

# Path to Stockfish binary
STOCKFISH_PATH = "/home/ubuntu/stockfish/stockfish-android-armv8/stockfish/stockfish-android-armv8"


class AsyncChessRobotController:
    """
    Controls a physical chess-playing robot using asynchronous execution.

    Handles:
    - User input (speech or text)
    - Stockfish engine moves
    - Chess board state
    - Robot arm movement
    """

    def __init__(self):
        """Initialize robot, Stockfish engine, board, and event loop."""

        # Initialize robot hardware
        self.robot = Chess_Robot()
        self.robot.startup()

        # Initialize Stockfish chess engine
        self.stockfish = Stockfish(
            path=STOCKFISH_PATH,
            depth=18,
            parameters={
                "Threads": 2,
                "Minimum Thinking Time": 30
            }
        )

        # Create chess board representation
        self.board = chess.Board()

        # Coordinate translator for robot movement
        self.translator = ChessCoordinateTranslator()

        # Async event loop
        self.loop = asyncio.get_event_loop()

    async def execute_robot_sequence(self, uci_move):
        """
        Translate a chess move and command the robot to execute it.

        Parameters:
            uci_move (str): Move in UCI format (e.g., e2e4)
        """

        # Convert chess notation to robot coordinates
        move_data = self.translator.parse_chess_move(uci_move)

        from_x = move_data['from']['x']
        to_x   = move_data['to']['x']
        from_y = move_data['from']['y']
        to_y   = move_data['to']['y']

        # Send movement command to robot
        self.robot.robot_move(from_x, to_x, from_y, to_y)

        # Short pause to avoid blocking the event loop
        await asyncio.sleep(0.1)

    async def get_user_move_async(self):
        """
        Request a legal move from the user via keyboard input.

        Returns:
            str | None: UCI move string or None if user quits.
        """

        while True:
            try:
                # Run blocking input() in background thread
                user_input = await self.async_input(
                    "\nEnter your move (e.g., 'e2e4' or 'quit' to exit): "
                )

                print("Chess Board:" + self.board)

                # Exit condition
                if user_input.lower() == 'quit':
                    return None

                # Convert input to chess move
                user_move = chess.Move.from_uci(user_input)

                # Validate legality
                if user_move in self.board.legal_moves:
                    return user_input
                else:
                    print(f"Illegal move: {user_input}.")
                    legal_moves = list(self.board.legal_moves)

                    if legal_moves:
                        moves_str = ', '.join([move.uci() for move in legal_moves[:8]])
                        print(f"Legal moves: {moves_str}")

            except ValueError:
                print(f"Invalid move format: {user_input}.")
            except KeyboardInterrupt:
                print("\nGame interrupted by user.")
                return None
            except Exception as e:
                print(f"Error getting user input: {e}")
                return None

    async def async_input(self, prompt):
        """
        Non-blocking wrapper around Python's input().

        Parameters:
            prompt (str): Text shown to user.
        """

        return await self.loop.run_in_executor(None, input, prompt)

    # Mapping of German spoken numbers to digits
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

    def spoken_to_uci(self, spoken: str) -> str | None:
        """
        Convert spoken German chess coordinates into UCI notation.

        Parameters:
            spoken (str): Speech input.

        Returns:
            str | None: UCI string if valid, otherwise None.
        """

        tokens = spoken.lower().split()

        cleaned = []
        for t in tokens:
            if t in "abcdefgh":
                cleaned.append(t)
            elif t in self.GERMAN_NUMBERS:
                cleaned.append(self.GERMAN_NUMBERS[t])

        # Expect exactly four characters (e2e4)
        if len(cleaned) != 4:
            return None

        return "".join(cleaned)

    async def get_user_move_speech_async(self):
        """
        Obtain a legal move using speech recognition.

        Returns:
            str: Valid UCI move.
        """

        while True:
            try:
                # Run speech recognition in background thread
                spoken = await self.loop.run_in_executor(None, listen)

                # Convert speech to chess move
                uci = self.spoken_to_uci(spoken)
                if not uci:
                    print("❌ Could not understand move.")
                    continue

                move = chess.Move.from_uci(uci)

                # Validate move
                if move in self.board.legal_moves:
                    return uci
                else:
                    print(f"❌ Illegal move: {uci}.")

            except Exception as e:
                print(f"Speech recognition error: {e}")

    async def make_stockfish_move_async(self):
        """
        Query Stockfish asynchronously for the best move.

        Returns:
            str | None: Best UCI move or None on failure.
        """

        try:

            # Run Stockfish in separate thread
            def get_best_move():
                self.stockfish.set_fen_position(self.board.fen())
                return self.stockfish.get_best_move()

            best_move = await self.loop.run_in_executor(None, get_best_move)

            if best_move is None:
                print("Stockfish returned no move.")
                return None

            stockfish_move = chess.Move.from_uci(best_move)

            # Ensure engine move is legal
            if stockfish_move not in self.board.legal_moves:
                print(f"Stockfish suggested illegal move: {best_move}")
                legal_moves = list(self.board.legal_moves)

                if legal_moves:
                    alternative_move = legal_moves[0].uci()
                    print(f"Using alternative move: {alternative_move}")
                    return alternative_move

                return None

            print(f"🤖 Stockfish plays: {best_move}")
            return best_move

        except Exception as e:
            print(f"Error getting Stockfish move: {e}")
            return None

    async def make_move(self, uci_move):
        """
        Execute a move physically and update the chess board.

        Parameters:
            uci_move (str): Move in UCI format.

        Returns:
            bool: True if successful.
        """

        try:
            move = chess.Move.from_uci(uci_move)

            if move in self.board.legal_moves:

                # Command robot to move piece
                await self.execute_robot_sequence(uci_move)

                # Update internal board state
                self.board.push(move)

                return True

            else:
                print(f"Illegal move: {uci_move}")
                return False

        except Exception as e:
            print(f"Error making move {uci_move}: {e}")
            return False

    def close(self):
        """
        Shut down robot.
        """

        try:
            if hasattr(self, 'robot'):
                self.robot.shutdown()

            if hasattr(self, 'stockfish'):
                del self.stockfish

        except Exception as e:
            print(f"Error during shutdown: {e}")


def print_board(board):
    """
    Print the chess board with coordinates.

    Parameters:
        board (chess.Board): Board to display.
    """

    print(board)
    print("\n" + "-" * 33)

    board_str = str(board)
    lines = board_str.split('\n')

    for i, line in enumerate(lines):
        print(f"{8-i} | {line}")

    print("    " + "-" * 29)
    print("    a b c d e f g h")
    print("-" * 33)


async def main():
    """
    Main asynchronous game loop.
    """

    chess_controller = None

    try:
        chess_controller = AsyncChessRobotController()

        print("=" * 50)
        print("🎮 ASYNC CHESS ROBOT GAME")
        print("=" * 50)

        move_number = 1

        # Primary game loop
        while not chess_controller.board.is_game_over():

            print_board(chess_controller.board)

            # Black = Stockfish
            if chess_controller.board.turn == chess.BLACK:

                stockfish_move = await chess_controller.make_stockfish_move_async()

                if stockfish_move is None:
                    break

                await chess_controller.make_move(stockfish_move)

            # White = User
            else:

                user_move = await chess_controller.get_user_move_speech_async()

                if user_move is None:
                    break

                await chess_controller.make_move(user_move)

            move_number += 1

    finally:
        if chess_controller:
            chess_controller.close()


if __name__ == "__main__":
    asyncio.run(main())
