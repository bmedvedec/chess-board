"""
Configuration Settings
-----------------------------
Centralized configuration for the chess application.
Adjust these values to customize behavior.
"""

import os


class Config:
    """Application configuration settings."""

    # ===================
    # Window Settings
    # ===================
    WINDOW_WIDTH = 980
    WINDOW_HEIGHT = 840
    WINDOW_TITLE = "Chess - Human vs Engine"
    FPS = 60

    # ===================
    # Board Settings
    # ===================
    BOARD_SIZE = 640  # Board size in pixels (should be divisible by 8)
    SHOW_COORDINATES = True  # Show file/rank labels (a-h, 1-8)
    FLIP_BOARD = False  # True to play as black (board flipped)

    # ===================
    # UI Layout Settings
    # ===================
    # Board position - LEFT aligned
    BOARD_X = 40
    BOARD_Y = 80

    # ===================
    # Player Settings
    # ===================
    HUMAN_COLOR = "white"  # "white" or "black"
    ENGINE_COLOR = HUMAN_COLOR == "white" and "black" or "white"  # Opposite of human

    # ===================
    # Animation Settings
    # ===================
    ANIMATE_MOVES = True  # Enable move animations
    ANIMATION_SPEED = 300  # Animation duration in milliseconds
    SHOW_LAST_MOVE = True  # Highlight last move

    # ===================
    # Sound Settings
    # ===================
    ENABLE_SOUNDS = True
    SOUND_VOLUME = 0.5  # 0.0 to 1.0

    # ===================
    # Chapter 8: UI Features
    # ===================
    SHOW_CAPTURED_PIECES = True  # Display captured pieces
    SHOW_GAME_CLOCK = False  # Show game timer/clock

    # ===================
    # File Paths
    # ===================
    ASSETS_DIR = "assets"
    PIECE_IMAGES_DIR = os.path.join(ASSETS_DIR, "pieces")
    SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

    # ===================
    # Debug Settings
    # ===================
    DEBUG_MODE = False
    SHOW_FPS = False
    LOG_MOVES = True

    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        errors = []

        if cls.BOARD_SIZE % 8 != 0:
            errors.append(f"BOARD_SIZE ({cls.BOARD_SIZE}) must be divisible by 8")

        if cls.HUMAN_COLOR not in ("white", "black"):
            errors.append(
                f"HUMAN_COLOR must be 'white' or 'black', got '{cls.HUMAN_COLOR}'"
            )

        # Validate window can fit board
        min_width = cls.BOARD_X + cls.BOARD_SIZE + 20

        if cls.WINDOW_WIDTH < min_width:
            errors.append(
                f"WINDOW_WIDTH ({cls.WINDOW_WIDTH}) too small. "
                f"Minimum {min_width} needed for board display"
            )

        # Validate height fits board
        min_height = cls.BOARD_Y + cls.BOARD_SIZE + 100
        if cls.WINDOW_HEIGHT < min_height:
            errors.append(
                f"WINDOW_HEIGHT ({cls.WINDOW_HEIGHT}) too small. "
                f"Minimum {min_height} needed for board display"
            )

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))

        return True
