import chess
from gui.board_state import BoardState, test_position


def main():
    print("=" * 50)
    print("Board State Testing")
    print("=" * 50)

    # Create board
    board = BoardState()
    print("\n[1] Starting Position:")
    board.print_board()

    # Make some moves
    print("\n[2] Making moves: e2e4, e7e5, Nf3, Nc6")
    board.make_move_uci("e2e4")
    board.make_move_uci("e7e5")
    board.make_move_uci("g1f3")
    board.make_move_uci("b8c6")  # Black moves, now it's White's turn again
    board.print_board()

    # Show legal moves from a square (now it's White's turn, so knight on f3 can move)
    print("\n[3] Legal moves for knight on f3:")
    knight_square = chess.F3
    destinations = board.get_legal_destinations_from_square(knight_square)
    dest_names = [board.square_name(sq) for sq in destinations]
    print(f"    Can move to: {dest_names}")

    # Show move history
    print("\n[4] Move History:")
    print(f"    UCI: {board.get_move_history_uci()}")
    print(f"    SAN: {board.get_move_history_san()}")

    # Test undo (undo Nc6 to get back to position after Nf3)
    print("\n[5] Undoing last move (Nc6):")
    undone = board.undo_move()
    print(f"    Undone: {undone.uci() if undone else 'None'}")
    board.print_board()

    # Test checkmate detection
    print("\n[6] Testing Checkmate Detection:")
    checkmate_board = test_position("checkmate")
    checkmate_board.print_board()
    print(f"    Is checkmate: {checkmate_board.is_checkmate()}")

    # Engine interface
    print("\n[7] Engine Interface Data:")
    engine_data = board.get_engine_input()
    print(f"    FEN: {engine_data['fen']}")
    print(f"    Turn: {'White' if engine_data['turn'] else 'Black'}")
    print(f"    Legal moves count: {len(engine_data['legal_moves'])}")

    # PGN export
    print("\n[8] PGN Export:")
    board.make_move_uci("g1f3")  # Re-make the undone move
    print(board.to_pgn())

    print("\n" + "=" * 50)
    print("Board State Tests Completed")
    print("=" * 50)


if __name__ == "__main__":
    main()
