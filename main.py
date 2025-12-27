#!/usr/bin/env python3
"""
Chess GUI Application
---------------------
Main entry point for the chess application with graphical interface.

This module provides the core game loop and initialization for a chess application
that supports human vs engine gameplay with move visualization. The application
uses pygame for rendering and the python-chess library for chess logic.
"""

import sys
import pygame
import chess

from gui.board_gui import BoardGUI
from gui.input_handler import InputHandler
from utils.config import Config
from gui.colors import Colors
from gui.board_state import BoardState
from gui.game_result_dialog import GameResultDialog
from gui.move_history_panel import MoveHistoryPanel
from gui.game_controls import (
    GameControls,
    SimplePGNDialog,
    save_pgn_to_file,
    load_pgn_from_file,
)

from engine.engine_wrapper import (
    initialize_engine as init_engine_wrapper,
    is_engine_ready,
)
from engine.engine_controller import EngineController


def initialize_pygame():
    """
    Initialize pygame and create the main application window.

    Sets up the pygame environment, creates a display window with configured
    dimensions, and initializes the game clock for frame rate control.

    Returns:
        tuple:
            - screen (pygame.Surface): The main display surface for rendering
            - clock (pygame.time.Clock): Clock object for FPS management

    Note:
        Window dimensions are pulled from Config.WINDOW_WIDTH and Config.WINDOW_HEIGHT.
        The window title is set from Config.WINDOW_TITLE.
    """
    # Initialize all pygame modules (display, font, mixer, etc.)
    pygame.init()

    # Set the window title displayed in the title bar
    pygame.display.set_caption(Config.WINDOW_TITLE)

    # Create the main display window with specified dimensions
    screen = pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))

    # Initialize clock for controlling frame rate
    clock = pygame.time.Clock()

    print(f"[Init] Window created: {Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
    return screen, clock


def initialize_engine(engine_path=None):
    """
    Load and initialize the chess engine model.

    Placeholder for loading a neural network or traditional
    chess engine that will serve as the AI opponent.

    Returns:
        EngineController: Controller managing engine operations and threading
    """
    print("\n[Engine] Initializing inference engine...")

    # Initialize engine wrapper
    success = init_engine_wrapper(engine_path)

    if success:
        print("[Engine] ✅ Engine loaded successfully")
    else:
        print("[Engine] ⚠️ Engine not available - will use random moves as fallback")

    # Create engine controller (handles threading)
    controller = EngineController()

    return controller


def check_game_end_conditions(board_state: BoardState) -> tuple:
    """
    Check for game end conditions and return result.

    Args:
        board_state: BoardState instance

    Returns:
        Tuple of (is_game_over, result_type, winner, reason)
    """
    board = board_state.board

    # Checkmate
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black"
        return (True, "checkmate", winner, "")

    # Stalemate
    if board.is_stalemate():
        return (True, "stalemate", None, "")

    # Insufficient material
    if board.is_insufficient_material():
        return (True, "draw", None, "insufficient material")

    # Fifty-move rule
    if board.can_claim_fifty_moves():
        return (True, "draw", None, "50-move rule")

    # Threefold repetition
    if board.can_claim_threefold_repetition():
        return (True, "draw", None, "threefold repetition")

    # Game continues
    return (False, None, None, None)


def check_engine_turn_and_move(board_state, engine_controller, move_history):
    """
    Check if it's engine's turn and request move if needed.

    Args:
        board_state: BoardState instance
        engine_controller: EngineController instance
        move_history: List of moves in UCI notation

    Returns:
        True if engine is now thinking, False otherwise
    """
    # Determine engine color
    engine_color = chess.BLACK if Config.HUMAN_COLOR == "white" else chess.WHITE

    # Check if it's engine's turn
    if board_state.board.turn == engine_color:
        # Check if engine is already thinking
        if not engine_controller.is_thinking():
            # Check if game is over
            if board_state.is_game_over():
                return False

            print(f"\n[Engine] Engine's turn ({board_state.get_turn_string()})")

            # Request move from engine (non-blocking)
            engine_controller.request_move(
                board=board_state.board,
                move_history=move_history,
                time_limit=Config.ENGINE_TIME_LIMIT,
                search_depth=Config.MCTS_ITERATIONS,
                temperature=Config.TEMPERATURE,
            )
            return True

    return False


def main():
    """
    Main application entry point and game loop.

    Orchestrates the entire chess application lifecycle:
        1. Validates configuration settings
        2. Initializes pygame and the display window
        3. Sets up the chess board logic
        4. Runs the main event/render loop
        5. Handles cleanup on exit

    Returns:
        int: Exit code (0 for successful execution)
    """
    # ==================== Initialization Phase ====================
    print("=" * 50)
    print("Chess GUI")
    print("=" * 50)

    # Validate configuration settings before proceeding
    # This ensures all required config values are present and valid
    Config.validate()
    print("✅ Configuration validated")

    # Initialize pygame subsystems and create the display window
    screen, clock = initialize_pygame()
    print("✅ Pygame initialized")

    # Initialize chess board using BoardState
    # Board starts in standard starting position
    board_state = BoardState()
    print(f"✅ Chess board initialized")
    print(f"    Starting FEN: {board_state.get_fen()}")

    # Display chess board statistics for verification
    print(f"    Legal moves: {board_state.count_legal_moves()} available")
    print(f"    Turn: {board_state.get_turn_string()}")

    # Initialize board GUI renderer
    board_gui = BoardGUI(screen)
    print("✅ Board GUI renderer initialized")

    # Initialize input handler
    input_handler = InputHandler(board_gui, board_state)
    print("✅ Input handler initialized")

    result_dialog = GameResultDialog(screen)
    move_panel = MoveHistoryPanel(
        screen,
        x=Config.MOVE_HISTORY_X,
        y=Config.MOVE_HISTORY_Y,
        width=Config.MOVE_HISTORY_WIDTH,
        height=Config.MOVE_HISTORY_HEIGHT,
    )
    game_controls = GameControls(
        screen,
        x=Config.GAME_CONTROLS_X,
        y=Config.GAME_CONTROLS_Y,
        width=Config.GAME_CONTROLS_WIDTH,
    )
    pgn_dialog = SimplePGNDialog(screen)
    print("✅ Game state management components initialized")

    # Initialize the chess engine (AI opponent)
    engine_controller = initialize_engine()  # Uses path from engine_wrapper.py
    print("✅ Engine controller initialized")

    # Track move history for engine
    move_history = []

    # Game state flags
    game_ended = False
    last_result = None

    # Determine player color
    print(f"\n[Info] You are playing as: {Config.HUMAN_COLOR.upper()}")
    print(f"[Info] Engine is playing as: {Config.ENGINE_COLOR.upper()}")

    # Check if engine should move first
    engine_thinking = check_engine_turn_and_move(
        board_state, engine_controller, move_history
    )

    # Notify user that display test is running
    print("\n[Info] Running display test...")
    print("[Info] Close window or press ESC to exit\n")
    print("\n[Controls]")
    print("  R - Reset board")
    print("  U - Undo last move")
    print("  S - Save game (PGN)")
    print("  L - Load game (PGN)")
    print("  Mouse - Select and move pieces")
    print("  Right panel - Move history, game controls")
    print()

    # ==================== Main Game Loop ====================
    running = True
    while running:
        # -------------------- Event Handling --------------------
        # Process all events from the event queue
        for event in pygame.event.get():
            # Handle window close button
            if event.type == pygame.QUIT:
                running = False

            # Handle keyboard input
            elif event.type == pygame.KEYDOWN:
                # ESC key exits the application
                if event.key == pygame.K_ESCAPE:
                    running = False
                # R key resets the board to starting position
                elif event.key == pygame.K_r:
                    board_state.reset()
                    input_handler.reset()
                    move_history.clear()
                    engine_controller.cancel_thinking()
                    game_ended = False
                    last_result = None
                    move_panel.scroll_to_top()
                    print("[Action] Board reset")
                    print(f"    Status: {board_state.get_game_status()}")
                    # Check if engine should move first
                    engine_thinking = check_engine_turn_and_move(
                        board_state, engine_controller, move_history
                    )

                # U key undoes last move (or two moves if playing vs engine)
                elif event.key == pygame.K_u:
                    if not engine_controller.is_thinking() and not game_ended:
                        # Undo player's last move (and engine's move if present)
                        moves_to_undo = (
                            2 if len(board_state.board.move_stack) >= 2 else 1
                        )

                        undone_moves = []
                        for _ in range(moves_to_undo):
                            undone = board_state.undo_move()
                            if undone:
                                undone_moves.append(undone.uci())
                                if move_history:
                                    move_history.pop()

                        if undone_moves:
                            print(
                                f"[Action] Undone {len(undone_moves)} move(s): {', '.join(undone_moves)}"
                            )
                            input_handler.reset()
                            game_ended = False
                            last_result = None
                        else:
                            print("[Action] No moves to undo")
                        print(f"    Status: {board_state.get_game_status()}")
                    else:
                        print("[Action] Cannot undo while engine is thinking")

                elif event.key == pygame.K_s:
                    # Save game shortcut
                    if len(board_state.board.move_stack) > 0:
                        filename = pgn_dialog.show_save_dialog()
                        if filename:
                            pgn_string = board_state.to_pgn()
                            if save_pgn_to_file(pgn_string, filename):
                                print(f"[Action] ✅ Game saved to: {filename}")
                            else:
                                print(f"[Action] ❌ Failed to save game")

                elif event.key == pygame.K_l:
                    # Load game shortcut
                    filename = pgn_dialog.show_load_dialog()
                    if filename:
                        pgn_string = load_pgn_from_file(filename)
                        if pgn_string:
                            try:
                                # Cancel any engine thinking
                                engine_controller.cancel_thinking()

                                # Load the game
                                board_state = BoardState.from_pgn(pgn_string)
                                input_handler.board_state = board_state
                                input_handler.reset()
                                move_history = board_state.get_move_history_uci()
                                game_ended = False
                                last_result = None
                                move_panel.scroll_to_bottom()

                                print(f"[Action] ✅ Game loaded from: {filename}")
                                print(f"    Moves: {len(move_history)}")
                                print(f"    Status: {board_state.get_game_status()}")

                                # Check if engine should move
                                engine_thinking = check_engine_turn_and_move(
                                    board_state, engine_controller, move_history
                                )

                            except Exception as e:
                                print(f"[Action] ❌ Failed to load game: {e}")

            # Mouse wheel for move history scrolling
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if move_panel.is_mouse_over(mouse_pos):
                    move_panel.handle_mouse_wheel(event.y)

            # Mouse events - Support BOTH drag-and-drop AND click-to-move
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check for game controls clicks
                    button_id = game_controls.handle_click(event.pos)
                    if button_id:
                        if button_id == "save_pgn":
                            if len(board_state.board.move_stack) > 0:
                                filename = pgn_dialog.show_save_dialog()
                                if filename:
                                    pgn_string = board_state.to_pgn()
                                    if save_pgn_to_file(pgn_string, filename):
                                        print(f"[Action] ✅ Game saved to: {filename}")

                        elif button_id == "load_pgn":
                            filename = pgn_dialog.show_load_dialog()
                            if filename:
                                pgn_string = load_pgn_from_file(filename)
                                if pgn_string:
                                    try:
                                        engine_controller.cancel_thinking()
                                        board_state = BoardState.from_pgn(pgn_string)
                                        input_handler.board_state = board_state
                                        input_handler.reset()
                                        move_history = (
                                            board_state.get_move_history_uci()
                                        )
                                        game_ended = False
                                        last_result = None
                                        move_panel.scroll_to_bottom()
                                        print(f"[Action] ✅ Game loaded: {filename}")
                                        engine_thinking = check_engine_turn_and_move(
                                            board_state, engine_controller, move_history
                                        )
                                    except Exception as e:
                                        print(f"[Action] ❌ Failed to load: {e}")

                        elif button_id == "resign":
                            if not game_ended:
                                # Current player resigns
                                winner = (
                                    "Black"
                                    if board_state.board.turn == chess.WHITE
                                    else "White"
                                )
                                print(
                                    f"[Action] {board_state.get_turn_string()} resigns!"
                                )
                                game_ended = True
                                last_result = ("resignation", winner, "")
                                # Show result dialog
                                choice = result_dialog.show("resignation", winner, "")
                                if choice == "new_game":
                                    board_state.reset()
                                    input_handler.reset()
                                    move_history.clear()
                                    engine_controller.cancel_thinking()
                                    game_ended = False
                                    last_result = None
                                    move_panel.scroll_to_top()
                                    engine_thinking = check_engine_turn_and_move(
                                        board_state, engine_controller, move_history
                                    )

                    # Only handle chess input on human's turn and if game not over
                    if not game_ended:
                        human_color = (
                            chess.WHITE
                            if Config.HUMAN_COLOR == "white"
                            else chess.BLACK
                        )
                        if (
                            board_state.board.turn == human_color
                            and not engine_controller.is_thinking()
                        ):
                            input_handler.handle_mouse_down(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and not game_ended:  # Left click release
                    human_color = (
                        chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
                    )
                    if (
                        board_state.board.turn == human_color
                        and not engine_controller.is_thinking()
                    ):
                        # Try to complete drag move
                        move_made = input_handler.handle_mouse_up(event.pos)

                        # If no drag move was made, handle as click-to-move
                        if not move_made:
                            move_made = input_handler.handle_mouse_click(event.pos)

                        # If player made a move, add to history and check for engine turn
                        if move_made:
                            # Get the last move from board
                            if board_state.board.move_stack:
                                last_move = board_state.board.peek()
                                move_history.append(last_move.uci())

                            # Check for game end
                            is_over, result_type, winner, reason = (
                                check_game_end_conditions(board_state)
                            )
                            if is_over:
                                game_ended = True
                                last_result = (result_type, winner, reason)
                                print(f"[Game] Game over: {result_type}")
                                if winner:
                                    print(f"       Winner: {winner}")
                                if reason:
                                    print(f"       Reason: {reason}")

                                # Show result dialog
                                choice = result_dialog.show(result_type, winner, reason)
                                if choice == "new_game":
                                    board_state.reset()
                                    input_handler.reset()
                                    move_history.clear()
                                    engine_controller.cancel_thinking()
                                    game_ended = False
                                    last_result = None
                                    move_panel.scroll_to_top()
                                    engine_thinking = check_engine_turn_and_move(
                                        board_state, engine_controller, move_history
                                    )
                            else:
                                # Check if engine should move now
                                engine_thinking = check_engine_turn_and_move(
                                    board_state, engine_controller, move_history
                                )

            elif event.type == pygame.MOUSEMOTION and not game_ended:
                # Track mouse position during drag, but only on human's turn
                human_color = (
                    chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
                )
                if (
                    board_state.board.turn == human_color
                    and not engine_controller.is_thinking()
                ):
                    input_handler.handle_mouse_motion(event.pos)

        # -------------------- Engine Move Processing --------------------

        if not game_ended:
            # Check if engine has a move ready
            move_uci = engine_controller.get_move_if_ready()

            if move_uci is not None:  # Engine has returned a move
                try:
                    # Parse, validate, and apply the move
                    move = chess.Move.from_uci(move_uci)

                    # Check if move is legal
                    if move in board_state.board.legal_moves:
                        move_san = board_state.board.san(move)
                        success = board_state.make_move(move)

                        # If move applied successfully, update history and reset input
                        if success:
                            move_history.append(move_uci)
                            move_panel.scroll_to_bottom()
                            print(f"[Engine] Move made: {move_san} ({move_uci})")
                            print(f"         Status: {board_state.get_game_status()}")
                            input_handler.reset()

                            # Check for game end
                            is_over, result_type, winner, reason = (
                                check_game_end_conditions(board_state)
                            )
                            if is_over:
                                game_ended = True
                                last_result = (result_type, winner, reason)
                                print(f"[Game] Game over: {result_type}")
                                if winner:
                                    print(f"       Winner: {winner}")
                                if reason:
                                    print(f"       Reason: {reason}")

                                # Show result dialog
                                choice = result_dialog.show(result_type, winner, reason)
                                if choice == "new_game":
                                    board_state.reset()
                                    input_handler.reset()
                                    move_history.clear()
                                    engine_controller.cancel_thinking()
                                    game_ended = False
                                    last_result = None
                                    move_panel.scroll_to_top()
                                    engine_thinking = check_engine_turn_and_move(
                                        board_state, engine_controller, move_history
                                    )
                        else:
                            print(f"[Engine] ❌ Failed to apply move: {move_uci}")
                    else:
                        print(f"[Engine] ❌ Illegal move returned: {move_uci}")

                except Exception as e:
                    print(f"[Engine] ❌ Error applying move: {e}")

        # -------------------- Rendering Phase --------------------

        # Clear screen
        screen.fill(Colors.BACKGROUND)

        # Draw board with squares and coordinates
        board_gui.draw_board()

        # Draw check indicator first (behind pieces)
        board_gui.draw_check_indicator(board_state.board)

        # Draw selection highlights and legal move indicators (only on human's turn)
        if not game_ended:
            human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
            if (
                board_state.board.turn == human_color
                and not engine_controller.is_thinking()
            ):
                input_handler.render_selection_highlights()

        # Draw game info (turn indicator)
        board_gui.draw_game_info(board_state.board)

        # Draw "thinking" indicator if engine is calculating
        if engine_controller.is_thinking():
            font = pygame.font.SysFont("Arial", 24, bold=True)
            thinking_text = font.render("Engine thinking...", True, (255, 215, 0))
            text_rect = thinking_text.get_rect(centerx=screen.get_width() // 2, y=20)
            # Draw background
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (50, 50, 50), bg_rect)
            pygame.draw.rect(screen, (255, 215, 0), bg_rect, 2)
            screen.blit(thinking_text, text_rect)

        # Draw all pieces (hide the one being dragged)
        if input_handler.dragging and input_handler.drag_start_square is not None:
            # Temporarily remove dragged piece from board for rendering
            dragged_piece = board_state.board.piece_at(input_handler.drag_start_square)
            board_state.board.remove_piece_at(input_handler.drag_start_square)
            board_gui.draw_pieces(board_state.board)
            board_state.board.set_piece_at(
                input_handler.drag_start_square, dragged_piece
            )
        else:
            board_gui.draw_pieces(board_state.board)

        # Draw dragged piece on top (follows cursor) - only on human's turn
        if not game_ended:
            human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
            if (
                board_state.board.turn == human_color
                and not engine_controller.is_thinking()
            ):
                input_handler.render_dragged_piece()

        # Draw move history panel
        move_panel.draw(board_state.get_move_history_san())

        # Draw game controls
        game_controls.draw()

        # Show FPS if enabled
        if Config.SHOW_FPS:
            fps = clock.get_fps()
            font = pygame.font.SysFont("Arial", 18)
            fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
            screen.blit(fps_text, (10, 10))

        # Update the display with all rendered graphics
        # flip() updates the entire display surface
        pygame.display.flip()

        # -------------------- Frame Rate Control --------------------
        # Limit the loop to run at the configured FPS
        # This prevents excessive CPU usage and ensures smooth animation
        clock.tick(Config.FPS)

    # ==================== Cleanup Phase ====================
    # Cleanup
    print("\n" + "=" * 50)
    print("Shutting down...")

    # Cancel any ongoing engine thinking
    if engine_controller.is_thinking():
        print("[Cleanup] Cancelling engine thinking...")
        engine_controller.cancel_thinking()

    # Properly shut down pygame and release resources
    # Display final game state summary
    print("Final Game State:")
    print(f"    Moves played: {len(board_state.get_move_history_uci())}")
    print(f"    Status: {board_state.get_game_status()}")
    if board_state.get_move_history_san():
        print(f"    Move history: {' '.join(board_state.get_move_history_san())}")
    print("✅ Application closed cleanly")
    print("=" * 50)

    pygame.quit()
    return 0


if __name__ == "__main__":
    # Entry point guard - ensures main() only runs when script is executed directly
    # (not when imported as a module)
    sys.exit(main())
