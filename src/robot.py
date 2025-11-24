from interbotix_common_modules.common_robot.robot import robot_shutdown, robot_startup
from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
from stockfish_main import ChessRobotController
import chess


"""
This script commands some arbitrary positions to the arm joints:

To get started, open a terminal and type:

    ros2 launch interbotix_xsarm_control xsarm_control.launch robot_model:=wx250s

Then change to this directory and type:

    python3 joint_position_control.py
"""

def execute_robot_sequence(bot, sequence):
    """Execute the robot movement sequence"""
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

def main():
    bot = InterbotixManipulatorXS(
        robot_model='wx250s',
        group_name='arm',
        moving_time=2.0,
        accel_time=1.0,
        gripper_name='gripper',
        gripper_pressure=2.5,
    )

    robot_startup()

    # Initialize robot to home position
    bot.arm.go_to_home_pose()
    bot.gripper.release()
    
    # Initialize chess controller
    chess_controller = ChessRobotController()
    
    print("Starting Chess Game with Robot:\n")
    
    move_number = 1
    # while not chess_controller.board.is_game_over():
    # Give current position to engine
    chess_controller.stockfish.set_fen_position(chess_controller.board.fen())
    
    # Get best move from Stockfish
    # best_move = chess_controller.stockfish.get_best_move()
    best_move = "e2e4"  # Example move for testing

    if best_move is None:
        print("Engine returned no move. Stopping.")
        # break
    
    print(f"Move {move_number}: {best_move} ({'White' if chess_controller.board.turn else 'Black'})")
    
    # Convert to robot coordinates and get movement sequence
    robot_sequence = chess_controller.get_robot_move_sequence(best_move)
    print(f"Executing robot sequence for move: {best_move}")
    
    # Execute the robot sequence
    execute_robot_sequence(bot, robot_sequence)
    
    # Apply move on chess board
    move = chess.Move.from_uci(best_move)
    if move not in chess_controller.board.legal_moves:
        print("Illegal move from engine:", move)
        # break
    
    chess_controller.board.push(move)
    
    print(chess_controller.board, "\n")
    move_number += 1
    
    print("Game over!")
    print("Result:", chess_controller.board.result())
    
    # Return to home and sleep position
    bot.arm.go_to_home_pose()
    bot.arm.go_to_sleep_pose()
    robot_shutdown()

if __name__ == '__main__':
    main()