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


def apply_engine_move(board_state, engine_controller, move_history, input_handler):
    """
    Check if engine has finished thinking and apply move if ready.

    Args:
        board_state: BoardState instance
        engine_controller: EngineController instance
        move_history: List of moves in UCI notation
        input_handler: InputHandler instance

    Returns:
        True if move was applied, False if still thinking or error
    """
    # Check if engine has a move ready
    move_uci = engine_controller.get_move_if_ready()

    if move_uci is None:
        return False  # Still thinking

    if move_uci == "":
        print("[Engine] ❌ Engine returned empty move")
        return True  # Error, but stop thinking

    try:
        # Parse and validate move
        move = chess.Move.from_uci(move_uci)

        if move not in board_state.board.legal_moves:
            print(f"[Engine] ❌ Illegal move returned: {move_uci}")
            return True  # Error, but stop thinking

        # Apply move
        move_san = board_state.board.san(move)
        success = board_state.make_move(move)

        if success:
            move_history.append(move_uci)
            print(f"[Engine] Move made: {move_san} ({move_uci})")
            print(f"         Status: {board_state.get_game_status()}")

            # Clear any selection after engine move
            input_handler.reset()

            return True
        else:
            print(f"[Engine] ❌ Failed to apply move: {move_uci}")
            return True  # Error, but stop thinking

    except Exception as e:
        print(f"[Engine] ❌ Error applying move: {e}")
        return True  # Error, but stop thinking


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

    # Initialize the chess engine (AI opponent)
    engine_controller = initialize_engine()  # Uses path from engine_wrapper.py
    print("✅ Engine controller initialized")

    # Track move history for engine
    move_history = []

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
    print("[Info] Press 'R' to reset board, 'U' to undo move\n")
    if Config.SHOW_FPS:
        print("[Info] FPS counter enabled\n")
    else:
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
                    print("[Action] Board reset")
                    print(f"    Status: {board_state.get_game_status()}")
                    # Check if engine should move first
                    engine_thinking = check_engine_turn_and_move(
                        board_state, engine_controller, move_history
                    )

                # U key undoes last move (or two moves if playing vs engine)
                elif event.key == pygame.K_u:
                    if not engine_controller.is_thinking():
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
                        else:
                            print("[Action] No moves to undo")
                        print(f"    Status: {board_state.get_game_status()}")
                    else:
                        print("[Action] Cannot undo while engine is thinking")

            # Mouse events - Support BOTH drag-and-drop AND click-to-move
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Only handle input on human's turn
                    # Start potential drag (also selects piece)
                    human_color = (
                        chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
                    )
                    if (
                        board_state.board.turn == human_color
                        and not engine_controller.is_thinking()
                    ):
                        input_handler.handle_mouse_down(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
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

                            # Check if engine should move now
                            engine_thinking = check_engine_turn_and_move(
                                board_state, engine_controller, move_history
                            )

            elif event.type == pygame.MOUSEMOTION:
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
                        print(f"[Engine] Move made: {move_san} ({move_uci})")
                        print(f"         Status: {board_state.get_game_status()}")
                        input_handler.reset()
                    else:
                        print(f"[Engine] ❌ Failed to apply move: {move_uci}")
                else:
                    print(f"[Engine] ❌ Illegal move returned: {move_uci}")

            except Exception as e:
                print(f"[Engine] ❌ Error applying move: {e}")

        # -------------------- Rendering Phase --------------------
        # Draw board with squares and coordinates
        board_gui.draw_board()

        # Draw check indicator first (behind pieces)
        board_gui.draw_check_indicator(board_state.board)

        # Draw selection highlights and legal move indicators (only on human's turn)
        human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
        if (
            board_state.board.turn == human_color
            and not engine_controller.is_thinking()
        ):
            input_handler.render_selection_highlights()

        # Draw game info (turn indicator)
        board_gui.draw_game_info(board_state.board)

        # Draw all pieces
        board_gui.draw_pieces(board_state.board)

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
        if (
            board_state.board.turn == human_color
            and not engine_controller.is_thinking()
        ):
            input_handler.render_dragged_piece()

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
    print("[✅] Application closed cleanly")
    print("=" * 50)

    pygame.quit()
    return 0


if __name__ == "__main__":
    # Entry point guard - ensures main() only runs when script is executed directly
    # (not when imported as a module)
    sys.exit(main())
