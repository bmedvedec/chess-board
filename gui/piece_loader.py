"""
Piece Loader Module
--------------------
Manages loading, caching, and rendering of chess piece images from PNG files.
Provides efficient image scaling, caching strategies, and integration with the
python-chess library for seamless piece rendering on the chess board.
"""

import pygame
import chess
import utils.resource_loader as resource_loader


class PieceLoader:
    """
    Chess piece image loader with caching and scaling support.

    Manages the loading of chess piece PNG images from disk, scales them to
    match the current board square size, and caches the results for efficient
    rendering. Supports dynamic board resizing and provides simple API for
    piece rendering.
    """

    def __init__(self, piece_dir="assets/pieces"):
        """
        Initialize the piece loader with asset directory path.

        Sets up the piece loader with the specified directory for PNG images
        and initializes the caching system. No images are loaded at this stage
        (lazy loading pattern).

        Args:
            piece_dir: str, optional
                Path to directory containing piece PNG images
                Default: "assets/pieces"
                Expected files: white_pawn.png, black_knight.png, etc.
        """
        # Store asset directory path
        self.piece_dir = piece_dir

        # Initialize empty cache for scaled images
        self.cache = {}

        # Symbol to Filename Mapping

        # Maps chess.Piece.symbol() output to PNG filenames
        # Uppercase = white pieces, lowercase = black pieces
        self.symbol_to_name = {
            # White pieces (uppercase symbols)
            "P": "white_pawn",
            "N": "white_knight",
            "B": "white_bishop",
            "R": "white_rook",
            "Q": "white_queen",
            "K": "white_king",
            # Black pieces (lowercase symbols)
            "p": "black_pawn",
            "n": "black_knight",
            "b": "black_bishop",
            "r": "black_rook",
            "q": "black_queen",
            "k": "black_king",
        }

    def load_pieces(self, square_size):
        """
        Load and cache all 12 piece images at the specified square size.

        Loads PNG images from disk, scales them to match the board square size
        (80% of square for padding), and stores them in the cache. If images
        are already cached at this size, returns immediately (idempotent).

        Args:
            square_size: int
                Size of chess board squares in pixels
                Pieces will be scaled to square_size × 0.8
        """
        # Calculate Piece Size
        piece_size = int(square_size * 0.8)

        # Create cache key for this specific size
        cache_key = f"size_{square_size}"

        # Check Cache
        # If already loaded at this size, nothing to do
        if cache_key in self.cache:
            return

        # Initialize Cache Entry

        # Create empty dictionary to store all 12 piece images at this size
        self.cache[cache_key] = {}

        # Load All Pieces
        # Iterate through all 12 chess pieces (6 white + 6 black)
        for symbol, name in self.symbol_to_name.items():
            try:
                # Construct full path to PNG file
                # path = f"{self.piece_dir}/{name}.png"
                path = resource_loader.resource_path(f"{self.piece_dir}\\{name}.png")

                # Load PNG image from disk
                original = pygame.image.load(path).convert_alpha()

                # Scale image to calculated piece size
                scaled = pygame.transform.smoothscale(
                    original, (piece_size, piece_size)
                )

                # Store scaled image in cache
                self.cache[cache_key][symbol] = scaled

            except pygame.error as e:
                # Handle missing or invalid image files
                print(f"Error loading {name}: {e}")

                # Create colored placeholder surface
                # Red for white pieces, blue for black pieces
                placeholder = pygame.Surface((piece_size, piece_size))
                placeholder.fill((255, 0, 0) if symbol.isupper() else (0, 0, 255))

                # Store placeholder in cache (game continues with colored squares)
                self.cache[cache_key][symbol] = placeholder

    def get_piece_image(self, piece, square_size):
        """
        Retrieve cached image for a chess piece at the specified size.

        Looks up the scaled piece image from the cache. If the requested size
        hasn't been loaded yet, automatically calls load_pieces() first. Accepts
        both chess.Piece objects and raw symbol strings.

        Args:
            piece: chess.Piece or str
                Either a chess.Piece object from python-chess library,
                or a symbol string ('P', 'n', 'K', etc.)
            square_size: int
                Size of chess board squares in pixels
                Must match the size used when rendering the board

        Returns:
            pygame.Surface or None
                The scaled piece image surface if found
                None if the symbol is not recognized
        """
        # Create cache key for this size
        cache_key = f"size_{square_size}"

        # Ensure pieces are loaded at this size
        # If not cached, load_pieces() will load and cache them
        # If already cached, load_pieces() returns immediately (no-op)
        if cache_key not in self.cache:
            self.load_pieces(square_size)

        # Extract Symbol
        if isinstance(piece, chess.Piece):
            # chess.Piece object: extract symbol ('P', 'n', etc.)
            symbol = piece.symbol()
        else:
            # Already a symbol string, use directly
            symbol = piece

        # Retrieve from Cache
        return self.cache[cache_key].get(symbol)

    def draw_piece(self, screen, piece, x, y, square_size):
        """
        Draw a chess piece centered within a square.

        Args:
            screen: pygame.Surface
                The pygame surface to draw on (typically the main screen)
            piece: chess.Piece or str
                Either a chess.Piece object or a symbol string ('P', 'n', etc.)
            x: int
                X coordinate of the top-left corner of the square
            y: int
                Y coordinate of the top-left corner of the square
            square_size: int
                Size of the chess board squares in pixels
        """
        # Retrieve Piece Image
        image = self.get_piece_image(piece, square_size)

        # Draw if Valid
        if image:
            # Calculate piece size (80% of square)
            piece_size = int(square_size * 0.8)

            # Calculate offset to center piece in square
            offset = (square_size - piece_size) // 2

            # Draw piece centered in square
            screen.blit(image, (x + offset, y + offset))
