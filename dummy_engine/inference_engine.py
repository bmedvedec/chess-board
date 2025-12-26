"""
Dummy Inference Engine for Testing
-----------------------------------
Lightweight chess engine for testing the chess GUI without ML dependencies.

This module provides a simple, heuristic-based chess engine that requires NO
trained models, neural networks, or machine learning frameworks. It's designed
specifically for testing and development of the chess GUI application.

Strategy Options:
    The engine includes 4 different strategies (switch by commenting/uncommenting):

    1. Pure Random: Uniform random selection of legal moves
       - Simplest possible implementation
       - No chess knowledge required
       - Good baseline for testing

    2. Capture Priority:
       - Prefers capturing moves over non-captures
       - Random selection among captures
       - Simple but slightly better than random

    3. Center Control:
       - Prioritizes moves to center squares (e4, d4, e5, d5)
       - Classic chess opening principle
       - Good for early game

    4. Material Evaluation:
       - Evaluates material balance after each move
       - Uses standard piece values
       - Looks one move ahead
       - Most sophisticated strategy
"""

import chess
import random
from typing import Optional, List


def get_best_move(
    board: chess.Board,
    move_history: Optional[List[str]] = None,
    time_limit: float = 5.0,
    search_depth: Optional[int] = None,
    temperature: float = 1.0,
    model=None,
) -> str:
    """
    Generate move using simple heuristics.

    Args:
        board (chess.Board): Current position to analyze.
            Standard python-chess Board object with game state.

        move_history (Optional[List[str]], optional): Game move history in UCI.
            Not used by this dummy engine, but accepted for compatibility.
            Defaults to None.

        time_limit (float, optional): Maximum thinking time in seconds.
            Capped at 0.5s for this dummy engine to keep testing fast.
            Defaults to 5.0.

        search_depth (Optional[int], optional): Search depth parameter.
            Not used by this dummy engine (no search tree).
            Accepted for compatibility. Defaults to None.

        temperature (float, optional): Move selection randomness (0.0 to 2.0+).
            Not used by this dummy engine.
            Accepted for compatibility. Defaults to 1.0.

        model (Any, optional): Pre-loaded model object.
            Not used by this dummy engine (no model needed).
            Always None for this implementation. Defaults to None.

    Returns:
        str: UCI format move string (e.g., "e2e4", "e7e5").
            Always returns a valid legal move.

    Raises:
        ValueError: If no legal moves available (game over position).
            Should never happen in practice - engine called when moves exist.
    """
    import time

    # Simulate realistic thinking time
    think_time = min(time_limit, 0.5)  # Cap at 0.5s for testing
    time.sleep(think_time)

    # Get all legal moves in current position
    legal_moves = list(board.legal_moves)

    # Sanity check - should never happen in practice
    # Engine only called when moves exist
    if not legal_moves:
        raise ValueError("No legal moves available!")

    # ========================================================================
    # STRATEGY SELECTION: Uncomment ONE of the following strategies
    # ========================================================================

    # === STRATEGY 1: Pure Random (simplest baseline) ===
    # Uniformly random selection among all legal moves
    # return random.choice(legal_moves).uci()

    # === STRATEGY 2: Capture Priority  ===
    # Prioritizes capturing opponent's pieces
    # If captures available: Random selection among captures
    # If no captures: Random selection among all moves

    # Filter moves that capture opponent pieces
    captures = [move for move in legal_moves if board.is_capture(move)]

    # If any captures available, prefer them
    if captures:
        return random.choice(captures).uci()

    # Otherwise, pick any legal move randomly
    return random.choice(legal_moves).uci()

    # === STRATEGY 3: Center Control ===
    # Prioritizes moves to the four central squares
    # Center squares are e4, d4, e5, d5
    # center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    # center_moves = [move for move in legal_moves if move.to_square in center_squares]
    # if center_moves:
    #     return random.choice(center_moves).uci()
    # return random.choice(legal_moves).uci()

    # === STRATEGY 4: Material Evaluation ===
    # Most sophisticated strategy - looks one move ahead
    # Evaluates resulting material balance after each move
    # Uses standard piece values and capture bonuses
    # best_move = evaluate_material(board, legal_moves)
    # return best_move.uci()


def evaluate_material(board: chess.Board, legal_moves: List[chess.Move]) -> chess.Move:
    """
    Select move based on material balance evaluation (Strategy 4).

    Performs a one-move lookahead, evaluating the material balance that
    results from each possible move, then selects the move with the best outcome.

    Args:
        board (chess.Board): Current position to analyze.
            Not modified - copies are made for evaluation.

        legal_moves (List[chess.Move]): List of all legal moves to evaluate.
            Pre-generated list from board.legal_moves.

    Returns:
        chess.Move: Best move according to material evaluation.
            Returns first move if all moves score equally.
    """
    # Standard chess piece values
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }

    # Initialize best move tracking
    # Start with first move to ensure we always return something
    best_move = legal_moves[0]
    best_score = -999  # Very negative to ensure any real score is better

    # Evaluate each possible move
    for move in legal_moves:
        # Create copy of board to test this move
        # Don't modify original board - just evaluate
        board_copy = board.copy()
        board_copy.push(move)

        # Calculate material balance after this move
        # Positive = good for current player, negative = bad
        score = 0

        # Sum up all pieces on the board
        for square in chess.SQUARES:
            piece = board_copy.piece_at(square)

            if piece:
                # Get value of this piece
                value = piece_values[piece.piece_type]

                # Add value if it's our piece, subtract if opponent's
                if piece.color == board.turn:
                    score += value  # Our piece - positive contribution
                else:
                    score -= value  # Opponent's piece - negative contribution

        # Add bonus for captures to encourage taking material
        if board.is_capture(move):
            # Get the piece that was captured (before move was made)
            captured = board.piece_at(move.to_square)

            if captured:
                # Bonus is 2× the captured piece value
                # This encourages captures even when material balance is neutral
                score += piece_values[captured.piece_type] * 2

        # Update best move if this move scores higher
        if score > best_score:
            best_score = score
            best_move = move

    # Return the move with the highest evaluated score
    return best_move
