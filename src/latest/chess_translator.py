# chess_translator.py

class ChessCoordinateTranslator:
    def __init__(self):
        # File (letter) to Y coordinate mapping
        self.file_to_y = {
            '1': -0.187, '2': -0.132, '3': -0.073, '4': -0.022,
            '5': 0.022, '6': 0.073, '7': 0.132, '8': 0.187
        }
        
        # Rank (number) to X coordinate mapping  
        self.rank_to_x = {
            'a': 0.2, 'b': 0.25, 'c': 0.3, 'd': 0.35,
            'e': 0.4, 'f': 0.45, 'g': 0.5, 'h': 0.55
        }
    
    def chess_to_robot_coords(self, chess_square):
        """Convert chess square (e.g., 'e2') to robot coordinates (x, y)"""
        if len(chess_square) != 2:
            raise ValueError(f"Invalid chess square: {chess_square}")
        
        rank_char = chess_square[0].lower()
        file_char = chess_square[1]
        
        if file_char not in self.file_to_y:
            raise ValueError(f"Invalid file: {file_char}")
        if rank_char not in self.rank_to_x:
            raise ValueError(f"Invalid rank: {rank_char}")
        
        x = self.rank_to_x[rank_char]
        y = self.file_to_y[file_char]
        
        return x, y
    
    def parse_chess_move(self, uci_move):
        """Parse UCI move (e.g., 'e2e4') to extract source and target coordinates"""
        if len(uci_move) != 4:
            raise ValueError(f"Invalid UCI move: {uci_move}")
        
        from_square = uci_move[0:2]  # e.g., 'e2'
        to_square = uci_move[2:4]    # e.g., 'e4'
        
        from_x, from_y = self.chess_to_robot_coords(from_square)
        to_x, to_y = self.chess_to_robot_coords(to_square)
        
        return {
            'from': {'x': from_x, 'y': from_y},
            'to': {'x': to_x, 'y': to_y}
        }
