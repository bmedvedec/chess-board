"""
Chess GUI Application
---------------------
Main entry point for the chess application with graphical interface.

This module provides the core game loop and initialization for a chess application
that supports human vs engine gameplay with move visualization. The application
uses pygame for rendering and the python-chess library for chess logic.
"""

import sys
from typing import List
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
    save_pgn_to_file,
    load_pgn_from_file,
)
from gui.move_animator import MoveAnimator
from gui.captured_pieces_display import CapturedPiecesDisplay
from gui.sound_manager import SoundManager
from gui.player_clock import PlayerClock
from gui.time_control_dialog import TimeControlDialog
from gui.settings_menu import SettingsMenu
from gui.help_screen import HelpScreen
from gui.layout_handler import LayoutHandler
from gui.color_selection_dialog import ColorSelectionDialog

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


def navigate_to_move(move_index: int, full_move_history: List[str]):
    """
    Create a board state at a specific move in the history.

    Args:
        move_index: Index in move history (0 = after first move, -1 = current)
        full_move_history: Complete move history in UCI format

    Returns:
        New BoardState at the requested position
    """
    # Create fresh board
    nav_state = BoardState()

    # Replay moves up to and including the selected move
    moves_to_play = move_index + 1 if move_index >= 0 else len(full_move_history)

    for i in range(min(moves_to_play, len(full_move_history))):
        move_uci = full_move_history[i]
        nav_state.make_move_uci(move_uci)

    return nav_state


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


def reset_game_state(
    board_state,
    input_handler,
    move_history,
    engine_controller,
    move_panel,
    white_clock,
    black_clock,
    move_animator,
    sound_manager,
    time_control,
):
    """
    Helper function to reset all game state for a new game.

    Args:
        board_state: BoardState to reset
        input_handler: InputHandler to reset
        move_history: List to clear
        engine_controller: EngineController to cancel
        move_panel: MoveHistoryPanel to scroll
        white_clock: White PlayerClock to reset
        black_clock: Black PlayerClock to reset
        move_animator: MoveAnimator to cancel
        sound_manager: SoundManager for sound
        time_control: Time control in seconds (or None)

    Returns:
        tuple: (game_ended=False, last_result=None)
    """
    board_state.reset()
    input_handler.reset()
    move_history.clear()
    engine_controller.cancel_thinking()
    move_panel.scroll_to_top()

    # Reset both clocks with time control
    white_clock.reset(time_control)
    black_clock.reset(time_control)
    white_clock.start()
    black_clock.start()
    white_clock.activate()
    white_clock.resume()

    move_animator.cancel()
    sound_manager.play_game_start_sound()

    return False, None  # game_ended, last_result


def show_game_setup_dialogs(screen, time_control_dialog, color_selection_dialog):
    """
    Show both time control and color selection dialogs.

    Args:
        screen: pygame.Surface for rendering dialogs
        time_control_dialog: TimeControlDialog instance
        color_selection_dialog: ColorSelectionDialog instance

    Returns:
        tuple: (selected_time_control, selected_color)
            - selected_time_control: Time in seconds or None for unlimited
            - selected_color: "white" or "black"
    """
    # Show time control dialog
    selected_time_control = time_control_dialog.show()

    if selected_time_control is None:
        print("✅ Time control: Unlimited")
    else:
        minutes = selected_time_control // 60
        print(f"✅ Time control: {minutes} minutes per player")

    # Show color selection dialog
    selected_color = color_selection_dialog.show()

    # Update Config with selected color
    setattr(Config, "HUMAN_COLOR", selected_color)
    setattr(Config, "ENGINE_COLOR", "black" if selected_color == "white" else "white")

    print(f"✅ Color selected: Human plays as {selected_color.upper()}")
    print(f"   Engine plays as {Config.ENGINE_COLOR.upper()}")

    # Optional: Flip board when playing as Black
    if selected_color == "black":
        setattr(Config, "FLIP_BOARD", True)
    else:
        setattr(Config, "FLIP_BOARD", False)

    return selected_time_control, selected_color


