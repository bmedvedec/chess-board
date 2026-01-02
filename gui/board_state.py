"""
Board State Management
----------------------------------
Comprehensive chess board state management module.

This module provides a high-level wrapper around the python-chess library,
offering a clean, intuitive interface for managing chess game state.
It handles move validation, game state detection, position tracking,
and provides utilities for both GUI rendering and chess engine integration.
"""

import chess
import chess.pgn
from typing import Optional, List, Tuple
from io import StringIO


class BoardState:
    """
    High-level chess board state manager with comprehensive game logic.

    This class wraps the python-chess Board class and provides an intuitive
    interface for chess game management. It maintains move history, validates
    moves, detects game-ending conditions, and provides utilities for both
    human players and chess engines.
    """

    def __init__(self, fen: Optional[str] = None):
        """
        Initialize a new chess board state.

        Creates a new board either from the standard starting position or from a specified FEN string.
        Initializes empty move history lists for tracking game progress.

        Args:
            fen (Optional[str]): FEN string representing a specific board position.
                If None, initializes to standard chess starting position.
        """
        # Initialize python-chess Board from FEN or standard starting position
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()

        # Move history in UCI notation (Universal Chess Interface)
        # Format: e2e4, e7e8q (includes promotion piece)
        # Used for engine communication and game replay
        self.move_history_uci: List[str] = []

        # Move history in SAN notation (Standard Algebraic Notation)
        # Format: e4, Nf3, O-O, exd5
        # Used for display to human players and PGN export
        self.move_history_san: List[str] = []

    # =========================================
    # Position Information
    # =========================================
    # Methods for querying the current board position and piece placement

    def get_fen(self) -> str:
        """
        Get current position as complete FEN string.

        Returns:
            str: Complete FEN string of current position
        """
        return self.board.fen()

    def get_board_fen(self) -> str:
        """
        Get only the piece placement portion of FEN.

        Returns just the board layout without turn, castling rights, etc.
        Useful for position comparison regardless of game state.

        Returns:
            str: Board FEN (piece placement only)
        """
        return self.board.board_fen()

    def get_piece_at(self, square: int) -> Optional[chess.Piece]:
        """
        Get the chess piece at a given square.

        Args:
            square (int): Square index from 0-63:
                Can also use chess module constants: chess.E4, chess.A1, etc.

        Returns:
            Optional[chess.Piece]: Piece object with .piece_type and .color attributes,
                or None if square is empty
        """
        return self.board.piece_at(square)

    def get_piece_at_coords(self, file: int, rank: int) -> Optional[chess.Piece]:
        """
        Get piece at file/rank coordinates (alternative to square index).

        Convenient method for accessing pieces using file/rank notation
        instead of square indices.

        Args:
            file (int): File coordinate 0-7 where a=0, b=1, ..., h=7
            rank (int): Rank coordinate 0-7 where 1=0, 2=1, ..., 8=7

        Returns:
            Optional[chess.Piece]: Piece object or None if square is empty
        """
        square = chess.square(file, rank)
        return self.board.piece_at(square)

    def get_piece_symbol_at(self, square: int) -> Optional[str]:
        """
        Get single-character piece symbol at a square.

        Returns the standard FEN notation symbol for the piece.

        Args:
            square (int): Square index (0-63)

        Returns:
            Optional[str]: Piece symbol:
                - White pieces: 'P', 'N', 'B', 'R', 'Q', 'K' (uppercase)
                - Black pieces: 'p', 'n', 'b', 'r', 'q', 'k' (lowercase)
                - Empty square: None
        """
        piece = self.board.piece_at(square)
        return piece.symbol() if piece else None

    # =========================================
    # Turn Management
    # =========================================
    # Methods for determining whose turn it is to move

    @property
    def turn(self) -> bool:
        """Current turn: chess.WHITE (True) or chess.BLACK (False)."""
        return self.board.turn

    @property
    def is_white_turn(self) -> bool:
        """True if it's white's turn."""
        return self.board.turn == chess.WHITE

    @property
    def is_black_turn(self) -> bool:
        """True if it's black's turn."""
        return self.board.turn == chess.BLACK

    def get_turn_string(self) -> str:
        """Get current turn as string."""
        return "White" if self.is_white_turn else "Black"

    # =========================================
    # Move Generation & Validation
    # =========================================
    # Methods for generating legal moves and validating move legality

    def get_legal_moves(self) -> List[chess.Move]:
        """
        Get list of all legal moves in the current position.

        Returns:
            List[chess.Move]: List of chess.Move objects representing all legal moves
        """
        return list(self.board.legal_moves)

    def get_legal_moves_uci(self) -> List[str]:
        """
        Get legal moves as UCI (Universal Chess Interface) strings.

        Returns:
            List[str]: List of moves in UCI notation
        """
        return [move.uci() for move in self.board.legal_moves]

    def get_legal_moves_from_square(self, square: int) -> List[chess.Move]:
        """
        Get all legal moves originating from a specific square.

        Useful for highlighting valid destinations when a piece is selected.

        Args:
            square (int): Source square index (0-63)

        Returns:
            List[chess.Move]: Legal moves starting from the given square
        """
        return [m for m in self.board.legal_moves if m.from_square == square]

    def get_legal_destinations_from_square(self, square: int) -> List[int]:
        """
        Get list of destination squares for legal moves from a given square.

        Returns just the destination square indices, useful for drawing
        legal move indicators on the GUI.

        Args:
            square (int): Source square index (0-63)

        Returns:
            List[int]: List of destination square indices
        """
        moves = self.get_legal_moves_from_square(square)
        return [m.to_square for m in moves]

    def is_legal_move(self, move: chess.Move) -> bool:
        """
        Check if a specific move is legal in the current position.

        Args:
            move (chess.Move): Move object to validate

        Returns:
            bool: True if move is legal, False otherwise
        """
        return move in self.board.legal_moves

    def is_legal_uci(self, uci: str) -> bool:
        """
        Check if a UCI move string is legal in the current position.

        Args:
            uci (str): Move in UCI notation (e.g., "e2e4")

        Returns:
            bool: True if move is legal, False if illegal or invalid format
        """
        try:
            move = chess.Move.from_uci(uci)
            return move in self.board.legal_moves
        except ValueError:
            return False

    def count_legal_moves(self) -> int:
        """
        Count the number of legal moves available.

        Used for detecting stalemate (0 legal moves, not in check)

        Returns:
            int: Number of legal moves in current position
        """
        return self.board.legal_moves.count()

    # =========================================
    # Move Execution
    # =========================================
    # Methods for making moves and managing move history

    def make_move(self, move: chess.Move) -> bool:
        """
        Execute a move on the board and update move history.

        Args:
            move (chess.Move): chess.Move object to execute

        Returns:
            bool: True if move was successfully made, False if move is illegal
        """
        # Validate move legality before execution
        if move not in self.board.legal_moves:
            return False

        # Generate SAN notation before making the move
        # SAN depends on current position (e.g., which pieces can reach a square)
        san = self.board.san(move)

        # Execute the move on the internal board
        # This updates piece positions, turn, castling rights, etc.
        self.board.push(move)

        # Record move in both notations for different use cases
        self.move_history_uci.append(move.uci())  # For engine communication
        self.move_history_san.append(san)  # For human-readable display

        return True

    def make_move_uci(self, uci: str) -> bool:
        """
        Execute a move from UCI string.

        Args:
            uci: Move in UCI notation (e.g., "e2e4", "e7e8q")

        Returns:
            True if move was made, False if illegal
        """
        try:
            move = chess.Move.from_uci(uci)
            return self.make_move(move)
        except ValueError:
            return False

    def make_move_from_squares(
        self, from_sq: int, to_sq: int, promotion: Optional[int] = None
    ) -> bool:
        """
        Execute a move from source to destination squares.

        Args:
            from_sq: Source square (0-63)
            to_sq: Destination square (0-63)
            promotion: Piece type for pawn promotion
                      (chess.QUEEN, chess.ROOK, etc.)

        Returns:
            True if move was made, False if illegal
        """
        move = chess.Move(from_sq, to_sq, promotion=promotion)
        return self.make_move(move)

    def undo_move(self) -> Optional[chess.Move]:
        """
        Undo the last move.

        Returns:
            The move that was undone, or None if no moves to undo
        """
        if not self.board.move_stack:
            return None

        move = self.board.pop()

        # Remove from history
        if self.move_history_uci:
            self.move_history_uci.pop()
        if self.move_history_san:
            self.move_history_san.pop()

        return move

    def undo_two_moves(self) -> Tuple[Optional[chess.Move], Optional[chess.Move]]:
        """
        Undo last two moves (player + engine).

        Returns:
            Tuple of (last_move, second_last_move) that were undone
        """
        move1 = self.undo_move()
        move2 = self.undo_move()
        return (move1, move2)

    # =========================================
    # Game State Detection
    # =========================================
    # Methods for detecting check, checkmate, stalemate, and draw conditions
    # Critical for determining game outcome and providing UI feedback

    def is_check(self) -> bool:
        """
        Check if the current player's king is in check.

        Returns:
            bool: True if current player is in check, False otherwise
        """
        return self.board.is_check()

    def is_checkmate(self) -> bool:
        """
        Check if the current player is checkmated (game over).

        Returns:
            bool: True if current player is checkmated, False otherwise
        """
        return self.board.is_checkmate()

    def is_stalemate(self) -> bool:
        """
        Check if the position is a stalemate draw.

        Returns:
            bool: True if position is stalemate, False otherwise
        """
        return self.board.is_stalemate()

    def is_insufficient_material(self) -> bool:
        """
        Check if neither side has sufficient material to checkmate.

        Returns:
            bool: True if draw due to insufficient material, False otherwise
        """
        return self.board.is_insufficient_material()

    def can_claim_fifty_moves(self) -> bool:
        """
        Check if the 50-move rule draw can be claimed.

        Returns:
            bool: True if 50-move draw can be claimed, False otherwise
        """
        return self.board.can_claim_fifty_moves()

    def can_claim_threefold_repetition(self) -> bool:
        """
        Check if threefold repetition draw can be claimed.

        Returns:
            bool: True if threefold repetition draw can be claimed, False otherwise
        """
        return self.board.can_claim_threefold_repetition()

    def is_game_over(self) -> bool:
        """
        Check if the game has ended by any means.

        Returns:
            bool: True if game is over, False if game is ongoing
        """
        return self.board.is_game_over()

    def get_game_result(self) -> Optional[str]:
        """
        Get the game result in PGN notation.

        Returns:
            Optional[str]: Game result:
                - "1-0" if white wins (black is checkmated)
                - "0-1" if black wins (white is checkmated)
                - "1/2-1/2" if draw (any draw condition)
                - None if game is still ongoing
        """
        if not self.is_game_over():
            return None

        if self.is_checkmate():
            # The side to move is checkmated, so the other side wins
            return "0-1" if self.is_white_turn else "1-0"
        else:
            # All other game-ending conditions are draws
            return "1/2-1/2"

    def get_game_status(self) -> str:
        """
        Get a human-readable game status message.

        Provides descriptive status for display in the GUI, including
        who is to move, check status, and game-ending conditions.

        Returns:
            str: Human-readable status message
        """
        if self.is_checkmate():
            winner = "Black" if self.is_white_turn else "White"
            return f"Checkmate! {winner} wins"
        elif self.is_stalemate():
            return "Stalemate - Draw"
        elif self.is_insufficient_material():
            return "Draw - Insufficient material"
        elif self.can_claim_fifty_moves():
            return "Draw claimable - 50 move rule"
        elif self.can_claim_threefold_repetition():
            return "Draw claimable - Threefold repetition"
        elif self.is_check():
            return f"{self.get_turn_string()} is in check"
        else:
            return f"{self.get_turn_string()} to move"

    # =========================================
    # Special Move Detection
    # =========================================

    def is_promotion_move(self, from_sq: int, to_sq: int) -> bool:
        """Check if move would be a pawn promotion."""
        piece = self.board.piece_at(from_sq)
        if piece is None or piece.piece_type != chess.PAWN:
            return False

        to_rank = chess.square_rank(to_sq)
        return (piece.color == chess.WHITE and to_rank == 7) or (
            piece.color == chess.BLACK and to_rank == 0
        )

    def is_castling_move(self, move: chess.Move) -> bool:
        """Check if move is castling."""
        return self.board.is_castling(move)

    def is_en_passant_move(self, move: chess.Move) -> bool:
        """Check if move is en passant capture."""
        return self.board.is_en_passant(move)

    def get_castling_rights(self) -> dict:
        """Get current castling rights."""
        return {
            "white_kingside": self.board.has_kingside_castling_rights(chess.WHITE),
            "white_queenside": self.board.has_queenside_castling_rights(chess.WHITE),
            "black_kingside": self.board.has_kingside_castling_rights(chess.BLACK),
            "black_queenside": self.board.has_queenside_castling_rights(chess.BLACK),
        }

    # =========================================
    # Move History & PGN
    # =========================================

    def get_move_history_uci(self) -> List[str]:
        """Get move history as UCI strings (for engine)."""
        return self.move_history_uci.copy()

    def get_move_history_san(self) -> List[str]:
        """Get move history in SAN notation (for display)."""
        return self.move_history_san.copy()

    def get_last_move(self) -> Optional[chess.Move]:
        """Get the last move made."""
        if self.board.move_stack:
            return self.board.peek()
        return None

    def get_fullmove_number(self) -> int:
        """Get current full move number."""
        return self.board.fullmove_number

    def get_halfmove_clock(self) -> int:
        """Get halfmove clock (for 50-move rule)."""
        return self.board.halfmove_clock

    def to_pgn(
        self,
        white_name: str = "Human",
        black_name: str = "Engine",
        event: str = "Casual Game",
    ) -> str:
        """
        Export game as PGN string.

        Args:
            white_name: White player name
            black_name: Black player name
            event: Event name

        Returns:
            PGN formatted string
        """
        game = chess.pgn.Game()
        game.headers["Event"] = event
        game.headers["White"] = white_name
        game.headers["Black"] = black_name
        game.headers["Result"] = self.get_game_result() or "*"

        node = game
        for move in self.board.move_stack:
            node = node.add_variation(move)

        return str(game)

    @classmethod
    def from_pgn(cls, pgn_string: str) -> "BoardState":
        """
        Create BoardState from PGN string.

        Args:
            pgn_string: PGN formatted game

        Returns:
            New BoardState with game loaded
        """
        pgn = StringIO(pgn_string)
        game = chess.pgn.read_game(pgn)

        if game is None:
            raise ValueError("Invalid PGN string provided.")

        state = cls()
        for move in game.mainline_moves():
            state.make_move(move)

        return state

    # =========================================
    # Board Reset & Setup
    # =========================================

    def reset(self):
        """Reset to starting position."""
        self.board.reset()
        self.move_history_uci.clear()
        self.move_history_san.clear()

    def set_fen(self, fen: str):
        """
        Set position from FEN string.
        Clears move history.
        """
        self.board.set_fen(fen)
        self.move_history_uci.clear()
        self.move_history_san.clear()

    def copy(self) -> "BoardState":
        """Create a deep copy of current state."""
        new_state = BoardState(self.get_fen())
        new_state.move_history_uci = self.move_history_uci.copy()
        new_state.move_history_san = self.move_history_san.copy()
        return new_state

    # =========================================
    # Coordinate Conversion Utilities
    # =========================================

    @staticmethod
    def square_to_coords(square: int) -> Tuple[int, int]:
        """
        Convert square index to (file, rank) coordinates.

        Args:
            square: 0-63 (a1=0, h8=63)

        Returns:
            (file, rank) where file=0-7, rank=0-7
        """
        return (chess.square_file(square), chess.square_rank(square))

    @staticmethod
    def coords_to_square(file: int, rank: int) -> int:
        """
        Convert (file, rank) to square index.

        Args:
            file: 0-7 (a=0, h=7)
            rank: 0-7 (1=0, 8=7)

        Returns:
            Square index 0-63
        """
        return chess.square(file, rank)

    @staticmethod
    def square_name(square: int) -> str:
        """Get algebraic name of square (e.g., 'e4')."""
        return chess.square_name(square)

    @staticmethod
    def parse_square(name: str) -> int:
        """Parse square name to index (e.g., 'e4' -> 28)."""
        return chess.parse_square(name)

    # =========================================
    # Engine Interface
    # =========================================

    def get_engine_input(self) -> dict:
        """
        Get all information engine might need.

        Returns:
            Dictionary with board state for engine
        """
        return {
            "board": self.board.copy(),  # Copy of chess.Board
            "fen": self.get_fen(),
            "move_history": self.get_move_history_uci(),
            "turn": self.turn,
            "is_check": self.is_check(),
            "legal_moves": self.get_legal_moves_uci(),
        }

    # =========================================
    # Display / Debug
    # =========================================

    def __str__(self) -> str:
        """String representation (ASCII board)."""
        return str(self.board)

    def print_board(self):
        """Print ASCII representation of board."""
        print(self.board)
        print(f"\nFEN: {self.get_fen()}")
        print(f"Turn: {self.get_turn_string()}")
        print(f"Status: {self.get_game_status()}")


