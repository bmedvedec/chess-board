"""
Responsive Layout Handler
-------------------------
This module manages dynamic window resizing and component layout positioning
for the chess application. It ensures a responsive user interface that adapts
to different window sizes while maintaining proper proportions and visual hierarchy.
"""

from utils.config import Config


class LayoutHandler:
    """
    Manages responsive layout and dynamic window resizing for the chess application.

    This class handles all aspects of window size changes, ensuring that the chess
    board, side panels, and other UI components maintain proper proportions and
    positioning. The layout automatically adapts to different window sizes while
    preserving visual hierarchy and usability.
    """

    def __init__(self):
        """
        Initialize the layout handler with default configuration values.

        Stores original dimensions from Config to enable reset functionality
        and establishes minimum size constraints for the window.
        """
        # Store original dimensions from Config
        # These values serve as a baseline for reset functionality
        self.original_board_size = Config.BOARD_SIZE
        self.original_window_width = Config.WINDOW_WIDTH
        self.original_window_height = Config.WINDOW_HEIGHT
        self.panel_width = Config.SIDE_PANEL_WIDTH
        self.panel_margin = Config.SIDE_PANEL_MARGIN

        # Minimum sizes to prevent unusable UI
        self.min_window_width = 800
        self.min_window_height = 700

    def handle_resize(self, new_width: int, new_height: int) -> bool:
        """
        Handle window resize event and update all component positions.

        This method is the core of the layout system. It calculates new dimensions
        and positions for all UI components based on the new window size, ensuring
        proper scaling, centering, and spacing.

        Args:
            new_width: int
                Requested new window width in pixels
            new_height: int
                Requested new window height in pixels

        Returns:
            bool:
                Always returns True to indicate layout was updated successfully
        """
        # Enforce minimum size to prevent unusable UI
        new_width = max(self.min_window_width, new_width)
        new_height = max(self.min_window_height, new_height)

        # Calculate available space for board (accounting for panels and margins)
        fixed_margin = 40

        available_width = new_width - self.panel_width - fixed_margin - 80

        available_height = new_height - 160  # Top and bottom margins

        # Board should fit in both dimensions and stay square
        # Use the limiting dimension (smaller of width/height)
        max_board_size = min(available_width, available_height)

        # Keep board size divisible by 8 (for square rendering)
        # Each chess square needs to be an integer pixel size
        # Board has 8x8 squares, so total size must be 8*n
        new_board_size = (max_board_size // 8) * 8

        # Clamp board size to acceptable range
        new_board_size = max(320, min(960, new_board_size))

        # Update Config with new board size
        setattr(Config, "BOARD_SIZE", new_board_size)

        # Calculate centered board position
        total_layout_width = new_board_size + fixed_margin + self.panel_width
        layout_start_x = (new_width - total_layout_width) // 2

        # Apply minimum left margin to prevent board touching left edge
        board_x = max(20, layout_start_x)

        # Center vertically with minimum top margin
        board_y = (new_height - new_board_size) // 2

        # Update Config with board position
        setattr(Config, "BOARD_X", max(20, board_x))
        setattr(Config, "BOARD_Y", max(70, board_y))

        # Update panel positions (fixed distance from board)
        # All panels share the same x-coordinate (aligned vertically)
        panel_x = board_x + new_board_size + fixed_margin

        # Move history (full board height)
        setattr(Config, "MOVE_HISTORY_X", panel_x)
        setattr(Config, "MOVE_HISTORY_Y", Config.BOARD_Y)
        setattr(Config, "MOVE_HISTORY_WIDTH", self.panel_width)
        setattr(Config, "MOVE_HISTORY_HEIGHT", new_board_size)

        # Game controls (top-right)
        setattr(Config, "GAME_CONTROLS_X", panel_x)
        setattr(Config, "GAME_CONTROLS_Y", 10)
        setattr(Config, "GAME_CONTROLS_WIDTH", self.panel_width)

        # Calculate widths for captured pieces and clocks
        captured_width = int(new_board_size * 0.7)
        clock_width = new_board_size - captured_width - 10

        # Captured pieces - white (above board, left side)
        setattr(Config, "CAPTURED_PIECES_WHITE_X", Config.BOARD_X)
        setattr(Config, "CAPTURED_PIECES_WHITE_Y", Config.BOARD_Y - 60)
        setattr(Config, "CAPTURED_PIECES_WHITE_WIDTH", captured_width)
        setattr(Config, "CAPTURED_PIECES_WHITE_HEIGHT", 50)

        # White's clock (below board, right side)
        setattr(Config, "WHITE_CLOCK_X", Config.BOARD_X + captured_width + 10)
        setattr(Config, "WHITE_CLOCK_Y", Config.BOARD_Y + new_board_size + 10)
        setattr(Config, "WHITE_CLOCK_WIDTH", clock_width)
        setattr(Config, "WHITE_CLOCK_HEIGHT", 50)

        # Captured pieces - black (below board, left side)
        setattr(Config, "CAPTURED_PIECES_BLACK_X", Config.BOARD_X)
        setattr(Config, "CAPTURED_PIECES_BLACK_Y", Config.BOARD_Y + new_board_size + 10)
        setattr(Config, "CAPTURED_PIECES_BLACK_WIDTH", captured_width)
        setattr(Config, "CAPTURED_PIECES_BLACK_HEIGHT", 50)

        # Black's clock (above board, right side)
        setattr(Config, "BLACK_CLOCK_X", Config.BOARD_X + captured_width + 10)
        setattr(Config, "BLACK_CLOCK_Y", Config.BOARD_Y - 60)
        setattr(Config, "BLACK_CLOCK_WIDTH", clock_width)
        setattr(Config, "BLACK_CLOCK_HEIGHT", 50)

        return True

    def reset_to_default(self):
        """
        Reset layout to original dimensions from initialization.
        """
        # Restore original board size
        setattr(Config, "BOARD_SIZE", self.original_board_size)

        # Recalculate layout using original window dimensions
        # This updates all panel positions and spacing
        self.handle_resize(self.original_window_width, self.original_window_height)