def start_new_game_with_dialogs(
    board_state,
    input_handler,
    move_history,
    engine_controller,
    move_panel,
    white_clock,
    black_clock,
    move_animator,
    sound_manager,
    screen,
    time_control_dialog,
    color_selection_dialog,
):
    """
    Start a new game by showing setup dialogs and resetting all game state.

    This function:
    1. Shows time control and color selection dialogs
    2. Resets the board and all game components
    3. Applies the new settings
    4. Returns control to the main loop

    Args:
        board_state: BoardState instance
        input_handler: InputHandler instance
        move_history: List of moves
        engine_controller: EngineController instance
        move_panel: MoveHistoryPanel instance
        white_clock: White player's clock
        black_clock: Black player's clock
        move_animator: MoveAnimator instance
        sound_manager: SoundManager instance
        screen: pygame.Surface for rendering dialogs
        time_control_dialog: TimeControlDialog instance
        color_selection_dialog: ColorSelectionDialog instance

    Returns:
        tuple: (game_ended, last_result, new_time_control)
            - game_ended: False (game just started)
            - last_result: None (no previous result)
            - new_time_control: The selected time control in seconds
    """
    print("\n[New Game] Showing setup dialogs...")

    # Show dialogs to get new settings
    new_time_control, new_color = show_game_setup_dialogs(
        screen, time_control_dialog, color_selection_dialog
    )

    # Cancel any engine thinking
    engine_controller.cancel_thinking()

    # Reset board and game state
    board_state.reset()
    input_handler.reset()
    move_history.clear()
    move_panel.scroll_to_top()

    # Reset both clocks with new time control
    white_clock.reset(new_time_control)
    black_clock.reset(new_time_control)
    white_clock.start()
    black_clock.start()
    white_clock.activate()
    white_clock.resume()

    # Cancel any animations
    move_animator.cancel()

    # Play game start sound
    sound_manager.play_game_start_sound()

    print(
        f"[New Game] Started - Time: {new_time_control}s, Color: {Config.HUMAN_COLOR}"
    )
    print(f"    Status: {board_state.get_game_status()}")

    # Return updated game state
    return False, None, new_time_control


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
        icon_size=Config.GAME_CONTROLS_ICON_SIZE,
        spacing=Config.GAME_CONTROLS_SPACING,
    )
    print("✅ Game state management components initialized")

    # Initialize move animator
    move_animator = MoveAnimator(board_gui)
    print("✅ Move animator initialized")

    # Initialize captured pieces display
    captured_display = CapturedPiecesDisplay(
        screen,
        white_x=Config.CAPTURED_PIECES_WHITE_X,
        white_y=Config.CAPTURED_PIECES_WHITE_Y,
        white_width=Config.CAPTURED_PIECES_WHITE_WIDTH,
        white_height=Config.CAPTURED_PIECES_WHITE_HEIGHT,
        black_x=Config.CAPTURED_PIECES_BLACK_X,
        black_y=Config.CAPTURED_PIECES_BLACK_Y,
        black_width=Config.CAPTURED_PIECES_BLACK_WIDTH,
        black_height=Config.CAPTURED_PIECES_BLACK_HEIGHT,
    )
    print("✅ Captured pieces display initialized")

    # Initialize sound manager
    sound_manager = SoundManager()
    print("✅ Sound manager initialized")

    # Create dialog instances
    time_control_dialog = TimeControlDialog(screen)
    color_selection_dialog = ColorSelectionDialog(screen)

    # Show game setup dialogs (time control + color selection)
    selected_time_control, selected_color = show_game_setup_dialogs(
        screen, time_control_dialog, color_selection_dialog
    )
    game_time_control = selected_time_control

    # Initialize individual player clocks
    white_clock = PlayerClock(
        screen,
        x=Config.WHITE_CLOCK_X,
        y=Config.WHITE_CLOCK_Y,
        width=Config.WHITE_CLOCK_WIDTH,
        height=Config.WHITE_CLOCK_HEIGHT,
        player_name="White",
        player_color=chess.WHITE,
        time_control=selected_time_control,
    )

    black_clock = PlayerClock(
        screen,
        x=Config.BLACK_CLOCK_X,
        y=Config.BLACK_CLOCK_Y,
        width=Config.BLACK_CLOCK_WIDTH,
        height=Config.BLACK_CLOCK_HEIGHT,
        player_name="Black",
        player_color=chess.BLACK,
        time_control=selected_time_control,
    )

    # Start both clocks (paused initially)
    white_clock.start()
    black_clock.start()
    # Activate white's clock (white moves first)
    white_clock.activate()
    white_clock.resume()

    print("✅ Player clocks initialized")

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

    # Store time control for game resets
    game_time_control = selected_time_control

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

                # Left arrow - previous halfmove
                elif event.key == pygame.K_LEFT:
                    # Previous halfmove
                    current_idx = len(board_state.board.move_stack) - 1
                    if current_idx > 0:  # Can go back
                        target_idx = current_idx - 1
                        board_state = navigate_to_move(target_idx, move_history)
                        input_handler.board_state = board_state
                        input_handler.reset()
                        print(
                            f"[Navigation] ← Previous move (position {target_idx + 1})"
                        )
                    elif current_idx == 0:  # At first move, go to start
                        board_state = navigate_to_move(-1, move_history)
                        input_handler.board_state = board_state
                        input_handler.reset()
                        print(f"[Navigation] ← Start position")

                # Right arrow - next halfmove
                elif event.key == pygame.K_RIGHT:
                    # Next halfmove
                    current_idx = len(board_state.board.move_stack) - 1
                    if current_idx < len(move_history) - 1:
                        target_idx = current_idx + 1
                        board_state = navigate_to_move(target_idx, move_history)
                        input_handler.board_state = board_state
                        input_handler.reset()
                        print(f"[Navigation] → Next move (position {target_idx + 1})")

                # Up arrow - jump to first move
                elif event.key == pygame.K_UP:
                    # Jump to first move
                    if move_history:
                        board_state = navigate_to_move(0, move_history)
                        input_handler.board_state = board_state
                        input_handler.reset()
                        print(f"[Navigation] ↑ First move")

                # Down arrow - jump to last played move
                elif event.key == pygame.K_DOWN:
                    # Jump to last played move
                    if move_history:
                        target_idx = len(move_history) - 1
                        board_state = navigate_to_move(target_idx, move_history)
                        input_handler.board_state = board_state
                        input_handler.reset()
                        print(f"[Navigation] ↓ Last move (latest position)")

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
                    game_ended, last_result, game_time_control = (
                        start_new_game_with_dialogs(
                            board_state,
                            input_handler,
                            move_history,
                            engine_controller,
                            move_panel,
                            white_clock,
                            black_clock,
                            move_animator,
                            sound_manager,
                            screen,
                            time_control_dialog,
                            color_selection_dialog,
                        )
                    )
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
                    icon_size=Config.GAME_CONTROLS_ICON_SIZE,
                    spacing=Config.GAME_CONTROLS_SPACING,
                )
                captured_display = CapturedPiecesDisplay(
                    screen,
                    white_x=Config.CAPTURED_PIECES_WHITE_X,
                    white_y=Config.CAPTURED_PIECES_WHITE_Y,
                    white_width=Config.CAPTURED_PIECES_WHITE_WIDTH,
                    white_height=Config.CAPTURED_PIECES_WHITE_HEIGHT,
                    black_x=Config.CAPTURED_PIECES_BLACK_X,
                    black_y=Config.CAPTURED_PIECES_BLACK_Y,
                    black_width=Config.CAPTURED_PIECES_BLACK_WIDTH,
                    black_height=Config.CAPTURED_PIECES_BLACK_HEIGHT,
                )

                # Recreate player clocks - preserve state from old clocks
                # Save state before recreating
                old_white_time = (
                    white_clock.time_remaining
                    if hasattr(white_clock, "time_remaining")
                    else game_time_control
                )
                old_black_time = (
                    black_clock.time_remaining
                    if hasattr(black_clock, "time_remaining")
                    else game_time_control
                )
                old_white_is_active = (
                    white_clock.is_active
                    if hasattr(white_clock, "is_active")
                    else (board_state.board.turn == chess.WHITE)
                )
                old_paused = (
                    white_clock.paused if hasattr(white_clock, "paused") else True
                )

                white_clock = PlayerClock(
                    screen,
                    x=Config.WHITE_CLOCK_X,
                    y=Config.WHITE_CLOCK_Y,
                    width=Config.WHITE_CLOCK_WIDTH,
                    height=Config.WHITE_CLOCK_HEIGHT,
                    player_name="White",
                    player_color=chess.WHITE,
                    time_control=game_time_control,
                )

                black_clock = PlayerClock(
                    screen,
                    x=Config.BLACK_CLOCK_X,
                    y=Config.BLACK_CLOCK_Y,
                    width=Config.BLACK_CLOCK_WIDTH,
                    height=Config.BLACK_CLOCK_HEIGHT,
                    player_name="Black",
                    player_color=chess.BLACK,
                    time_control=game_time_control,
                )

                # Restore clock state
                if game_time_control is not None:  # Only restore if using time controls
                    white_clock.time_remaining = old_white_time
                    black_clock.time_remaining = old_black_time
                    white_clock.start()  # Initialize
                    black_clock.start()
                    if old_white_is_active:
                        white_clock.activate()
                    else:
                        black_clock.activate()
                    if not old_paused:
                        if old_white_is_active:
                            white_clock.resume()
                        else:
                            black_clock.resume()

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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check for game controls clicks
                    button_id = game_controls.handle_click(event.pos)

                    # Handle New Game button click
                    if button_id == "new_game":
                        print("[Action] New Game button pressed")
                        game_ended, last_result, game_time_control = (
                            start_new_game_with_dialogs(
                                board_state,
                                input_handler,
                                move_history,
                                engine_controller,
                                move_panel,
                                white_clock,
                                black_clock,
                                move_animator,
                                sound_manager,
                                screen,
                                time_control_dialog,
                                color_selection_dialog,
                            )
                        )

                        # Check if engine should move first
                        engine_thinking = check_engine_turn_and_move(
                            board_state, engine_controller, move_history
                        )

                    # Handle save button click
                    if button_id == "save_pgn":
                        if len(board_state.board.move_stack) > 0:
                            filepath = game_controls.show_save_dialog()
                            if filepath:
                                pgn_string = board_state.to_pgn()
                                if save_pgn_to_file(pgn_string, filepath):
                                    print(f"[Action] ✅ Game saved to: {filepath}")

                    # Handle load button click
                    elif button_id == "load_pgn":
                        filepath = game_controls.show_load_dialog()
                        if filepath:
                            pgn_string = load_pgn_from_file(filepath)
                            if pgn_string:
                                try:
                                    new_state = BoardState.from_pgn(pgn_string)
                                    board_state = new_state
                                    move_history = board_state.get_move_history_uci()
                                    input_handler.board_state = board_state
                                    move_panel.scroll_to_bottom()
                                    game_ended = False
                                    last_result = None
                                    print(f"[Action] ✅ Game loaded: {filepath}")
                                except Exception as e:
                                    print(f"[Action] ❌ Failed to load: {e}")

                    # Handle resign button click
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

                        # Pause both clocks
                        white_clock.pause()
                        black_clock.pause()

                        # Show result dialog
                        choice = result_dialog.show("resignation", winner, "")
                        if choice == "new_game":
                            game_ended, last_result, game_time_control = (
                                start_new_game_with_dialogs(
                                    board_state,
                                    input_handler,
                                    move_history,
                                    engine_controller,
                                    move_panel,
                                    white_clock,
                                    black_clock,
                                    move_animator,
                                    sound_manager,
                                    screen,
                                    time_control_dialog,
                                    color_selection_dialog,
                                )
                            )
                            engine_thinking = check_engine_turn_and_move(
                                board_state, engine_controller, move_history
                            )

                    # Move history click navigation
                    else:
                        # Check if user clicked on move history panel
                        clicked_move_idx = move_panel.handle_click(event.pos)

                        # If a move was clicked, navigate to that position
                        if clicked_move_idx is not None and clicked_move_idx < len(
                            move_history
                        ):
                            print(
                                f"[Navigation] Jumped to position after move {clicked_move_idx + 1}"
                            )

                            # Create new board state at that position
                            board_state = navigate_to_move(
                                clicked_move_idx, move_history
                            )

                            # Update references
                            input_handler.board_state = board_state
                            input_handler.reset()

                            # Cancel any thinking
                            engine_controller.cancel_thinking()

                            # This is navigation mode - viewing only
                            # To resume play, user clicks "New Game"
                            print(f"[Navigation] Position: {board_state.get_fen()}")
                            print("[Navigation] Click 'New Game' to start fresh game")

                        elif not game_ended:
                            human_color = (
                                chess.WHITE
                                if Config.HUMAN_COLOR == "white"
                                else chess.BLACK
                            )
                            # Allow mouse down during engine thinking if premove enabled
                            if board_state.board.turn == human_color or (
                                Config.ENABLE_PREMOVE
                                and engine_controller.is_thinking()
                            ):
                                input_handler.handle_mouse_down(
                                    event.pos, engine_controller.is_thinking()
                                )

            # Mouse button up - handle move completion
            elif event.type == pygame.MOUSEBUTTONUP and not game_ended:
                if event.button == 1:  # Left click release
                    human_color = (
                        chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
                    )
                    # Allow mouse up during engine thinking if premove enabled
                    if board_state.board.turn == human_color or (
                        Config.ENABLE_PREMOVE and engine_controller.is_thinking()
                    ):
                        # Try to complete drag move (may be premove)
                        move_made = input_handler.handle_mouse_up(
                            event.pos, engine_controller.is_thinking()
                        )

                        # If no drag move was made, handle as click-to-move
                        if not move_made:
                            move_made = input_handler.handle_mouse_click(
                                event.pos, engine_controller.is_thinking()
                            )

                        # If player made a move, add to history and check for engine turn
                        if move_made:
                            # Get the last move from board
                            if board_state.board.move_stack:
                                last_move = board_state.board.peek()
                                move_history.append(last_move.uci())
                                move_panel.scroll_to_bottom()

                                # Start move animation ONLY for click-to-move
                                # Check how the move was made
                                move_method = input_handler.get_last_move_method()

                                if move_method == "click":
                                    # Animate click-to-move
                                    piece_at_dest = board_state.board.piece_at(
                                        last_move.to_square
                                    )
                                    if piece_at_dest:
                                        move_animator.start_animation(
                                            piece_at_dest,
                                            last_move.from_square,
                                            last_move.to_square,
                                        )
                                # If move_method == "drag", skip animation

                                # Clear the move method tracking
                                input_handler.clear_move_method()

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

                                # Switch active clock based on whose turn it is
                                if board_state.board.turn == chess.WHITE:
                                    white_clock.activate()
                                    white_clock.resume()
                                    black_clock.deactivate()
                                else:
                                    black_clock.activate()
                                    black_clock.resume()
                                    white_clock.deactivate()

                            # Check for game end
                            is_over, result_type, winner, reason = (
                                check_game_end_conditions(board_state)
                            )
                            if is_over:
                                game_ended = True
                                last_result = (result_type, winner, reason)
                                sound_manager.play_game_end_sound()

                                # Pause both clocks
                                white_clock.pause()
                                black_clock.pause()

                                print(f"[Game] Game over: {result_type}")
                                if winner:
                                    print(f"       Winner: {winner}")
                                if reason:
                                    print(f"       Reason: {reason}")

                                # Show result dialog
                                choice = result_dialog.show(result_type, winner, reason)
                                if choice == "new_game":
                                    game_ended, last_result, game_time_control = (
                                        start_new_game_with_dialogs(
                                            board_state,
                                            input_handler,
                                            move_history,
                                            engine_controller,
                                            move_panel,
                                            white_clock,
                                            black_clock,
                                            move_animator,
                                            sound_manager,
                                            screen,
                                            time_control_dialog,
                                            color_selection_dialog,
                                        )
                                    )

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
                # Allow mouse motion during engine thinking if premove enabled
                if board_state.board.turn == human_color or (
                    Config.ENABLE_PREMOVE and engine_controller.is_thinking()
                ):
                    input_handler.handle_mouse_motion(
                        event.pos, engine_controller.is_thinking()
                    )

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

                            # Switch active clock
                            if board_state.board.turn == chess.WHITE:
                                white_clock.activate()
                                white_clock.resume()
                                black_clock.deactivate()
                            else:
                                black_clock.activate()
                                black_clock.resume()
                                white_clock.deactivate()

                            print(f"[Engine] Move made: {move_san} ({move_uci})")
                            print(f"         Status: {board_state.get_game_status()}")
                            input_handler.soft_reset()

                            # Check for game end
                            is_over, result_type, winner, reason = (
                                check_game_end_conditions(board_state)
                            )
                            if is_over:
                                game_ended = True
                                last_result = (result_type, winner, reason)
                                sound_manager.play_game_end_sound()

                                # Pause both clocks
                                white_clock.pause()
                                black_clock.pause()

                                print(f"[Game] Game over: {result_type}")
                                if winner:
                                    print(f"       Winner: {winner}")
                                if reason:
                                    print(f"       Reason: {reason}")

                                # Show result dialog
                                choice = result_dialog.show(result_type, winner, reason)
                                if choice == "new_game":
                                    game_ended, last_result, game_time_control = (
                                        start_new_game_with_dialogs(
                                            board_state,
                                            input_handler,
                                            move_history,
                                            engine_controller,
                                            move_panel,
                                            white_clock,
                                            black_clock,
                                            move_animator,
                                            sound_manager,
                                            screen,
                                            time_control_dialog,
                                            color_selection_dialog,
                                        )
                                    )

                                    engine_thinking = check_engine_turn_and_move(
                                        board_state, engine_controller, move_history
                                    )

                            else:
                                # Game continues - execute premove if queued
                                if input_handler.has_premove():
                                    premove_made = (
                                        input_handler.execute_next_premove_if_valid()
                                    )
                                    if premove_made:
                                        # Premove was executed - handle as a regular move
                                        if board_state.board.move_stack:
                                            last_move = board_state.board.peek()
                                            move_history.append(last_move.uci())
                                            # Play sound, check game end, etc.

                                            # Start move animation ONLY for click-to-move
                                            # Check how the move was made
                                            move_method = (
                                                input_handler.get_last_move_method()
                                            )

                                            if move_method == "click":
                                                # Animate click-to-move
                                                piece_at_dest = (
                                                    board_state.board.piece_at(
                                                        last_move.to_square
                                                    )
                                                )
                                                if piece_at_dest:
                                                    move_animator.start_animation(
                                                        piece_at_dest,
                                                        last_move.from_square,
                                                        last_move.to_square,
                                                    )
                                            # If move_method == "drag", skip animation

                                            # Clear the move method tracking
                                            input_handler.clear_move_method()

                                            # Play move sound
                                            is_capture = board_state.board.is_capture(
                                                last_move
                                            )
                                            is_check = board_state.board.is_check()
                                            is_castle = board_state.board.is_castling(
                                                last_move
                                            )

                                            if is_castle:
                                                sound_manager.play_castle_sound()
                                            elif last_move.promotion:
                                                sound_manager.play_promotion_sound()
                                            else:
                                                sound_manager.play_move_sound(
                                                    is_capture=is_capture,
                                                    is_check=is_check,
                                                )

                                            # Switch active clock based on whose turn it is
                                            if board_state.board.turn == chess.WHITE:
                                                white_clock.activate()
                                                white_clock.resume()
                                                black_clock.deactivate()
                                            else:
                                                black_clock.activate()
                                                black_clock.resume()
                                                white_clock.deactivate()

                                        # Check for game end
                                        is_over, result_type, winner, reason = (
                                            check_game_end_conditions(board_state)
                                        )
                                        if is_over:
                                            game_ended = True
                                            last_result = (result_type, winner, reason)
                                            sound_manager.play_game_end_sound()

                                            # Pause both clocks
                                            white_clock.pause()
                                            black_clock.pause()

                                            print(f"[Game] Game over: {result_type}")
                                            if winner:
                                                print(f"       Winner: {winner}")
                                            if reason:
                                                print(f"       Reason: {reason}")

                                            # Show result dialog
                                            choice = result_dialog.show(
                                                result_type, winner, reason
                                            )
                                            if choice == "new_game":
                                                (
                                                    game_ended,
                                                    last_result,
                                                    game_time_control,
                                                ) = start_new_game_with_dialogs(
                                                    board_state,
                                                    input_handler,
                                                    move_history,
                                                    engine_controller,
                                                    move_panel,
                                                    white_clock,
                                                    black_clock,
                                                    move_animator,
                                                    sound_manager,
                                                    screen,
                                                    time_control_dialog,
                                                    color_selection_dialog,
                                                )

                                                engine_thinking = (
                                                    check_engine_turn_and_move(
                                                        board_state,
                                                        engine_controller,
                                                        move_history,
                                                    )
                                                )
                                        else:
                                            engine_thinking = (
                                                check_engine_turn_and_move(
                                                    board_state,
                                                    engine_controller,
                                                    move_history,
                                                )
                                            )

                        else:
                            print(f"[Engine] ❌ Failed to apply move: {move_uci}")
                    else:
                        print(f"[Engine] ❌ Illegal move returned: {move_uci}")

                except Exception as e:
                    print(f"[Engine] ❌ Error applying move: {e}")

        # Check for time expiration (optional - only if using timed games)
        if not game_ended:
            if white_clock.is_time_expired():
                # White ran out of time - check if Black can win

                # Check if Black has insufficient material to deliver checkmate
                if board_state.board.has_insufficient_material(chess.BLACK):
                    # Draw - Black cannot checkmate even with infinite time
                    game_ended = True
                    last_result = ("draw", None, "insufficient material")
                    sound_manager.play_game_end_sound()
                    white_clock.pause()
                    black_clock.pause()

                    print(
                        "[Game] Time forfeit, but draw - Black has insufficient mating material"
                    )
                    choice = result_dialog.show("draw", None, "insufficient material")
                else:
                    # Black wins on time
                    game_ended = True
                    last_result = ("time_forfeit", "Black", "White ran out of time")
                    sound_manager.play_game_end_sound()
                    white_clock.pause()
                    black_clock.pause()

                    print("[Game] Time expired: White ran out of time - Black wins")
                    choice = result_dialog.show(
                        "time_forfeit", "Black", "White ran out of time"
                    )

                if choice == "new_game":
                    game_ended, last_result, game_time_control = (
                        start_new_game_with_dialogs(
                            board_state,
                            input_handler,
                            move_history,
                            engine_controller,
                            move_panel,
                            white_clock,
                            black_clock,
                            move_animator,
                            sound_manager,
                            screen,
                            time_control_dialog,
                            color_selection_dialog,
                        )
                    )
                    engine_thinking = check_engine_turn_and_move(
                        board_state, engine_controller, move_history
                    )

            elif black_clock.is_time_expired():
                # Black ran out of time - check if White can win

                # Check if White has insufficient material to deliver checkmate
                if board_state.board.has_insufficient_material(chess.WHITE):
                    # Draw - White cannot checkmate even with infinite time
                    game_ended = True
                    last_result = ("draw", None, "insufficient material")
                    sound_manager.play_game_end_sound()
                    white_clock.pause()
                    black_clock.pause()

                    print(
                        "[Game] Time forfeit, but draw - White has insufficient mating material"
                    )
                    choice = result_dialog.show("draw", None, "insufficient material")
                else:
                    # White wins on time
                    game_ended = True
                    last_result = ("time_forfeit", "White", "Black ran out of time")
                    sound_manager.play_game_end_sound()
                    white_clock.pause()
                    black_clock.pause()

                    print("[Game] Time expired: Black ran out of time - White wins")
                    choice = result_dialog.show(
                        "time_forfeit", "White", "Black ran out of time"
                    )

                if choice == "new_game":
                    game_ended, last_result, game_time_control = (
                        start_new_game_with_dialogs(
                            board_state,
                            input_handler,
                            move_history,
                            engine_controller,
                            move_panel,
                            white_clock,
                            black_clock,
                            move_animator,
                            sound_manager,
                            screen,
                            time_control_dialog,
                            color_selection_dialog,
                        )
                    )
                    engine_thinking = check_engine_turn_and_move(
                        board_state, engine_controller, move_history
                    )

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

        # Draw square highlights UNDER pieces
        if not game_ended:
            human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
            if board_state.board.turn == human_color or (
                Config.ENABLE_PREMOVE and engine_controller.is_thinking()
            ):
                input_handler.render_square_highlights(engine_controller.is_thinking())

        # Decide which board to use for drawing pieces
        if Config.ENABLE_PREMOVE and input_handler.has_premove():
            draw_board = input_handler.build_visual_board()
        else:
            draw_board = board_state.board

        # Draw pieces (hide piece being animated or dragged)
        for square in chess.SQUARES:
            # Skip if being animated
            if move_animator.is_square_being_animated(square):
                continue

            # Skip if being dragged
            if input_handler.dragging and square == input_handler.drag_start_square:
                continue

            piece = draw_board.piece_at(square)
            if piece:
                board_gui._draw_piece(piece, square)

        # Draw legal move dots OVER pieces
        if not game_ended:
            human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
            if board_state.board.turn == human_color or (
                Config.ENABLE_PREMOVE and engine_controller.is_thinking()
            ):
                input_handler.render_legal_move_dots(engine_controller.is_thinking())

        # Render animated piece
        move_animator.render(screen)

        # Render dragged piece (on human's turn OR during engine thinking if premove)
        if not game_ended:
            human_color = chess.WHITE if Config.HUMAN_COLOR == "white" else chess.BLACK
            if board_state.board.turn == human_color or (
                Config.ENABLE_PREMOVE and engine_controller.is_thinking()
            ):
                input_handler.render_dragged_piece()
                board_gui.draw_premove_arrows(input_handler.premove_queue)

        # Draw captured pieces (if enabled)
        if Config.SHOW_CAPTURED_PIECES:
            captured_display.draw(board_state.board)

        # Draw player clocks
        white_clock.draw()
        black_clock.draw()

        # Calculate current move index for highlighting
        current_move_idx = (
            len(board_state.board.move_stack) - 1
            if board_state.board.move_stack
            else -1
        )

        # Convert UCI move history to SAN for display
        # Use the ORIGINAL move_history (not board_state's) to show all moves even during navigation
        full_san_history = []
        temp_board = BoardState()
        for move_uci in move_history:
            temp_board.make_move_uci(move_uci)
        full_san_history = temp_board.get_move_history_san()

        move_panel.draw(full_san_history, current_move_idx)

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
