"""
Move Animator
-------------
Smooth piece movement animations for better chess game feel.

This module provides a sophisticated animation system for chess piece movements.
Instead of pieces teleporting instantly between squares, they smoothly glide
from source to destination.
"""

import pygame
import chess
from typing import Optional, Tuple
from utils.config import Config


class MoveAnimator:
    """
    Time-based animation system for smooth chess piece movements.

    This class manages the animation of a chess piece moving from one square
    to another. It uses time-based interpolation with ease-out cubic easing
    to create smooth piece movements.
    """

    def __init__(self, board_gui):
        """
        Initialize move animator with configuration settings.

        Loads animation settings from configuration and initializes all state
        variables to their idle values.

        Args:
            board_gui: BoardGUI instance for coordinate conversion and rendering.
                Must provide:
                - _square_to_coords(): Convert square index to (row, col)
                - board_x, board_y: Board position on screen
                - square_size: Size of each square in pixels
                - piece_images: Dictionary mapping piece symbols to images
        """
        # Store reference to board GUI for coordinate conversion
        # and accessing piece images
        self.board_gui = board_gui

        # Load animation settings from configuration
        self.animation_enabled = Config.ANIMATE_MOVES
        self.animation_speed = Config.ANIMATION_SPEED

        # All state variables start in "idle" configuration

        # Animation active flag
        self.is_animating = False

        # Animation timing (milliseconds since pygame initialization)
        self.animation_start_time = 0

        # Piece being animated
        self.animation_piece = None

        self.from_square = None
        self.to_square = None

        self.start_pos = None
        self.end_pos = None

    def start_animation(
        self, piece: chess.Piece, from_square: chess.Square, to_square: chess.Square
    ):
        """
        Begin animating a piece move from source to destination.

        Initializes all animation state and calculates pixel positions for
        the animation path.

        Args:
            piece (chess.Piece): The piece being moved.
                Contains piece type (PAWN, KNIGHT, etc.) and color (WHITE/BLACK).
                Used to look up the correct piece image during rendering.

            from_square (chess.Square): Source square index (0-63).
                The square the piece is moving from.
                Uses python-chess square indexing (0=a1, 63=h8).

            to_square (chess.Square): Destination square index (0-63).
                The square the piece is moving to.
                Uses python-chess square indexing.
        """
        # Early exit if animations are disabled
        if not self.animation_enabled:
            return

        # Activate animation state
        self.is_animating = True

        # Record start time (milliseconds since pygame.init())
        self.animation_start_time = pygame.time.get_ticks()

        # Store animation parameters
        self.animation_piece = piece
        self.from_square = from_square
        self.to_square = to_square

        # Calculate start and end positions in screen pixel coordinates
        self.start_pos = self._square_to_pixel_center(from_square)
        self.end_pos = self._square_to_pixel_center(to_square)

    def _square_to_pixel_center(self, square: chess.Square) -> Tuple[int, int]:
        """
        Convert chess square index to pixel coordinates of square center.

        Uses BoardGUI's coordinate system to find the pixel position of the
        center of a chess square. This is where pieces are centered during
        rendering.

        Args:
            square (chess.Square): Square index in python-chess format (0-63).
                0 = a1 (bottom-left for white)
                63 = h8 (top-right for white)
                Index represents square regardless of board orientation.

        Returns:
            Tuple[int, int]: (x, y) pixel coordinates of square center.
                x: Horizontal position on screen
                y: Vertical position on screen
                Both measured from top-left of screen (0, 0)
        """
        # Convert square index to board coordinates (row, col)
        row, col = self.board_gui._square_to_coords(square)

        # Calculate top-left corner of square in pixels
        x = self.board_gui.board_x + col * self.board_gui.square_size
        y = self.board_gui.board_y + row * self.board_gui.square_size

        # Calculate center point of square
        # Add half the square size to both coordinates
        center_x = x + self.board_gui.square_size // 2
        center_y = y + self.board_gui.square_size // 2

        # Return center coordinates
        return (center_x, center_y)

    def update(self) -> bool:
        """
        Update animation state and check if animation is still in progress.

        Returns:
            bool: Animation status.
                - True: Animation is still in progress (piece is moving)
                - False: Animation is complete or not active
        """
        # Early exit if not currently animating
        if not self.is_animating:
            return False

        # Get current time in milliseconds
        current_time = pygame.time.get_ticks()

        # Calculate how much time has elapsed since animation started
        elapsed = current_time - self.animation_start_time

        # Check if animation duration has been reached or exceeded
        if elapsed >= self.animation_speed:
            # Animation complete - transition to idle state
            self.is_animating = False
            return False

        # Animation still in progress
        return True

    def get_animated_position(self) -> Optional[Tuple[int, int]]:
        """
        Calculate current pixel position of animated piece using easing.

        Uses ease-out cubic easing to create smooth, natural-looking motion.
        The piece starts fast and slows down as it approaches the destination.

        Returns:
            Optional[Tuple[int, int]]: Current position of animated piece.
                - (x, y): Pixel coordinates if animation is active
                - None: If not animating or positions not set
        """
        # Validate animation state and position data
        if not self.is_animating or self.start_pos is None or self.end_pos is None:
            return None

        # Get current time
        current_time = pygame.time.get_ticks()

        # Calculate elapsed time since animation started
        elapsed = current_time - self.animation_start_time

        # Calculate linear progress (0.0 to 1.0)
        progress = min(1.0, elapsed / self.animation_speed)

        # Ease-out cubic easing for smooth deceleration
        eased_progress = 1 - pow(1 - progress, 3)

        # Unpack start and end coordinates
        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos

        # Linear interpolation with eased progress
        current_x = start_x + (end_x - start_x) * eased_progress
        current_y = start_y + (end_y - start_y) * eased_progress

        # Convert to integer pixel coordinates
        # Pygame requires integer positions for rendering
        return (int(current_x), int(current_y))

    def render(self, screen: pygame.Surface):
        """
        Render the animated piece at its current interpolated position.

        Draws the piece image centered on the current animation position.

        Args:
            screen (pygame.Surface): Pygame display surface to render on.
                The piece will be drawn on top of existing content.
        """
        # Validate animation state
        if not self.is_animating or self.animation_piece is None:
            return

        # Get current interpolated position
        pos = self.get_animated_position()
        if pos is None:
            return

        # Get piece image using piece_loader
        image = self.board_gui.piece_loader.get_piece_image(
            self.animation_piece, self.board_gui.square_size
        )

        # Early exit if no image found
        if image is None:
            return

        # Draw centered on current position
        x = pos[0] - image.get_width() // 2
        y = pos[1] - image.get_height() // 2

        # Render the image
        screen.blit(image, (x, y))

    def is_square_being_animated(self, square: chess.Square) -> bool:
        """
        Check if a square is involved in the current animation.

        This checks if the given square is EITHER the source OR destination
        of the current animation. Both squares should be hidden during animation:
        - Source square: piece is moving away, shouldn't be rendered there
        - Destination square: piece hasn't arrived yet, shouldn't be rendered there

        This is used by BoardGUI to skip rendering pieces at both squares during
        animation. Without this check, pieces would appear in multiple places.

        Args:
            square (chess.Square): Square index to check (0-63).

        Returns:
            bool: Animation status for this square.
                - True: Piece from this square is being animated (don't render)
                - False: No animation from this square (render normally)
        """
        # Check if currently animating AND square is either source OR destination
        # Both conditions must be true to skip rendering
        return self.is_animating and (
            square == self.from_square or square == self.to_square
        )

    def cancel(self):
        """
        Cancel current animation and return to idle state immediately.
        """
        # Deactivate animation flag
        self.is_animating = False

        # Clear all animation state variables
        # Return to idle state with None values
        self.animation_piece = None
        self.from_square = None
        self.to_square = None
