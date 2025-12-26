"""
Promotion Dialog
----------------
Modal dialog interface for pawn promotion piece selection.

This module implements a graphical dialog that appears when a pawn reaches the
opposite end of the board and must be promoted.
"""

import pygame
import chess
from typing import Optional, Tuple
from gui.colors import Colors


class PromotionDialog:
    """
    Modal dialog for pawn promotion piece selection.

    Displays a centered dialog box with clickable piece options, allowing the
    player to choose which piece to promote a pawn to. Supports both mouse
    clicks and keyboard shortcuts for selection.
    """

    def __init__(self, screen: pygame.Surface, piece_images: dict):
        """
        Initialize the promotion dialog with display surface and piece images.

        Args:
            screen (pygame.Surface): Main pygame display surface
            piece_images (dict): Dictionary mapping piece symbols (e.g., 'Q', 'q')
                to pygame.Surface sprite images
        """
        # Store references to display and piece graphics
        self.screen = screen
        self.piece_images = piece_images

        # Dialog box dimensions and position
        self.dialog_width = 400
        self.dialog_height = 150

        # Center dialog in the window
        self.dialog_x = (screen.get_width() - self.dialog_width) // 2
        self.dialog_y = (screen.get_height() - self.dialog_height) // 2

        # Define available promotion piece options
        # Order is standard: Queen (most common), Rook, Bishop, Knight
        self.pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        self.piece_symbols = ["Q", "R", "B", "N"]

        # Calculate layout for piece buttons
        self.piece_size = 80  # Size of each clickable piece square
        self.piece_spacing = 20  # Gap between adjacent pieces

        # Calculate total width needed for all pieces
        self.total_pieces_width = (
            len(self.pieces) * self.piece_size
            + (len(self.pieces) - 1) * self.piece_spacing
        )

        # Center the piece row within the dialog
        self.pieces_start_x = (
            self.dialog_x + (self.dialog_width - self.total_pieces_width) // 2
        )

        # Position pieces vertically (below title)
        self.pieces_y = self.dialog_y + 50

    def show(self, is_white: bool) -> Optional[int]:
        """
        Display promotion dialog and wait for user to select a piece.

        Creates a modal dialog with a separate event loop that blocks until the
        user makes a selection. The dialog shows four piece options with hover
        effects and supports both mouse and keyboard input.

        Args:
            is_white (bool): True if promoting a white pawn, False for black pawn
                This determines which color pieces to display

        Returns:
            Optional[int]: Selected promotion piece type:
                - chess.QUEEN (5): Queen promotion
                - chess.ROOK (4): Rook promotion
                - chess.BISHOP (3): Bishop promotion
                - chess.KNIGHT (2): Knight promotion
                - None: User closed window (cancellation)
        """
        # Create semi-transparent black overlay to darken the game board
        # This provides visual focus on the dialog
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))

        # Determine piece symbol case based on color
        color_prefix = "P" if is_white else "p"

        # Enter modal dialog event loop
        # This loop runs independently from the main game loop
        # It blocks until the user makes a selection, creating a modal experience
        running = True
        choice = None

        while running:
            # -------------------- Rendering Phase --------------------

            # Draw semi-transparent overlay over the game board
            # This darkens the background and focuses attention on the dialog
            self.screen.blit(overlay, (0, 0))

            # Draw dialog box background with border
            # Creates the main container for the promotion options
            dialog_rect = pygame.Rect(
                self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height
            )
            # Fill dialog background with configured color
            pygame.draw.rect(self.screen, Colors.BACKGROUND, dialog_rect)
            # Add border around dialog (3 pixels wide)
            pygame.draw.rect(self.screen, Colors.BORDER, dialog_rect, 3)

            # Render title text centered at top of dialog
            font = pygame.font.SysFont("Arial", 24, bold=True)
            title_text = font.render(
                "Choose Promotion Piece", True, Colors.COORDINATE_TEXT
            )
            # Center title horizontally
            title_rect = title_text.get_rect(
                centerx=self.dialog_x + self.dialog_width // 2, y=self.dialog_y + 15
            )
            self.screen.blit(title_text, title_rect)

            # -------------------- Draw Piece Selection Buttons --------------------

            # Get current mouse position for hover detection
            mouse_pos = pygame.mouse.get_pos()

            # Store piece rectangles for click detection
            # Each tuple contains (rectangle, piece_type) for event handling
            piece_rects = []

            # Iterate through all four promotion options
            for i, (piece_type, piece_symbol) in enumerate(
                zip(self.pieces, self.piece_symbols)
            ):
                # Calculate position for this piece button
                # Each piece is offset by its index multiplied by (size + spacing)
                x = self.pieces_start_x + i * (self.piece_size + self.piece_spacing)
                y = self.pieces_y

                # Create clickable rectangle for this piece option
                piece_rect = pygame.Rect(x, y, self.piece_size, self.piece_size)
                # Store for click detection later
                piece_rects.append((piece_rect, piece_type))

                # Determine if mouse cursor is currently over this piece
                # Used to provide visual hover feedback
                is_hovering = piece_rect.collidepoint(mouse_pos)

                # Draw button background with hover effect
                # Lighter color when hovering to indicate interactivity
                bg_color = Colors.BUTTON_HOVER if is_hovering else Colors.BUTTON_NORMAL
                pygame.draw.rect(self.screen, bg_color, piece_rect)
                # Add border around button (2 pixels wide)
                pygame.draw.rect(self.screen, Colors.BORDER, piece_rect, 2)

                # Render piece image on button
                # Convert piece symbol to correct case based on color
                # White pieces use uppercase (Q, R, B, N), black uses lowercase (q, r, b, n)
                if is_white:
                    full_symbol = piece_symbol.upper()
                else:
                    full_symbol = piece_symbol.lower()

                # Look up and render the piece sprite
                if full_symbol in self.piece_images:
                    image = self.piece_images[full_symbol]

                    # Scale image to fit within button with 5-pixel padding on each side
                    # This creates a small margin around the piece for visual clarity
                    scaled_image = pygame.transform.smoothscale(
                        image, (self.piece_size - 10, self.piece_size - 10)
                    )

                    # Center the piece image within the button rectangle
                    image_rect = scaled_image.get_rect(center=piece_rect.center)
                    self.screen.blit(scaled_image, image_rect)

            # Update the display to show all rendered elements
            # flip() is used instead of update() to refresh the entire screen
            pygame.display.flip()

            # -------------------- Event Handling --------------------

            # Process all pending events in the queue
            # This loop handles user input (keyboard, mouse, window close)
            for event in pygame.event.get():
                # Handle window close button (X button)
                if event.type == pygame.QUIT:
                    # Return None to signal cancellation
                    return None

                # Handle keyboard input
                elif event.type == pygame.KEYDOWN:
                    # ESC key - quick exit with Queen as default
                    # This is the most common promotion choice
                    if event.key == pygame.K_ESCAPE:
                        return chess.QUEEN

                    # Keyboard shortcuts for quick piece selection
                    # Maps Q/R/B/N keys to their corresponding piece types
                    key_map = {
                        pygame.K_q: chess.QUEEN,  # Q = Queen
                        pygame.K_r: chess.ROOK,  # R = Rook
                        pygame.K_b: chess.BISHOP,  # B = Bishop
                        pygame.K_n: chess.KNIGHT,  # N = Knight
                    }
                    # Check if a valid shortcut key was pressed
                    if event.key in key_map:
                        return key_map[event.key]

                # Handle mouse clicks
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button only
                        # Check if click was on any of the piece buttons
                        # Iterate through all piece rectangles
                        for rect, piece_type in piece_rects:
                            # Test if click position is inside this rectangle
                            if rect.collidepoint(event.pos):
                                # Valid selection - return chosen piece type
                                return piece_type

        # Fallback return - should never be reached in normal operation
        # This ensures a valid piece type is always returned
        return chess.QUEEN

    def show_promotion_choice_simple(self, is_white: bool) -> int:
        """
        Show promotion dialog with guaranteed non-None return value.

        This is a convenience wrapper around show() that ensures a valid piece
        type is always returned. If the user closes the dialog window (which
        would normally return None), this method defaults to Queen promotion.

        Args:
            is_white (bool): True if promoting a white pawn, False for black pawn

        Returns:
            int: Selected promotion piece type (guaranteed non-None):
                - chess.QUEEN (5): Queen promotion (default if cancelled)
                - chess.ROOK (4): Rook promotion
                - chess.BISHOP (3): Bishop promotion
                - chess.KNIGHT (2): Knight promotion
        """
        # Call main show() method and use or operator to default to Queen
        # If show() returns None (window closed), the or operator evaluates to chess.QUEEN
        # This ensures we always return a valid piece type integer
        return self.show(is_white) or chess.QUEEN