# =========================================
# Convenience Functions
# =========================================
# Module-level utility functions for creating board states


def create_board(fen: Optional[str] = None) -> BoardState:
    """
    Factory function to create a new BoardState instance.

    Convenience wrapper around BoardState constructor for cleaner imports.

    Args:
        fen (Optional[str]): FEN string for custom position, or None for starting position

    Returns:
        BoardState: New board state instance
    """
    return BoardState(fen)


def test_position(name: str) -> BoardState:
    """
    Create a board with a predefined test position.

    Provides quick access to common chess positions useful for testing
    specific game mechanics and edge cases.

    Args:
        name (str): Name of the test position to load

    Available Positions:
        - "start": Standard starting position (same as default)
        - "castling": Position with castling rights for both sides
        - "en_passant": Position where en passant capture is available
        - "promotion": Position ready for pawn promotion
        - "checkmate": Fool's mate checkmate position
        - "stalemate": Classic king vs king stalemate

    Returns:
        BoardState: Board initialized to the requested test position

    Raises:
        ValueError: If position name is not recognized
    """
    # Dictionary of predefined test positions in FEN notation
    positions = {
        "start": None,  # Default starting position
        "castling": "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
        "en_passant": "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
        "promotion": "8/P7/8/8/8/8/8/4K2k w - - 0 1",
        "checkmate": "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
        "stalemate": "k7/8/1K6/8/8/8/8/8 b - - 0 1",
    }

    if name not in positions:
        raise ValueError(
            f"Unknown position: {name}. Available: {list(positions.keys())}"
        )

    return BoardState(positions[name])
