"""
Captured Pieces Display
-----------------------
Visual display of captured chess pieces and material advantage.

This module provides a UI component that shows which pieces have been
captured during a chess game. It displays captured pieces for both sides in separate
sections and highlights material advantage with a numerical score.
"""

import pygame
import chess
from typing import List, Tuple
from gui.colors import Colors


class CapturedPiecesDisplay:
    """
    UI component for displaying captured chess pieces and material balance.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        white_x: int,
        white_y: int,
        white_width: int,
        white_height: int,
        black_x: int,
        black_y: int,
        black_width: int,
        black_height: int,
    ):
        """
        Initialize captured pieces display with position and styling.

        Creates the display component ready to show captured pieces.
        Sets up fonts, dimensions, and stores references to screen and piece images.

        Args:
            screen (pygame.Surface): Main pygame display surface.
                Used for rendering captured pieces display.

            white_x (int): X position for white's captured pieces section.
            white_y (int): Y position for white's captured pieces section.
            white_width (int): Width of white's captured pieces section.
            white_height (int): Height of white's captured pieces section.

            black_x (int): X position for black's captured pieces section.
            black_y (int): Y position for black's captured pieces section.
            black_width (int): Width of black's captured pieces section.
            black_height (int): Height of black's captured pieces section.
        """
        # Store display surface reference
        self.screen = screen

        # White's captured pieces section (above board)
        self.white_rect = pygame.Rect(white_x, white_y, white_width, white_height)

        # Black's captured pieces section (below board)
        self.black_rect = pygame.Rect(black_x, black_y, black_width, black_height)

        # Title font for section headers
        self.title_font = pygame.font.SysFont("Arial", 11, bold=True)

        # Score font for material advantage display
        self.score_font = pygame.font.SysFont("Arial", 14, bold=True)

        # Font that supports chess symbols
        self.piece_font = pygame.font.SysFont(
            "Segoe UI Symbol, Arial Unicode MS, DejaVu Sans", 20
        )

        # Size of captured piece icons in pixels
        self.piece_size = 24

        # Padding from edges of each section
        self.padding = 4

    def draw(self, board: chess.Board):
        """
        Render complete captured pieces display with both sections.

        It analyzes the current board state to determine captured pieces,
        calculates material balance, and draws both display sections.

        Args:
            board (chess.Board): Current board state from python-chess.
                Used to determine which pieces have been captured.
                Compared against starting position piece counts.
        """
        # Analyze current board to determine which pieces were captured
        # Returns two lists: pieces each side has lost
        white_captured, black_captured = self._get_captured_pieces(board)

        # Calculate material difference between the two sides
        material_score = self._calculate_material_score(white_captured, black_captured)

        # Draw section for White's losses (pieces Black captured)
        self._draw_section(
            "White Lost",
            white_captured,
            self.white_rect,
            Colors.COORDINATE_TEXT,
            material_score if material_score < 0 else 0,
        )

        # Draw section for Black's losses (pieces White captured)
        self._draw_section(
            "Black Lost",
            black_captured,
            self.black_rect,
            Colors.COORDINATE_TEXT,
            material_score if material_score > 0 else 0,
        )

    def _draw_section(
        self,
        title: str,
        pieces: List[chess.Piece],
        rect: pygame.Rect,
        text_color: Tuple[int, int, int],
        advantage: int,
    ):
        """
        Render one section showing captured pieces for one side.

        Draws a rectangular section containing:
        - Background and border
        - Title text ("White Lost" or "Black Lost")
        - Captured piece icons in rows with wrapping
        - Material advantage score (if applicable)

        Args:
            title (str): Section title text.
                Either "White Lost" or "Black Lost".

            pieces (List[chess.Piece]): Captured pieces to display.
                Already sorted by value (Queen first, Pawn last).
                Empty list if no pieces captured.

            rect (pygame.Rect): Bounding rectangle for this section.
                Defines position and size of the section.

            text_color (Tuple[int, int, int]): RGB color for text.
                Used for title and any labels.

            advantage (int): Material advantage points to display.
                0 = don't show advantage (equal or opponent's advantage)
                Positive = show "+N" in green on right side
                Only shows when this side has the advantage.
        """
        # -------------------- Background and Border --------------------

        # Fill with dark gray background
        pygame.draw.rect(self.screen, (40, 40, 40), rect)

        # Draw border around section
        pygame.draw.rect(self.screen, Colors.BORDER, rect, 1)

        # -------------------- Title Text --------------------

        # Render section title ("White Lost" or "Black Lost")
        title_surface = self.title_font.render(title, True, text_color)

        # Position in top-left with padding
        title_rect = title_surface.get_rect(
            x=rect.x + self.padding, y=rect.y + self.padding
        )

        # Draw title
        self.screen.blit(title_surface, title_rect)

        # -------------------- Captured Piece Icons --------------------

        # Starting position for first piece icon
        piece_x = rect.x + self.padding
        piece_y = rect.y + self.padding + 14

        # Draw each captured piece as small icon
        for piece in pieces:
            # Check if current piece would extend beyond right edge
            if piece_x + self.piece_size > rect.right - self.padding:
                # Not enough horizontal space - wrap to next row
                piece_x = rect.x + self.padding
                piece_y += self.piece_size + 2

            # Check if we're out of vertical space
            if piece_y + self.piece_size > rect.bottom - self.padding:
                break  # Stop drawing if no more room

            # Draw simple piece icon (using Unicode symbols)
            self._draw_piece_icon(piece, piece_x, piece_y)

            piece_x += self.piece_size + 2

        # -------------------- Material Advantage Score --------------------

        # Only draw advantage if this side is ahead (advantage > 0)
        if advantage > 0:
            # Format as "+N" (e.g., "+3", "+8")
            advantage_text = f"+{advantage}"

            # Render in green (WIN_COLOR) to indicate advantage
            advantage_surface = self.score_font.render(
                advantage_text, True, Colors.WIN_COLOR
            )

            # Position in top-right corner with padding
            # Right-aligned so it doesn't overlap with title
            advantage_rect = advantage_surface.get_rect(
                right=rect.right - self.padding,
                y=rect.y + self.padding,
            )

            # Draw advantage score
            self.screen.blit(advantage_surface, advantage_rect)

    def _draw_piece_icon(self, piece: chess.Piece, x: int, y: int):
        """
        Draw a piece using Unicode chess symbols (emoji).

        Args:
            piece (chess.Piece): Piece to render as placeholder.
            x (int): X position
            y (int): Y position
        """
        # Unicode chess piece symbols
        piece_symbols = {
            (chess.PAWN, chess.WHITE): "♙",
            (chess.KNIGHT, chess.WHITE): "♘",
            (chess.BISHOP, chess.WHITE): "♗",
            (chess.ROOK, chess.WHITE): "♖",
            (chess.QUEEN, chess.WHITE): "♕",
            (chess.KING, chess.WHITE): "♔",
            (chess.PAWN, chess.BLACK): "♟",
            (chess.KNIGHT, chess.BLACK): "♞",
            (chess.BISHOP, chess.BLACK): "♝",
            (chess.ROOK, chess.BLACK): "♜",
            (chess.QUEEN, chess.BLACK): "♛",
            (chess.KING, chess.BLACK): "♚",
        }

        # Get the Unicode symbol
        symbol = piece_symbols.get((piece.piece_type, piece.color), "?")

        # Render the symbol
        text_color = (240, 240, 240) if piece.color == chess.WHITE else (100, 100, 100)
        text = self.piece_font.render(symbol, True, text_color)

        # Draw at the specified position
        self.screen.blit(text, (x, y))

    def _get_captured_pieces(
        self, board: chess.Board
    ) -> Tuple[List[chess.Piece], List[chess.Piece]]:
        """
        Analyze board to determine which pieces have been captured.

        Compares current board state to standard starting position to find
        missing pieces.

        Args:
            board (chess.Board): Current board state from python-chess.
                Scanned to count remaining pieces of each type.

        Returns:
            Tuple[List[chess.Piece], List[chess.Piece]]: Captured pieces lists.
                - white_captured: White pieces captured by Black
                - black_captured: Black pieces captured by White
                Both lists sorted by value (Queen first, Pawn last).
        """
        # Define standard starting piece counts
        # King excluded since it can never be captured
        starting_counts = {
            chess.PAWN: 8,
            chess.KNIGHT: 2,
            chess.BISHOP: 2,
            chess.ROOK: 2,
            chess.QUEEN: 1,
        }

        # Initialize counters for pieces currently on board
        white_counts = {piece_type: 0 for piece_type in starting_counts.keys()}
        black_counts = {piece_type: 0 for piece_type in starting_counts.keys()}

        # Scan entire board to count remaining pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                # Increment counter for this piece type and color
                if piece.color == chess.WHITE:
                    white_counts[piece.piece_type] += 1
                else:
                    black_counts[piece.piece_type] += 1

        # Calculate which pieces are missing (captured)
        white_captured = []  # White pieces captured by Black
        black_captured = []  # Black pieces captured by White

        for piece_type, starting_count in starting_counts.items():
            # Calculate how many white pieces of this type are missing
            white_missing = starting_count - white_counts[piece_type]
            for _ in range(white_missing):
                # Create piece object for each missing white piece
                white_captured.append(chess.Piece(piece_type, chess.WHITE))

            # Calculate how many black pieces of this type are missing
            black_missing = starting_count - black_counts[piece_type]
            for _ in range(black_missing):
                # Create piece object for each missing black piece
                black_captured.append(chess.Piece(piece_type, chess.BLACK))

        # Define piece values for sorting
        # Higher value = more important piece = display first
        piece_values = {
            chess.QUEEN: 9,
            chess.ROOK: 5,
            chess.BISHOP: 3,
            chess.KNIGHT: 3,
            chess.PAWN: 1,
        }

        # Sort captured pieces by value (descending)
        white_captured.sort(key=lambda p: piece_values[p.piece_type], reverse=True)
        black_captured.sort(key=lambda p: piece_values[p.piece_type], reverse=True)

        return white_captured, black_captured

    def _calculate_material_score(
        self, white_captured: List[chess.Piece], black_captured: List[chess.Piece]
    ) -> int:
        """
        Calculate material advantage based on captured pieces.

        Uses standard chess piece values to compute net material balance.
        The side that has captured more valuable pieces has a positive advantage.

        Args:
            white_captured (List[chess.Piece]): White pieces that were captured.
                Pieces that Black has taken.

            black_captured (List[chess.Piece]): Black pieces that were captured.
                Pieces that White has taken.

        Returns:
            int: Material score indicating advantage.
                - Positive: White has advantage (captured more value)
                - Negative: Black has advantage (captured more value)
                - Zero: Equal material (no advantage)
        """
        # Standard chess piece values
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }

        # Calculate total value of white pieces that were captured
        white_lost = sum(piece_values[p.piece_type] for p in white_captured)

        # Calculate total value of black pieces that were captured
        black_lost = sum(piece_values[p.piece_type] for p in black_captured)

        # Calculate net material advantage
        # Positive = White ahead, Negative = Black ahead
        return black_lost - white_lost
