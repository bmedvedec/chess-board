"""
Color Constants for Chess GUI
-----------------------------
Defines all color values used in the chess board interface.
"""


class Colors:
    """Color constants for the chess board GUI."""

    # Board square colors
    LIGHT_SQUARE = (240, 217, 181)  # Classic light wood tone
    DARK_SQUARE = (181, 136, 99)  # Classic dark wood tone

    # Alternative color schemes
    # Green theme
    # LIGHT_SQUARE = (238, 238, 210)
    # DARK_SQUARE = (118, 150, 86)

    # Blue theme
    # LIGHT_SQUARE = (222, 227, 230)
    # DARK_SQUARE = (140, 162, 173)

    # Highlight colors
    SELECTED_SQUARE = (186, 202, 68, 180)  # Yellow-green highlight for selected piece
    LEGAL_MOVE_DOT = (100, 100, 100, 128)  # Gray dot for legal move indicators
    CAPTURE_MOVE_CIRCLE = (100, 100, 100, 180)  # Gray hollow circle for capture moves
    LAST_MOVE_FROM = (205, 210, 106, 150)  # Highlight for last move source
    LAST_MOVE_TO = (205, 210, 106, 150)  # Highlight for last move destination
    CHECK_HIGHLIGHT = (235, 97, 80, 180)  # Red highlight for king in check

    # UI colors
    BACKGROUND = (49, 46, 43)  # Dark background around board
    BORDER = (30, 30, 30)  # Board border color
    COORDINATE_TEXT = (200, 200, 200)  # File/rank labels

    # Status colors
    WHITE_TO_MOVE = (255, 255, 255)
    BLACK_TO_MOVE = (50, 50, 50)

    # Menu/button colors
    BUTTON_NORMAL = (80, 80, 80)
    BUTTON_HOVER = (100, 100, 100)
    BUTTON_PRESSED = (60, 60, 60)
    BUTTON_TEXT = (255, 255, 255)

    # Game result colors
    WIN_COLOR = (76, 175, 80)
    DRAW_COLOR = (255, 193, 7)
    LOSE_COLOR = (244, 67, 54)


# Piece color mapping (for loading correct piece images)
PIECE_COLORS = {"white": "w", "black": "b"}

# Piece type mapping
PIECE_TYPES = {
    "king": "k",
    "queen": "q",
    "rook": "r",
    "bishop": "b",
    "knight": "n",
    "pawn": "p",
}
