"""
Configuration Settings
-----------------------------
Centralized configuration module for the chess application.

This module contains all configurable parameters for the chess GUI application,
including display settings, gameplay options, animation parameters, and file paths.
"""

import os


class Config:
    """
    Application configuration settings container.

    This class serves as a centralized configuration store using class attributes.
    The validate() method ensures configuration consistency and prevents runtime errors.
    """

    # ===================
    # Window Settings
    # ===================
    WINDOW_WIDTH = 980  # Window width in pixels (must accommodate board + UI panels)
    WINDOW_HEIGHT = 840  # Window height in pixels (must accommodate board + controls)
    WINDOW_TITLE = "Chess - Human vs Engine"
    FPS = 60

    # ===================
    # Board Settings
    # ===================
    BOARD_SIZE = (
        640  # Board size in pixels (MUST be divisible by 8 for proper square sizing)
    )
    SHOW_COORDINATES = (
        True  # Display algebraic notation labels (files: a-h, ranks: 1-8)
    )
    FLIP_BOARD = (
        False  # Board orientation: False = white on bottom, True = black on bottom
    )

    # ===================
    # UI Layout Settings
    # ===================
    BOARD_X = 40  # X-coordinate (horizontal) offset from left edge of window in pixels
    BOARD_Y = 80  # Y-coordinate (vertical) offset from top edge of window in pixels

    # Side panel configuration
    SIDE_PANEL_WIDTH = 240
    SIDE_PANEL_MARGIN = 40

    # Move history panel - positioned to the right of the board
    MOVE_HISTORY_X = BOARD_X + BOARD_SIZE + SIDE_PANEL_MARGIN
    MOVE_HISTORY_Y = BOARD_Y
    MOVE_HISTORY_WIDTH = SIDE_PANEL_WIDTH
    MOVE_HISTORY_HEIGHT = BOARD_SIZE

    # Game controls panel - top-right corner with icon buttons
    GAME_CONTROLS_X = MOVE_HISTORY_X
    GAME_CONTROLS_Y = 10
    GAME_CONTROLS_WIDTH = SIDE_PANEL_WIDTH
    GAME_CONTROLS_ICON_SIZE = 50
    GAME_CONTROLS_SPACING = 10
    GAME_CONTROLS_USE_ICONS = True

    # Captured pieces display - split into two sections with individual clocks
    # Each section: captured pieces on left, player clock on right

    # Captured pieces take 70% of board width, clock takes remaining space
    CAPTURED_PIECES_WIDTH = int(BOARD_SIZE * 0.7)
    PLAYER_CLOCK_WIDTH = BOARD_SIZE - CAPTURED_PIECES_WIDTH - 10

    # White's captured pieces - above the board
    CAPTURED_PIECES_WHITE_X = BOARD_X
    CAPTURED_PIECES_WHITE_Y = BOARD_Y - 60
    CAPTURED_PIECES_WHITE_WIDTH = CAPTURED_PIECES_WIDTH
    CAPTURED_PIECES_WHITE_HEIGHT = 50

    # White's clock - BELOW the board (right side, next to captured pieces)
    WHITE_CLOCK_X = BOARD_X + CAPTURED_PIECES_WIDTH + 10
    WHITE_CLOCK_Y = BOARD_Y + BOARD_SIZE + 10
    WHITE_CLOCK_WIDTH = PLAYER_CLOCK_WIDTH
    WHITE_CLOCK_HEIGHT = 50

    # Black's captured pieces - below the board
    CAPTURED_PIECES_BLACK_X = BOARD_X
    CAPTURED_PIECES_BLACK_Y = BOARD_Y + BOARD_SIZE + 10
    CAPTURED_PIECES_BLACK_WIDTH = CAPTURED_PIECES_WIDTH
    CAPTURED_PIECES_BLACK_HEIGHT = 50

    # Black's clock - ABOVE the board (right side, next to captured pieces)
    BLACK_CLOCK_X = BOARD_X + CAPTURED_PIECES_WIDTH + 10
    BLACK_CLOCK_Y = BOARD_Y - 60
    BLACK_CLOCK_WIDTH = PLAYER_CLOCK_WIDTH
    BLACK_CLOCK_HEIGHT = 50

    # ===================
    # Player Settings
    # ===================
    HUMAN_COLOR = "white"  # Color for human player: "white" or "black"
    # Engine color is automatically assigned as the opposite of human color
    # This ensures proper turn-based gameplay without manual configuration
    ENGINE_COLOR = HUMAN_COLOR == "white" and "black" or "white"

    # ===================
    # Engine Settings
    # ===================
    ENGINE_TIME_LIMIT = 5.0  # Time limit per move in seconds
    MCTS_ITERATIONS = 1000  # Number of MCTS simulations per move
    TEMPERATURE = 1.0  # Exploration parameter for move selection

    # ===================
    # Animation Settings
    # ===================
    ANIMATE_MOVES = True  # Enable smooth piece sliding animations during moves
    ANIMATION_SPEED = 300  # Duration of move animation in milliseconds
    SHOW_LAST_MOVE = (
        True  # Highlight the source and destination squares of the last move played
    )

    # ===================
    # Sound Settings
    # ===================
    ENABLE_SOUNDS = (
        True  # Master toggle for all sound effects (move sounds, captures, etc.)
    )
    SOUND_VOLUME = 0.5  # Master volume level: 0.0 (muted) to 1.0 (maximum volume)

    # ===================
    # UI Features
    # ===================
    # Optional user interface components that can be toggled on/off

    SHOW_CAPTURED_PIECES = True  # Display panel showing pieces captured by each player
    SHOW_GAME_CLOCK = True  # Display game timer/clock for timed matches
    SHOW_FPS = False  # Display current frames per second in the window

    # ===================
    # File Paths
    # ===================
    ASSETS_DIR = "assets"  # Root directory for all game assets
    PIECE_IMAGES_DIR = os.path.join(ASSETS_DIR, "pieces")  # Chess piece images
    SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")  # Sound effect files
    ICONS_DIR = os.path.join(ASSETS_DIR, "icons")  # Icon images

    # ===================
    # Debug Settings
    # ===================
    DEBUG_MODE = False  # Enable verbose debug output and additional error information
    LOG_MOVES = True  # Print move notation to console for debugging and game review

    @classmethod
    def validate(cls):
        """
        Validate all configuration settings for consistency and correctness.

        Returns:
            bool: True if all validations pass

        Raises:
            ValueError: If any configuration setting is invalid, with a detailed error message listing all validation failures
        """
        errors = []

        # Validate board size is divisible by 8
        # Each square is BOARD_SIZE / 8 pixels; fractional squares would cause rendering issues
        if cls.BOARD_SIZE % 8 != 0:
            errors.append(f"BOARD_SIZE ({cls.BOARD_SIZE}) must be divisible by 8")

        # Validate human color is a valid chess color
        if cls.HUMAN_COLOR not in ("white", "black"):
            errors.append(
                f"HUMAN_COLOR must be 'white' or 'black', got '{cls.HUMAN_COLOR}'"
            )

        # Validate window width can accommodate the board and panels
        min_width = (
            cls.BOARD_X
            + cls.BOARD_SIZE
            + cls.SIDE_PANEL_MARGIN
            + cls.SIDE_PANEL_WIDTH
            + 20
        )

        if cls.WINDOW_WIDTH < min_width:
            errors.append(
                f"WINDOW_WIDTH ({cls.WINDOW_WIDTH}) too small. "
                f"Minimum {min_width} needed for board + panels"
            )

        # Validate window height can accommodate the board
        min_height = cls.BOARD_Y + cls.BOARD_SIZE + 100
        if cls.WINDOW_HEIGHT < min_height:
            errors.append(
                f"WINDOW_HEIGHT ({cls.WINDOW_HEIGHT}) too small. "
                f"Minimum {min_height} needed for board display"
            )

        # Validate panels don't go off screen
        if hasattr(cls, "MOVE_HISTORY_X") and hasattr(cls, "MOVE_HISTORY_WIDTH"):
            panel_right_edge = cls.MOVE_HISTORY_X + cls.MOVE_HISTORY_WIDTH
            if panel_right_edge > cls.WINDOW_WIDTH:
                errors.append(
                    f"Move history panel extends beyond window edge. "
                    f"Panel ends at {panel_right_edge}px but window is {cls.WINDOW_WIDTH}px wide. "
                    f"Increase WINDOW_WIDTH to at least {panel_right_edge + 20}px"
                )

        # If any errors were found, raise an exception with all error messages
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))

        return True
