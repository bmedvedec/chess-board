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

from utils.config import Config
from gui.colors import Colors
from gui.board_state import BoardState


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


def initialize_engine():
    """
    Load and initialize the chess engine model.

    Placeholder for loading a neural network or traditional
    chess engine that will serve as the AI opponent.

    Returns:
        None: Currently returns None as engine integration is not yet implemented.
            Future implementations will return an engine instance.

    TODO:
        - Implement model loading logic
        - Add error handling for missing model files
        - Configure engine strength/difficulty settings
    """
    print("[Warning] Engine loading not implemented yet")
    return None


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
    board = BoardState()
    print(f"[✓] Chess board initialized")
    print(f"    Starting FEN: {board.get_fen()}")

    # Display chess board statistics for verification
    print(f"    Legal moves: {board.count_legal_moves()} available")
    print(f"    Turn: {board.get_turn_string()}")

    # Initialize the chess engine (AI opponent)
    # Currently a placeholder - will load trained model in future
    model = initialize_engine()

    # Notify user that display test is running
    print("\n[Info] Running display test...")
    print("[Info] Close window or press ESC to exit\n")
    print("[Info] Press 'R' to reset board, 'U' to undo move\n")

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
                    board.reset()
                    print("[Action] Board reset")
                    print(f"    Status: {board.get_game_status()}")
                # U key undoes the last move made
                elif event.key == pygame.K_u:
                    undone = board.undo_move()
                    if undone:
                        print(f"[Action] Undone move: {undone.uci()}")
                    else:
                        print("[Action] No moves to undo")
                    print(f"    Status: {board.get_game_status()}")

        # -------------------- Rendering Phase --------------------
        # Clear the screen with background color
        screen.fill(Colors.BACKGROUND)

        # Calculate centered position for the chess board
        # Board is centered both horizontally and vertically in the window
        board_rect = pygame.Rect(
            (Config.WINDOW_WIDTH - Config.BOARD_SIZE) // 2,
            (Config.WINDOW_HEIGHT - Config.BOARD_SIZE) // 2,
            Config.BOARD_SIZE,
            Config.BOARD_SIZE,
        )

        # Draw the checkerboard pattern (8x8 grid)
        square_size = Config.BOARD_SIZE // 8
        for row in range(8):
            for col in range(8):
                # Calculate pixel position for this square
                x = board_rect.x + col * square_size
                y = board_rect.y + row * square_size

                # Determine square color using checkerboard pattern
                # Light squares occur when row + col is even
                is_light = (row + col) % 2 == 0
                color = Colors.LIGHT_SQUARE if is_light else Colors.DARK_SQUARE

                # Draw the square at the calculated position
                pygame.draw.rect(screen, color, (x, y, square_size, square_size))

        # Update the display with all rendered graphics
        # flip() updates the entire display surface
        pygame.display.flip()

        # -------------------- Frame Rate Control --------------------
        # Limit the loop to run at the configured FPS
        # This prevents excessive CPU usage and ensures smooth animation
        clock.tick(Config.FPS)

    # ==================== Cleanup Phase ====================
    # Properly shut down pygame and release resources
    pygame.quit()
    print("\n" + "=" * 50)
    print("Final Game State:")
    print(f"    Moves played: {len(board.get_move_history_uci())}")
    print(f"    Status: {board.get_game_status()}")
    if board.get_move_history_san():
        print(f"    Move history: {' '.join(board.get_move_history_san())}")
    print("[✓] Application closed cleanly")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    # Entry point guard - ensures main() only runs when script is executed directly
    # (not when imported as a module)
    sys.exit(main())
