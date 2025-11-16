from stockfish import Stockfish
import chess
# python chess library docu: https://pypi.org/project/stockfish/
STOCKFISH_PATH = r"D:\studium\Semester7\Embeded Systems\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"

# Start Stockfish engine
stockfish = Stockfish(
    path=STOCKFISH_PATH,
    depth=18,
    parameters={
        "Threads": 2,
        "Minimum Thinking Time": 30
    }
)

# Internal board manager
board = chess.Board() 

print("Starting Stockfish vs Stockfish:\n")

# Simulate game
move_number = 1
while not board.is_game_over():

    # give current position to engine
    stockfish.set_fen_position(board.fen())

    # ask engine for best move
    best_move = stockfish.get_best_move()
    if best_move is None:
        print("Engine returned no move. Stopping.")
        break

    print(f"Move {move_number}: {best_move} ({'White' if board.turn else 'Black'})")

    # apply move on board
    move = chess.Move.from_uci(best_move)
    if move not in board.legal_moves:
        print("Illegal move from engine:", move)
        break

    board.push(move)

    print(board, "\n")

    move_number += 1

print("Game over!")
print("Result:", board.result())
