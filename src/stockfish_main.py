from stockfish import Stockfish
import chess
from chess_translator import ChessCoordinateTranslator

STOCKFISH_PATH = r"D:\studium\Semester7\Embeded Systems\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"

class ChessRobotController:
    def __init__(self):
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
        
    def get_robot_move_sequence(self, uci_move):
        """Convert UCI move to robot movement sequence"""
        move_data = self.translator.parse_chess_move(uci_move)
        
        # Define movement sequence for the robot
        sequence = [
            # Move above the source square
            {'x': move_data['from']['x'], 'y': move_data['from']['y'], 'z': 0.2, 'action': 'move'},
            # Lower to pick up piece
            {'x': move_data['from']['x'], 'y': move_data['from']['y'], 'z': 0.1, 'action': 'move'},
            # Grasp piece
            {'action': 'grasp'},
            # Lift piece
            {'x': move_data['from']['x'], 'y': move_data['from']['y'], 'z': 0.2, 'action': 'move'},
            # Move above target square
            {'x': move_data['to']['x'], 'y': move_data['to']['y'], 'z': 0.2, 'action': 'move'},
            # Lower to place piece
            {'x': move_data['to']['x'], 'y': move_data['to']['y'], 'z': 0.1, 'action': 'move'},
            # Release piece
            {'action': 'release'},
            # Lift up
            {'x': move_data['to']['x'], 'y': move_data['to']['y'], 'z': 0.2, 'action': 'move'},
        ]
        
        return sequence

    def execute_robot_sequence(self, bot, sequence):
        """Execute the robot movement sequence (alternative method)"""
        for step in sequence:
            if step['action'] == 'move':
                bot.arm.set_ee_pose_components(
                    x=step['x'], 
                    y=step['y'], 
                    z=step['z'], 
                    roll=0.0, 
                    pitch=0.0, 
                    yaw=0.0
                )
            elif step['action'] == 'grasp':
                bot.gripper.grasp()
            elif step['action'] == 'release':
                bot.gripper.release()

# Keep the standalone main for testing if needed
def main():
    chess_controller = ChessRobotController()
    
    print("Starting Chess Game with Robot:\n")
    
    move_number = 1
    # while not chess_controller.board.is_game_over():
    #     chess_controller.stockfish.set_fen_position(chess_controller.board.fen())
        
    #     best_move = chess_controller.stockfish.get_best_move()
    #     if best_move is None:
    #         print("Engine returned no move. Stopping.")
    #         break
        
    #     print(f"Move {move_number}: {best_move} ({'White' if chess_controller.board.turn else 'Black'})")
        
    #     robot_sequence = chess_controller.get_robot_move_sequence(best_move)
    #     print(f"Robot sequence: {robot_sequence}")
        
    #     move = chess.Move.from_uci(best_move)
    #     if move not in chess_controller.board.legal_moves:
    #         print("Illegal move from engine:", move)
    #         break
        
    #     chess_controller.board.push(move)
    #     print(chess_controller.board, "\n")
    #     move_number += 1

    chess_controller.stockfish.set_fen_position(chess_controller.board.fen())
    
    best_move = chess_controller.stockfish.get_best_move()
    if best_move is None:
        print("Engine returned no move. Stopping.")
    
    print(f"Move {move_number}: {best_move} ({'White' if chess_controller.board.turn else 'Black'})")
    
    robot_sequence = chess_controller.get_robot_move_sequence(best_move)
    print(f"Robot sequence: {robot_sequence}")
    
    move = chess.Move.from_uci(best_move)
    if move not in chess_controller.board.legal_moves:
        print("Illegal move from engine:", move)
    
    chess_controller.board.push(move)
    print(chess_controller.board, "\n")
    move_number += 1
    
    print("Game over!")
    print("Result:", chess_controller.board.result())

if __name__ == "__main__":
    main()