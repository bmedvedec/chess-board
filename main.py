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
from gui.move_animator import MoveAnimator
from gui.captured_pieces_display import CapturedPiecesDisplay
from gui.sound_manager import SoundManager
from gui.game_clock import GameClock
from gui.settings_menu import SettingsMenu
from gui.help_screen import HelpScreen
from gui.layout_handler import LayoutHandler

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

    # Create the main display window with specified dimensions and resizable flag
    screen = pygame.display.set_mode(
        (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT),
        pygame.RESIZABLE,
    )

    # Initialize clock for controlling frame rate
    clock = pygame.time.Clock()

    print(f"[Init] Window created: {Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
    print("[Init] Window is resizable (drag edges to resize)")
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

    # Initialize move animator
    move_animator = MoveAnimator(board_gui)
    print("✅ Move animator initialized")

    # Initialize captured pieces display
    captured_display = CapturedPiecesDisplay(
        screen,
        x=Config.MOVE_HISTORY_X,
        y=Config.MOVE_HISTORY_Y + Config.MOVE_HISTORY_HEIGHT + 140,
        width=Config.MOVE_HISTORY_WIDTH,
        piece_images=board_gui.piece_images,
    )
    print("✅ Captured pieces display initialized")

    # Initialize sound manager
    sound_manager = SoundManager()
    print("✅ Sound manager initialized")

    # Initialize game clock
    game_clock = GameClock(
        screen,
        x=Config.BOARD_X,
        y=Config.BOARD_Y + Config.BOARD_SIZE + 20,
        width=200,
        use_chess_clock=False,  # Set to True for chess clocks
        time_control=None,  # Set to seconds (e.g., 300 for 5 min)
    )
    game_clock.start_game()
    print("✅ Game clock initialized")

    # Initialize menu and help screens
    settings_menu = SettingsMenu(screen)
    help_screen = HelpScreen(screen)
    print("✅ Menu system initialized")

    # Initialize layout handler for window resizing
    layout_handler = LayoutHandler()
    print("✅ Layout handler initialized")

    # Initialize the chess engine (AI opponent)
    engine_controller = initialize_engine()  # Uses path from engine_wrapper.py
    print("✅ Engine controller initialized")

    # Track move history for engine
    move_history = []

    # Game state flags
    game_ended = False
    last_result = None

    # Play game start sound
    sound_manager.play_game_start_sound()

    # Check if engine should move first
    engine_thinking = check_engine_turn_and_move(
        board_state, engine_controller, move_history
    )

    print(f"\n[Info] You are playing as: {Config.HUMAN_COLOR.upper()}")
    print(f"[Info] Engine is playing as: {Config.ENGINE_COLOR.upper()}")
    print("\n[Keyboard Shortcuts]")
    print("  R = New game/Reset")
    print("  U = Undo move")
    print("  S = Settings menu")
    print("  H = Help screen")
    print("  ESC = Exit game")

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

                # S key opens settings menu
                elif event.key == pygame.K_s:
                    print("[Menu] Opening settings...")
                    settings_changed = settings_menu.show()
                    if settings_changed:
                        # Apply sound settings to sound manager
                        sound_manager.set_enabled(Config.ENABLE_SOUNDS)
                        sound_manager.set_volume(Config.SOUND_VOLUME)

                        # Apply animation settings to move animator
                        move_animator.animation_enabled = Config.ANIMATE_MOVES
                        move_animator.animation_speed = Config.ANIMATION_SPEED

                        print("[Menu] Settings updated")
                        print(f"  Animations: {Config.ANIMATE_MOVES}")
                        print(f"  Sounds: {Config.ENABLE_SOUNDS}")
                        print(f"  Last move highlight: {Config.SHOW_LAST_MOVE}")
                        print(f"  Captured pieces: {Config.SHOW_CAPTURED_PIECES}")

                # H key opens help screen
                elif event.key == pygame.K_h:
                    print("[Menu] Opening help...")
                    help_screen.show()

                # R key resets the board to starting position
                elif event.key == pygame.K_r and not game_ended:
                    board_state.reset()
                    input_handler.reset()
                    move_history.clear()
                    engine_controller.cancel_thinking()
                    game_ended = False
                    last_result = None
                    move_panel.scroll_to_top()
                    game_clock.reset()
                    game_clock.start_game()
                    move_animator.cancel()
                    sound_manager.play_game_start_sound()
                    print("[Action] Board reset")
                    print(f"    Status: {board_state.get_game_status()}")
                    print("\n[Game] New game started")
                    # Check if engine should move first
                    engine_thinking = check_engine_turn_and_move(
                        board_state, engine_controller, move_history
                    )

                # U key undoes last move (or two moves if playing vs engine)
                elif event.key == pygame.K_u and not game_ended:
                    if not engine_controller.is_thinking():
                        # Undo two moves (player + engine)
                        move1 = board_state.undo_move()
                        move2 = board_state.undo_move()

                        if move1:
                            if move_history:
                                move_history.pop()
                            print(f"[Game] Undid move: {move1.uci()}")
                        if move2:
                            if move_history:
                                move_history.pop()
                            print(f"[Game] Undid move: {move2.uci()}")

                        input_handler.reset()

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

            # Window resize handler
            elif event.type == pygame.VIDEORESIZE:
                # Update layout
                layout_handler.handle_resize(event.w, event.h)

                # Recreate screen with new size
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

                # Reinitialize components with new Config values
                board_gui = BoardGUI(screen)
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
                captured_display = CapturedPiecesDisplay(
                    screen,
                    x=Config.CAPTURED_PIECES_X,
                    y=Config.CAPTURED_PIECES_Y,
                    width=Config.CAPTURED_PIECES_WIDTH,
                    piece_images=board_gui.piece_images,
                )
                game_clock = GameClock(
                    screen,
                    x=Config.GAME_CLOCK_X,
                    y=Config.GAME_CLOCK_Y,
                    width=Config.GAME_CLOCK_WIDTH,
                    use_chess_clock=False,
                    time_control=None,
                )
                settings_menu = SettingsMenu(screen)
                help_screen = HelpScreen(screen)
                result_dialog = GameResultDialog(screen)

                # Update references in other components
                input_handler.board_gui = board_gui
                move_animator.board_gui = board_gui

                print(
                    f"[Resize] Window: {event.w}x{event.h}, Board: {Config.BOARD_SIZE}x{Config.BOARD_SIZE}"
                )

            # Mouse wheel for move history scrolling
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if move_panel.is_mouse_over(mouse_pos):
                    move_panel.handle_mouse_wheel(event.y)

            # Mouse events - Support BOTH drag-and-drop AND click-to-move
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_ended:
                if event.button == 1:  # Left click
                    # Check for game controls clicks
                    button_id = game_controls.handle_click(event.pos)

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
                                    new_state = BoardState.from_pgn(pgn_string)
                                    board_state = new_state
                                    move_history = board_state.get_move_history_uci()
                                    input_handler.board_state = board_state
                                    move_panel.scroll_to_bottom()
                                    game_ended = False
                                    last_result = None
                                    print(f"[Action] ✅ Game loaded: {filename}")
                                except Exception as e:
                                    print(f"[Action] ❌ Failed to load: {e}")

                    elif button_id == "resign":
                        # Current player resigns
                        winner = (
                            "Black"
                            if board_state.board.turn == chess.WHITE
                            else "White"
                        )
                        print(f"[Action] {board_state.get_turn_string()} resigns!")
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
                            game_clock.reset()
                            game_clock.start_game()
                            move_animator.cancel()
                            sound_manager.play_game_start_sound()
                            engine_thinking = check_engine_turn_and_move(
                                board_state, engine_controller, move_history
                            )

                    else:
                        # Handle piece selection for drag
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

            # Mouse button up - handle move completion
            elif event.type == pygame.MOUSEBUTTONUP and not game_ended:
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
                                move_panel.scroll_to_bottom()

                                # Start move animation
                                piece_at_dest = board_state.board.piece_at(
                                    last_move.to_square
                                )
                                if piece_at_dest:
                                    move_animator.start_animation(
                                        piece_at_dest,
                                        last_move.from_square,
                                        last_move.to_square,
                                    )

                                # Play move sound
                                is_capture = board_state.board.is_capture(last_move)
                                is_check = board_state.board.is_check()
                                is_castle = board_state.board.is_castling(last_move)

                                if is_castle:
                                    sound_manager.play_castle_sound()
                                elif last_move.promotion:
                                    sound_manager.play_promotion_sound()
                                else:
                                    sound_manager.play_move_sound(
                                        is_capture=is_capture, is_check=is_check
                                    )

                                # Switch clock turn
                                game_clock.switch_turn(board_state.board.turn)

                            # Check for game end
                            is_over, result_type, winner, reason = (
                                check_game_end_conditions(board_state)
                            )
                            if is_over:
                                game_ended = True
                                last_result = (result_type, winner, reason)
                                sound_manager.play_game_end_sound()
                                game_clock.pause()

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
                                    game_clock.reset()
                                    game_clock.start_game()
                                    move_animator.cancel()
                                    sound_manager.play_game_start_sound()

                                    engine_thinking = check_engine_turn_and_move(
                                        board_state, engine_controller, move_history
                                    )
                            else:
                                # Check if engine should move now
                                engine_thinking = check_engine_turn_and_move(
                                    board_state, engine_controller, move_history
                                )

            # Mouse motion - drag handling
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
                        piece_to_move = board_state.board.piece_at(move.from_square)
                        move_san = board_state.board.san(move)
                        is_capture = board_state.board.is_capture(move)
                        is_castle = board_state.board.is_castling(move)
                        success = board_state.make_move(move)

                        # If move applied successfully, update history and reset input
                        if success:
                            move_history.append(move_uci)
                            move_panel.scroll_to_bottom()

                            # Start animation
                            if piece_to_move:
                                piece_at_dest = board_state.board.piece_at(
                                    move.to_square
                                )
                                if piece_at_dest:
                                    move_animator.start_animation(
                                        piece_at_dest, move.from_square, move.to_square
                                    )

                            # Play sound
                            is_check = board_state.board.is_check()
                            if is_castle:
                                sound_manager.play_castle_sound()
                            elif move.promotion:
                                sound_manager.play_promotion_sound()
                            else:
                                sound_manager.play_move_sound(
                                    is_capture=is_capture, is_check=is_check
                                )

                            # Switch clock
                            game_clock.switch_turn(board_state.board.turn)

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
                                sound_manager.play_game_end_sound()
                                game_clock.pause()

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
                                    game_clock.reset()
                                    game_clock.start_game()
                                    move_animator.cancel()
                                    sound_manager.play_game_start_sound()

                                    engine_thinking = check_engine_turn_and_move(
                                        board_state, engine_controller, move_history
                                    )
                        else:
                            print(f"[Engine] ❌ Failed to apply move: {move_uci}")
                    else:
                        print(f"[Engine] ❌ Illegal move returned: {move_uci}")

                except Exception as e:
                    print(f"[Engine] ❌ Error applying move: {e}")

        move_animator.update()

        # -------------------- Rendering Phase --------------------

        # Clear screen
        screen.fill(Colors.BACKGROUND)

        # Draw board with squares and coordinates
        board_gui.draw_board()

        if Config.SHOW_LAST_MOVE and not move_animator.is_animating:
            board_gui.draw_last_move_highlight(board_state.board)

        # Draw check indicator
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

        # Draw pieces (hide piece being animated or dragged)
        for square in chess.SQUARES:
            # Skip if being animated
            if move_animator.is_square_being_animated(square):
                continue

            # Skip if being dragged
            if input_handler.dragging and square == input_handler.drag_start_square:
                continue

            piece = board_state.board.piece_at(square)
            if piece:
                board_gui._draw_piece(piece, square)

        # Render animated piece
        move_animator.render(screen)

        # Render dragged piece (only on human's turn)
        if not game_ended:
            human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
            if (
                board_state.board.turn == human_color
                and not engine_controller.is_thinking()
            ):
                input_handler.render_dragged_piece()

        # Draw captured pieces (if enabled)
        if Config.SHOW_CAPTURED_PIECES:
            captured_display.draw(board_state.board)

        # Draw game clock
        game_clock.draw(board_state.board.turn)

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
