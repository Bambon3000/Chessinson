

import asyncio
import chess
from stockfish import Stockfish
from chess_translator import ChessCoordinateTranslator

STOCKFISH_PATH = r"D:\studium\Semester7\Embeded Systems\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"

class AsyncChessRobotController:
    def __init__(self):
        # Note: Stockfish doesn't have async methods natively
        # We'll run it in a thread pool for async operations
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
        
    def get_robot_move_sequence(self, uci_move):
        """Convert UCI move to robot movement sequence (synchronous)"""
        try:
            move_data = self.translator.parse_chess_move(uci_move)
            
            sequence = [
                {'x': move_data['from']['x'], 'y': move_data['from']['y'], 'z': 0.2, 'action': 'move'},
                {'x': move_data['from']['x'], 'y': move_data['from']['y'], 'z': 0.1, 'action': 'move'},
                {'action': 'grasp'},
                {'x': move_data['from']['x'], 'y': move_data['from']['y'], 'z': 0.2, 'action': 'move'},
                {'x': move_data['to']['x'], 'y': move_data['to']['y'], 'z': 0.2, 'action': 'move'},
                {'x': move_data['to']['x'], 'y': move_data['to']['y'], 'z': 0.1, 'action': 'move'},
                {'action': 'release'},
                {'x': move_data['to']['x'], 'y': move_data['to']['y'], 'z': 0.2, 'action': 'move'},
            ]
            
            return sequence
        except Exception as e:
            print(f"Error generating robot sequence for move {uci_move}: {e}")
            return []

    async def execute_robot_sequence(self, sequence):
        """Execute the robot movement sequence asynchronously"""
        for step in sequence:
            if step['action'] == 'move':
                # Simulate async movement (replace with actual robot async API calls)
                await self.async_move_robot(step['x'], step['y'], step['z'])
            elif step['action'] == 'grasp':
                await self.async_grasp()
            elif step['action'] == 'release':
                await self.async_release()
            # Small delay to simulate robot movement
            await asyncio.sleep(0.1)

    async def async_move_robot(self, x, y, z):
        """Async method to move robot (placeholder - implement your robot's async API)"""
        print(f"🤖 Robot moving to: x={x:.3f}, y={y:.3f}, z={z:.3f}")
        # Replace with actual async robot movement
        # Example: await robot.arm.async_move_to(x, y, z)
        await asyncio.sleep(0.5)  # Simulate movement time

    async def async_grasp(self):
        """Async method to grasp piece"""
        print("🤖 Robot grasping piece")
        await asyncio.sleep(0.3)  # Simulate grasp time

    async def async_release(self):
        """Async method to release piece"""
        print("🤖 Robot releasing piece")
        await asyncio.sleep(0.3)  # Simulate release time

    async def get_user_move_async(self):
        """Get a valid move from the user asynchronously"""
        while True:
            try:
                # Use asyncio's async input if available (Python 3.8+)
                user_input = await self.async_input("\nEnter your move (e.g., 'e2e4' or 'quit' to exit): ")
                
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
                # Get robot sequence
                sequence = self.get_robot_move_sequence(uci_move)
                if sequence:
                    print(f"🔧 Robot sequence for {uci_move}:")
                    for i, step in enumerate(sequence, 1):
                        if step['action'] == 'move':
                            print(f"  {i}. Move to ({step['x']:.3f}, {step['y']:.3f}, {step['z']:.3f})")
                        else:
                            print(f"  {i}. {step['action'].title()}")
                    
                    # Execute robot sequence asynchronously
                    await self.execute_robot_sequence(sequence)
                
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
            if hasattr(self, 'stockfish'):
                del self.stockfish
        except:
            pass

def print_board(board):
    """Print the chess board in a readable format"""
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
        print("\nGame started! Stockfish plays the first move.")
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
            if move_number == 1 or not chess_controller.board.turn:  # Black's turn (Stockfish)
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
                user_move = await chess_controller.get_user_move_async()
                
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
    
    # Test robot sequence generation
    if move:
        sequence = controller.get_robot_move_sequence(move)
        print(f"Robot sequence length: {len(sequence)}")
    
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