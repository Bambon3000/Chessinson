import asyncio
import chess
from stockfish import Stockfish
from chess_translator import ChessCoordinateTranslator
from move_chess_piece import Chess_Robot
from speech_recognition import listen

STOCKFISH_PATH = "/home/ubuntu/stockfish/stockfish-android-armv8/stockfish/stockfish-android-armv8"

class AsyncChessRobotController:
    def __init__(self):
        self.robot = Chess_Robot()
        self.robot.startup()

        self.stockfish = Stockfish(
            path=STOCKFISH_PATH,
            depth=18,
            parameters={
                "Threads": 2,
                "Minimum Thinking Time": 30
            }
        )
        self.board = chess.Board()
        self.translator = ChessCoordinateTranslator()
        self.loop = asyncio.get_event_loop()

    async def execute_robot_sequence(self, uci_move):
        move_data = self.translator.parse_chess_move(uci_move)

        from_x = move_data['from']['x']
        to_x   = move_data['to']['x']
        from_y = move_data['from']['y']
        to_y   = move_data['to']['y']

        self.robot.robot_move(from_x, to_x, from_y, to_y)

        await asyncio.sleep(0.1)

    async def get_user_move_async(self):
        """Get a valid move from the user asynchronously"""
        while True:
            try:
                # Use asyncio's async input if available (Python 3.8+)
                user_input = await self.async_input("\nEnter your move (e.g., 'e2e4' or 'quit' to exit): ")
                print("Chess Board:" + self.board)
                
                if user_input.lower() == 'quit':
                    return None
                
                # Convert user input to chess move
                user_move = chess.Move.from_uci(user_input)
                
                # Check if the move is legal
                if user_move in self.board.legal_moves:
                    return user_input
                else:
                    print(f"Illegal move: {user_input}. Please enter a valid move.")
                    legal_moves = list(self.board.legal_moves)
                    if legal_moves:
                        moves_str = ', '.join([move.uci() for move in legal_moves[:8]])
                        print(f"Legal moves: {moves_str}")
            except ValueError:
                print(f"Invalid move format: {user_input}. Please use UCI format.")
            except KeyboardInterrupt:
                print("\nGame interrupted by user.")
                return None
            except Exception as e:
                print(f"Error getting user input: {e}")
                return None

    async def async_input(self, prompt):
        """Async wrapper for input()"""
        return await self.loop.run_in_executor(None, input, prompt)
        
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
        tokens = spoken.lower().split()

        cleaned = []
        for t in tokens:
            if t in "abcdefgh":
                cleaned.append(t)
            elif t in self.GERMAN_NUMBERS:
                cleaned.append(self.GERMAN_NUMBERS[t])

        if len(cleaned) != 4:
            return None

        return "".join(cleaned)
        
    async def get_user_move_speech_async(self):
        """Get a valid move from speech recognition"""
        while True:
            try:
                spoken = await self.loop.run_in_executor(None, listen)

                uci = self.spoken_to_uci(spoken)
                if not uci:
                    print("❌ Could not understand move. Please repeat.")
                    continue

                move = chess.Move.from_uci(uci)
                if move in self.board.legal_moves:
                    return uci
                else:
                    print(f"❌ Illegal move: {uci}. Please repeat.")

            except Exception as e:
                print(f"Speech recognition error: {e}")

    async def make_stockfish_move_async(self):
        """Get Stockfish's move asynchronously using thread pool"""
        try:
            # Run Stockfish in thread pool since it's synchronous
            def get_best_move():
                self.stockfish.set_fen_position(self.board.fen())
                return self.stockfish.get_best_move()
            
            best_move = await self.loop.run_in_executor(None, get_best_move)
            
            if best_move is None:
                print("Stockfish returned no move.")
                return None
            
            stockfish_move = chess.Move.from_uci(best_move)
            
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
        """Make a move on the board and execute robot sequence"""
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                # Execute robot sequence asynchronously
                await self.execute_robot_sequence(uci_move)
                
                # Make the move on the board
                self.board.push(move)
                return True
            else:
                print(f"Illegal move: {uci_move}")
                return False
        except Exception as e:
            print(f"Error making move {uci_move}: {e}")
            return False

    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'robot'):
                self.robot.shutdown()
            if hasattr(self, 'stockfish'):
                del self.stockfish
        except Exception as e:
            print(f"Error during shutdown: {e}")

def print_board(board):
    """Print the chess board in a readable format"""
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
    chess_controller = None
    try:
        chess_controller = AsyncChessRobotController()
        
        print("=" * 50)
        print("🎮 ASYNC CHESS ROBOT GAME")
        print("=" * 50)
        print("\nGame started! You play the first move.")
        print("Enter moves in UCI format (e.g., 'e2e4', 'g1f3')")
        print("Type 'quit' to exit the game.\n")
        
        move_number = 1
        
        # Game loop
        while not chess_controller.board.is_game_over():
            print(f"\n{'='*50}")
            print(f"📋 MOVE {move_number}")
            print(f"Current turn: {'White' if chess_controller.board.turn else 'Black'}")
            print(f"{'='*50}")
            
            # Always print the board
            print_board(chess_controller.board)
            
            # Determine whose turn it is
            if chess_controller.board.turn == chess.BLACK:  # Black's turn (Stockfish)
                print("\n🤖 Stockfish's turn...")
                # Let Stockfish think asynchronously
                print("💭 Stockfish is thinking...")
                stockfish_move = await chess_controller.make_stockfish_move_async()
                
                if stockfish_move is None:
                    print("❌ No valid move from Stockfish. Game over.")
                    break
                
                # Execute Stockfish's move with robot
                print("🚀 Executing Stockfish's move with robot...")
                success = await chess_controller.make_move(stockfish_move)
                if not success:
                    print("❌ Failed to execute Stockfish's move")
                    break
                    
            else:  # White's turn (User)
                print("\n👤 Your turn!")
                user_move = await chess_controller.get_user_move_speech_async()
                
                if user_move is None:
                    print("👋 Game ended by user.")
                    break
                
                # Execute user's move with robot
                print(f"🚀 Executing your move {user_move} with robot...")
                success = await chess_controller.make_move(user_move)
                if not success:
                    print("❌ Failed to execute your move")
                    continue
                
                # Check if game is over after user's move
                if chess_controller.board.is_game_over():
                    break
            
            move_number += 1
        
        # Game over
        print("\n" + "="*50)
        print("🏁 GAME OVER")
        print("="*50)
        print("\nFinal board position:")
        print_board(chess_controller.board)
        
        result = chess_controller.board.result()
        print(f"\n📊 Game result: {result}")
        
        if chess_controller.board.is_checkmate():
            winner = "Black" if chess_controller.board.turn else "White"
            print(f"👑 Checkmate! {winner} wins!")
        elif chess_controller.board.is_stalemate():
            print("🤝 Stalemate! Draw!")
        elif chess_controller.board.is_insufficient_material():
            print("♟️ Draw by insufficient material!")
        
        print(f"📈 Total moves played: {move_number - 1}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Game interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if chess_controller:
            chess_controller.close()

async def quick_test():
    """Quick test function to verify async functionality"""
    print("🧪 Testing async chess game...")
    controller = AsyncChessRobotController()
    
    # Test Stockfish async move
    print("Testing async Stockfish move...")
    move = await controller.make_stockfish_move_async()
    print(f"Stockfish move: {move}")
    
    controller.close()
    print("✅ Test completed!")

if __name__ == "__main__":
    # Run quick test first if needed
    # asyncio.run(quick_test())
    
    # Run the main async game
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Game stopped.")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
