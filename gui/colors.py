"""
Color Constants for Chess GUI
-----------------------------
This module defines all RGB and RGBA color values used throughout the chess
application, including board colors, highlights, UI elements, and visual feedback.

Color Format:
    - RGB: (red, green, blue) - Values from 0-255, fully opaque
    - RGBA: (red, green, blue, alpha) - Alpha from 0 (transparent) to 255 (opaque)
"""


class Colors:
    """
    Color constants container for the chess board GUI.

    Organizes all color values into logical categories for easy maintenance and modification.
    """

    # ===================
    # Board Square Colors
    # ===================
    LIGHT_SQUARE = (240, 217, 181)  # Light squares - warm beige tone (RGB)
    DARK_SQUARE = (181, 136, 99)  # Dark squares - medium brown tone (RGB)

    # ===================
    # Alternative Color Schemes
    # ===================
    # Green theme - inspired by tournament chess boards
    # LIGHT_SQUARE = (238, 238, 210)  # Cream/off-white
    # DARK_SQUARE = (118, 150, 86)    # Forest green

    # Blue theme - modern, cool-toned aesthetic
    # LIGHT_SQUARE = (222, 227, 230)  # Light gray-blue
    # DARK_SQUARE = (140, 162, 173)   # Slate blue

    # ===================
    # Highlight Colors
    # ===================
    # Semi-transparent overlay colors for interactive feedback and game state visualization
    # All use RGBA format with alpha channel for transparency (allows board to show through)

    SELECTED_SQUARE = (186, 202, 68, 180)
    LEGAL_MOVE_DOT = (100, 100, 100, 128)
    CAPTURE_MOVE_CIRCLE = (100, 100, 100, 180)
    LAST_MOVE_FROM = (205, 210, 106, 150)
    LAST_MOVE_TO = (205, 210, 106, 150)
    CHECK_HIGHLIGHT = (235, 97, 80, 180)

    # ===================
    # UI Colors
    # ===================
    # Colors for interface elements surrounding the chess board

    BACKGROUND = (49, 46, 43)
    BORDER = (30, 30, 30)
    COORDINATE_TEXT = (200, 200, 200)

    # ===================
    # Status Colors
    # ===================
    # Colors for indicating whose turn it is to move

    WHITE_TO_MOVE = (255, 255, 255)
    BLACK_TO_MOVE = (50, 50, 50)

    # ===================
    # Menu/Button Colors
    # ===================
    # Interactive button states for menus, controls, and dialogs
    # Provides visual feedback for user interactions

    BUTTON_NORMAL = (80, 80, 80)
    BUTTON_HOVER = (100, 100, 100)
    BUTTON_PRESSED = (60, 60, 60)
    BUTTON_TEXT = (255, 255, 255)

    # ===================
    # Game Result Colors
    # ===================
    # Colors for displaying game outcome

    WIN_COLOR = (76, 175, 80)
    DRAW_COLOR = (255, 193, 7)
    LOSE_COLOR = (244, 67, 54)


# ===================
# Piece Mapping Constants
# ===================
# Dictionaries for translating piece names to file naming conventions

PIECE_COLORS = {"white": "w", "black": "b"}

PIECE_TYPES = {
    "king": "k",
    "queen": "q",
    "rook": "r",
    "bishop": "b",
    "knight": "n",
    "pawn": "p",
}
