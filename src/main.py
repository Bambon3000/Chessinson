import requests
import chess
import time

API_URL = "https://stockfish.online/api/s/v2.php"

# Dummy starting position (normal chess start)
board = chess.Board()

def get_best_move(fen, depth=15):
    params = {
        "fen": fen,
        "depth": depth
    }

    response = requests.get(API_URL, params=params)
    data = response.json()

    if not data.get("success"):
        print("API error:", data)
        return None

    # Example: "bestmove e2e4 ponder e7e5"
    bestmove_text = data["bestmove"]
    bestmove = bestmove_text.split()[1]    # "e2e4"

    return bestmove

print("Starting dummy console chess vs Stockfish Online.\n")

while not board.is_game_over():

    print("Current Position (FEN):")
    print(board.fen())
    print(board)

    # Ask Stockfish for next move
    fen = board.fen()
    bestmove = get_best_move(fen)

    if bestmove is None:
        print("No move returned, stopping.")
        break

    print("Stockfish plays:", bestmove)

    move = chess.Move.from_uci(bestmove)

    # Make sure the move is legal
    if move not in board.legal_moves:
        print("Illegal move received:", move)
        break

    board.push(move)

    # Slow down printing (optional)
    time.sleep(1)

print("\nGame Over:", board.result())
