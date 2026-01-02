"""
Chess Board GUI Renderer
------------------------
Comprehensive visual rendering system for the chess board interface.

This module handles all graphical rendering aspects of the chess application,
including board squares, piece images, coordinate labels, highlights, and
move indicators.
"""

import pygame
import chess
from typing import Optional, Tuple
from pathlib import Path

from gui.colors import Colors, PIECE_COLORS, PIECE_TYPES
from utils.config import Config


class BoardGUI:
    """
    Chess board graphical user interface renderer.

    The class maintains piece images, calculates board positioning, and provides
    methods for drawing various game elements with proper scaling and alignment.

    Attributes:
        screen (pygame.Surface): The display surface to render onto
        square_size (int): Pixel size of each board square
        board_x (int): X-coordinate of board's top-left corner
        board_y (int): Y-coordinate of board's top-left corner
        piece_images (dict): Cached piece sprite images keyed by symbol
        coord_font (pygame.font.Font): Font for coordinate labels
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the board GUI renderer with display surface and resources.

        Args:
            screen (pygame.Surface): The main pygame display surface to render onto
        """
        self.screen = screen

        # Calculate individual square size (board divided into 8x8 grid)
        self.square_size = Config.BOARD_SIZE // 8

        # Determine board position on screen
        if hasattr(Config, "BOARD_X") and hasattr(Config, "BOARD_Y"):
            # Use explicit positions from config
            self.board_x = Config.BOARD_X
            self.board_y = Config.BOARD_Y
        else:
            # Fallback: center the board (backward compatibility)
            self.board_x = (Config.WINDOW_WIDTH - Config.BOARD_SIZE) // 2
            self.board_y = (Config.WINDOW_HEIGHT - Config.BOARD_SIZE) // 2

        # Load and cache all piece sprite images
        # Images are loaded once during initialization for performance
        self.piece_images = self._load_piece_images()

        # Initialize font system for rendering coordinate labels
        pygame.font.init()
        self.coord_font = pygame.font.SysFont("Arial", 16)

        # Log successful initialization with diagnostic information
        print("[BoardGUI] Initialized successfully")
        print(f"    Square size: {self.square_size}x{self.square_size}")
        print(f"    Board position: ({self.board_x}, {self.board_y})")
        print(f"    Piece images loaded: {len(self.piece_images)} pieces")

    def _load_piece_images(self) -> dict:
        """
        Load and scale chess piece images from the assets directory.

        Returns:
            dict: Dictionary mapping piece symbols to pygame.Surface objects
                Keys follow python-chess convention:
                - Uppercase for white pieces: 'P', 'N', 'B', 'R', 'Q', 'K'
                - Lowercase for black pieces: 'p', 'n', 'b', 'r', 'q', 'k'
        """
        images = {}

        # Define all 12 piece symbols following python-chess FEN notation
        # Uppercase letters represent white pieces, lowercase represent black
        piece_symbols = {
            "P": ("white", "pawn"),
            "N": ("white", "knight"),
            "B": ("white", "bishop"),
            "R": ("white", "rook"),
            "Q": ("white", "queen"),
            "K": ("white", "king"),
            "p": ("black", "pawn"),
            "n": ("black", "knight"),
            "b": ("black", "bishop"),
            "r": ("black", "rook"),
            "q": ("black", "queen"),
            "k": ("black", "king"),
        }

        # Get path to assets directory from configuration
        assets_path = Path(Config.PIECE_IMAGES_DIR)

        if assets_path.exists():
            # Assets directory found - attempt to load each piece
            for symbol, (color, piece_type) in piece_symbols.items():
                # Try multiple file naming conventions for maximum compatibility
                # Different chess piece sets use different naming schemes
                possible_names = [
                    f"{color}_{piece_type}.png",  # e.g., "white_pawn.png"
                    f"{color[0]}{piece_type[0]}.png",  # e.g., "wp.png"
                    f"{PIECE_COLORS[color]}{PIECE_TYPES[piece_type]}.png",  # e.g., "wP.png"
                ]

                loaded = False
                for filename in possible_names:
                    image_path = assets_path / filename
                    if image_path.exists():
                        try:
                            # Load the image file
                            image = pygame.image.load(str(image_path))

                            # Scale image to fit within square with 15% padding
                            # This ensures pieces don't touch square edges
                            size = int(self.square_size * 0.85)
                            image = pygame.transform.scale(image, (size, size))

                            images[symbol] = image
                            loaded = True
                            break
                        except pygame.error as e:
                            print(f"[Warning] Failed to load {image_path}: {e}")

                # If no image file worked, create a placeholder
                if not loaded:
                    images[symbol] = self._create_placeholder_piece(symbol)
        else:
            # Assets directory doesn't exist - use placeholders for all pieces
            print(f"[Warning] Assets directory not found: {assets_path}")
            print("[Info] Using placeholder pieces (colored circles)")
            for symbol in piece_symbols.keys():
                images[symbol] = self._create_placeholder_piece(symbol)

        return images

    def _create_placeholder_piece(self, symbol: str) -> pygame.Surface:
        """
        Generate a placeholder graphic for a chess piece.

        Args:
            symbol (str): Piece symbol following FEN notation
                Uppercase for white (P, N, B, R, Q, K)
                Lowercase for black (p, n, b, r, q, k)

        Returns:
            pygame.Surface: Transparent surface containing the placeholder graphic
        """
        # Calculate size to match loaded images (85% of square)
        size = int(self.square_size * 0.85)

        # Create transparent surface for the piece
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Determine colors based on piece color (uppercase = white)
        is_white = symbol.isupper()
        circle_color = (240, 240, 240) if is_white else (50, 50, 50)
        border_color = (50, 50, 50) if is_white else (240, 240, 240)

        # Draw filled circle for the piece body
        center = size // 2
        pygame.draw.circle(surface, circle_color, (center, center), center - 2)

        # Draw circle outline for definition
        pygame.draw.circle(surface, border_color, (center, center), center - 2, 2)

        # Render piece letter (uppercase) centered in the circle
        font = pygame.font.SysFont("Arial", size // 2, bold=True)
        text = font.render(symbol.upper(), True, border_color)
        text_rect = text.get_rect(center=(center, center))
        surface.blit(text, text_rect)

        return surface

    def draw_board(self):
        """
        Render the complete chess board with squares, border, and coordinates.
        """
        # Fill entire screen with background color
        # This creates the margin area around the board
        self.screen.fill(Colors.BACKGROUND)

        # Draw decorative border around the chess board
        # Border is 2 pixels thick and surrounds the board area
        border_rect = pygame.Rect(
            self.board_x - 2,
            self.board_y - 2,
            Config.BOARD_SIZE + 4,
            Config.BOARD_SIZE + 4,
        )
        pygame.draw.rect(self.screen, Colors.BORDER, border_rect, 2)

        # Render all 64 squares in the 8x8 grid
        for row in range(8):
            for col in range(8):
                self._draw_square(row, col)

        # Add algebraic notation labels around the board if enabled
        if Config.SHOW_COORDINATES:
            self._draw_coordinates()

    def _draw_square(self, row: int, col: int):
        """
        Render a single chess board square with appropriate color.

        Draws one square of the chess board using alternating light and dark
        colors to create the classic checkerboard pattern.

        Args:
            row (int): Row index 0-7, where:
                - 0 corresponds to rank 8 (top of board from white's perspective)
                - 7 corresponds to rank 1 (bottom of board)
            col (int): Column index 0-7, where:
                - 0 corresponds to file 'a' (left side)
                - 7 corresponds to file 'h' (right side)

        Color Pattern:
            - Light squares: (row + col) is even
            - Dark squares: (row + col) is odd
        """
        # Calculate pixel position of this square's top-left corner
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size

        # Determine square color using checkerboard pattern
        # When row + col is even, the square is light
        is_light = (row + col) % 2 == 0
        color = Colors.LIGHT_SQUARE if is_light else Colors.DARK_SQUARE

        # Render the filled rectangle for this square
        pygame.draw.rect(self.screen, color, (x, y, self.square_size, self.square_size))

    def _draw_coordinates(self):
        """
        Render algebraic notation coordinate labels around the chess board.

        Draws file letters (a-h) along the top and bottom edges, and rank
        numbers (1-8) along the left and right edges.
        """
        # File letters from left to right (a through h)
        files = "abcdefgh"
        # Rank numbers from top to bottom (8 down to 1)
        ranks = "87654321"

        # Draw file labels (a-h) along horizontal edges
        for col, file in enumerate(files):
            # Center label horizontally within each square
            x = self.board_x + col * self.square_size + self.square_size // 2
            y_bottom = self.board_y + Config.BOARD_SIZE + 8  # Below board
            y_top = self.board_y - 20  # Above board

            # Render and position the file letter
            text = self.coord_font.render(file, True, Colors.COORDINATE_TEXT)
            text_rect = text.get_rect(center=(x, y_bottom))
            self.screen.blit(text, text_rect)

            text_rect = text.get_rect(center=(x, y_top))
            self.screen.blit(text, text_rect)

        # Draw rank labels (1-8) along vertical edges
        for row, rank in enumerate(ranks):
            # Center label vertically within each square
            y = self.board_y + row * self.square_size + self.square_size // 2
            x_left = self.board_x - 20  # Left of board
            x_right = self.board_x + Config.BOARD_SIZE + 20  # Right of board

            # Render and position the rank number
            text = self.coord_font.render(rank, True, Colors.COORDINATE_TEXT)
            text_rect = text.get_rect(center=(x_left, y))
            self.screen.blit(text, text_rect)

            text_rect = text.get_rect(center=(x_right, y))
            self.screen.blit(text, text_rect)

    def draw_pieces(self, board: chess.Board):
        """
        Render all chess pieces on the board according to current position.

        Iterates through all 64 squares and draws any pieces present at those
        locations.

        Args:
            board (chess.Board): python-chess Board object containing the current
                game position with piece placement information
        """
        # Iterate through all 64 squares (0 = a1, 63 = h8)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # Square is occupied - draw the piece
                self._draw_piece(piece, square)

    def _draw_piece(self, piece: chess.Piece, square: chess.Square):
        """
        Render a single chess piece at its specified square.

        Args:
            piece (chess.Piece): python-chess Piece object with color and type info
            square (chess.Square): Target square index (0-63) where piece should be drawn
        """
        # Convert chess square index to screen coordinates (row, col)
        row, col = self._square_to_coords(square)

        # Get the cached sprite image for this piece type
        symbol = piece.symbol()
        if symbol not in self.piece_images:
            print(f"[Warning] No image for piece: {symbol}")
            return

        image = self.piece_images[symbol]

        # Calculate pixel position of the square's top-left corner
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size

        # Center the piece image within the square
        # Images are smaller than squares to provide visual padding
        piece_x = x + (self.square_size - image.get_width()) // 2
        piece_y = y + (self.square_size - image.get_height()) // 2

        # Draw the piece sprite to the screen
        self.screen.blit(image, (piece_x, piece_y))

    def _square_to_coords(self, square: chess.Square) -> Tuple[int, int]:
        """
        Convert chess square index to display coordinates (row, col).

        Transforms a square index from python-chess notation (0-63) into
        screen coordinates suitable for rendering. Handles board flipping
        when playing as black.

        Args:
            square (chess.Square): Square index where:
                - 0 = a1, 7 = h1, 56 = a8, 63 = h8
                - Uses python-chess's standard square indexing

        Returns:
            Tuple[int, int]: (row, col) tuple where:
                - row: 0-7, with 0 = rank 8 (top), 7 = rank 1 (bottom)
                - col: 0-7, with 0 = file a (left), 7 = file h (right)
        """
        # Extract file and rank from square index
        file = chess.square_file(square)  # 0-7 representing files a-h
        rank = chess.square_rank(square)  # 0-7 representing ranks 1-8

        # Convert to display coordinates (top-left origin)
        # Rank 8 should be at the top (row 0), so we invert the rank
        row = 7 - rank
        col = file

        # Handle board flipping for playing as black
        if Config.FLIP_BOARD:
            row = 7 - row
            col = 7 - col

        return row, col

    def coords_to_square(self, x: int, y: int) -> Optional[chess.Square]:
        """
        Convert screen pixel coordinates to chess square index.

        Takes mouse click coordinates and determines which chess square was
        clicked. Returns None if the click was outside the board area.

        Args:
            x (int): Screen x coordinate in pixels
            y (int): Screen y coordinate in pixels

        Returns:
            Optional[chess.Square]: Square index (0-63), or None if coordinates
                are outside the board boundaries
        """
        # Check if click is within horizontal board bounds
        if x < self.board_x or x >= self.board_x + Config.BOARD_SIZE:
            return None
        # Check if click is within vertical board bounds
        if y < self.board_y or y >= self.board_y + Config.BOARD_SIZE:
            return None

        # Calculate which column and row were clicked
        # Subtract board offset and divide by square size
        col = (x - self.board_x) // self.square_size
        row = (y - self.board_y) // self.square_size

        # Clamp values to valid range
        # Handles edge cases near board boundaries
        col = max(0, min(7, col))
        row = max(0, min(7, row))

        # Convert display coordinates to chess notation
        # Row 0 is rank 8, so invert to get proper rank
        rank = 7 - row
        file = col

        # Handle board flipping
        if Config.FLIP_BOARD:
            rank = 7 - rank
            file = 7 - file

        # Convert file and rank to square index
        return chess.square(file, rank)

    def highlight_square(self, square: chess.Square, color: Tuple[int, int, int, int]):
        """
        Draw a semi-transparent colored overlay on a chess square.

        Used for visual feedback such as:
            - Selected piece highlighting
            - Last move indication
            - King in check warning
            - Square hover effects

        Args:
            square (chess.Square): Square index (0-63) to highlight
            color (Tuple[int, int, int, int]): RGBA color tuple where:
                - RGB values: 0-255
                - Alpha value: 0 (transparent) to 255 (opaque)
        """
        # Convert square index to display coordinates
        row, col = self._square_to_coords(square)

        # Calculate pixel position of the square
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size

        # Create transparent surface for the overlay
        # SRCALPHA flag enables per-pixel alpha transparency
        overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        overlay.fill(color)

        # Blit the overlay onto the screen at the square position
        self.screen.blit(overlay, (x, y))

    def draw_legal_move_indicators(self, legal_moves: list, board: chess.Board):
        """
        Draw visual indicators showing where a selected piece can move.

        Displays small circular dots on destination squares to show the player
        which moves are legal for the currently selected piece.

        Args:
            legal_moves (list): List of chess.Move objects representing valid moves
            board (chess.Board): Current board state for capture detection
        """
        for move in legal_moves:
            # Get destination square of this move
            to_square = move.to_square
            row, col = self._square_to_coords(to_square)

            # Check if this move is a capture
            is_capture = board.piece_at(to_square) is not None or board.is_en_passant(
                move
            )

            # Create transparent surface for the indicator dot
            surface = pygame.Surface(
                (self.square_size, self.square_size), pygame.SRCALPHA
            )
            center = (self.square_size // 2, self.square_size // 2)

            if is_capture:
                # Draw hollow circle for captures (larger, around the piece)
                radius = int(self.square_size * 0.42)
                pygame.draw.circle(
                    surface,
                    Colors.CAPTURE_MOVE_CIRCLE,
                    center,
                    radius,
                    4,
                )
            else:
                # Draw solid dot for non-captures
                radius = self.square_size // 8
                pygame.draw.circle(
                    surface,
                    Colors.LEGAL_MOVE_DOT,
                    center,
                    radius,
                )

            # Blit the indicator onto the screen at the square position
            self.screen.blit(
                surface,
                (
                    self.board_x + col * self.square_size,
                    self.board_y + row * self.square_size,
                ),
            )

    def draw_check_indicator(self, board: chess.Board):
        """
        Draw a red highlight around the king if in check.

        Args:
            board: Current board state
        """
        if not board.is_check():
            return

        # Find the king of the current player (who is in check)
        king_square = board.king(board.turn)
        if king_square is None:
            return

        row, col = self._square_to_coords(king_square)
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size

        # Draw pulsing red glow effect
        surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)

        # Draw multiple layers for glow effect
        for i in range(3):
            alpha = 180 - (i * 40)
            color = (235, 97, 80, alpha)
            pygame.draw.rect(
                surface,
                color,
                (i * 2, i * 2, self.square_size - i * 4, self.square_size - i * 4),
                3,
            )

        self.screen.blit(surface, (x, y))

    def draw_last_move_highlight(self, board: chess.Board):
        """
        Draw highlight for the last move made.
        Shows both source and destination squares.

        Args:
            board: Current board state
        """
        if not board.move_stack:
            return

        last_move = board.peek()

        # Highlight source square
        self.highlight_square(last_move.from_square, Colors.LAST_MOVE_FROM)

        # Highlight destination square
        self.highlight_square(last_move.to_square, Colors.LAST_MOVE_TO)

    def draw_game_info(self, board: chess.Board):
        """
        Render game status information above the chess board.

        Displays whose turn it is to move with appropriate color coding.
        This provides at-a-glance game state awareness for the player.

        Args:
            board (chess.Board): Current board state from python-chess
        """
        # Determine turn text based on current player
        turn_text = "White to move" if board.turn == chess.WHITE else "Black to move"

        # Create bold font for visibility
        font = pygame.font.SysFont("Arial", 24, bold=True)

        # Use different colors to distinguish whose turn it is
        color = (
            Colors.WHITE_TO_MOVE if board.turn == chess.WHITE else Colors.BLACK_TO_MOVE
        )

        # Render the text with appropriate color
        text_surface = font.render(turn_text, True, color)

        # Center text over the board (not the window)
        board_center_x = self.board_x + self.square_size * 4  # Center of 8 squares
        text_rect = text_surface.get_rect(centerx=board_center_x, y=self.board_y - 40)

        # Draw the text to the screen
        self.screen.blit(text_surface, text_rect)
