"""
Game Result Dialog
------------------
Modal dialog system for displaying chess game end conditions and results.

This module provides a polished, user-friendly interface for announcing game
outcomes and offering post-game options. It creates a modal overlay that pauses
the game and presents the result with appropriate messaging and visual styling.

Supported Result Types:
    1. Checkmate:
       - Announces winner (White or Black)
       - Victory message with color coding
       - Win color border (gold/yellow)

    2. Stalemate:
       - Draw announcement
       - Explanation of stalemate condition
       - Draw color border (gray)

    3. Draw (various causes):
       - Generic draw announcement
       - Customizable reason (50-move rule, threefold repetition, etc.)
       - Draw color border

    4. Resignation:
       - Winner announcement
       - Victory by resignation message
       - Win color border
"""

import pygame
from typing import Optional
from gui.colors import Colors


class GameResultDialog:
    """
    Modal dialog for displaying chess game end results and offering post-game choices.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the game result dialog with layout and styling.

        Args:
            screen (pygame.Surface): The main game display surface.
                Must be initialized pygame surface. Dialog will be centered on it.
        """
        # Store reference to main screen for rendering
        self.screen = screen

        # Set dialog size
        self.dialog_width = 500
        self.dialog_height = 250

        # Calculate dialog position to center it on the screen
        self.dialog_x = (screen.get_width() - self.dialog_width) // 2
        self.dialog_y = (screen.get_height() - self.dialog_height) // 2

        # Create fonts for different text elements
        # SysFont uses system fonts for consistent appearance across platforms

        # Title font
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)

        # Message font
        self.message_font = pygame.font.SysFont("Arial", 20)

        # Button font
        self.button_font = pygame.font.SysFont("Arial", 18, bold=True)

        # Define button sizes
        self.button_width = 150
        self.button_height = 50
        self.button_spacing = 20

        # Calculate horizontal positioning to center both buttons as a group
        total_buttons_width = 2 * self.button_width + self.button_spacing

        # Calculate starting X position to center the button group within dialog
        buttons_start_x = self.dialog_x + (self.dialog_width - total_buttons_width) // 2

        # Create "New Game" button rectangle (left button)
        self.new_game_button = pygame.Rect(
            buttons_start_x,
            self.dialog_y + self.dialog_height - 70,
            self.button_width,
            self.button_height,
        )

        # Create "Close" button rectangle (right button)
        self.close_button = pygame.Rect(
            buttons_start_x + self.button_width + self.button_spacing,
            self.dialog_y + self.dialog_height - 70,
            self.button_width,
            self.button_height,
        )

    def show(
        self, result_type: str, winner: Optional[str] = None, reason: str = ""
    ) -> str:
        """
        Display game result dialog and block until user makes a choice (modal).

        This method creates a modal overlay, displays the game result with appropriate
        styling and messaging, then enters an independent event loop that blocks until
        the user selects an action. The main game loop is paused during this time.

        Args:
            result_type (str): The type of game ending that occurred.
                - "checkmate": Game ended by checkmate (requires winner)
                - "stalemate": Game ended by stalemate (draw)
                - "draw": Game ended by other draw condition (use reason param)
                - "resignation": Game ended by resignation (requires winner)

            winner (Optional[str], optional): The winning player's color.
                - "White": White player won
                - "Black": Black player won
                - None: No winner (draw/stalemate)
                Required for "checkmate" and "resignation" types.
                Defaults to None.

            reason (str, optional): Additional context about the result.
                Only displayed for "draw" type results.
                Defaults to "" (no additional context).

        Returns:
            str: The user's choice for what to do next.
                - "new_game": User wants to start a fresh game
                - "close": User wants to exit the application
        """
        # Create semi-transparent black overlay to dim the game board
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))

        # Generate appropriate title, message, and color based on result type
        title_text, message_text, title_color = self._get_result_text(
            result_type, winner, reason
        )

        # Enter modal loop - runs independently from main game loop
        running = True
        choice = None

        while running:
            # -------------------- Rendering --------------------

            # Draw the semi-transparent overlay first (covers game board)
            self.screen.blit(overlay, (0, 0))

            # Create dialog rectangle for background and border
            dialog_rect = pygame.Rect(
                self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height
            )

            # Draw dialog background (solid color fill)
            pygame.draw.rect(self.screen, Colors.BACKGROUND, dialog_rect)

            # Draw colored border around dialog
            pygame.draw.rect(self.screen, title_color, dialog_rect, 4)

            # Render the main title text (large and bold)
            # Anti-aliasing (True) makes text smoother
            title_surface = self.title_font.render(title_text, True, title_color)

            # Center title horizontally
            title_rect = title_surface.get_rect(
                centerx=self.dialog_x + self.dialog_width // 2,
                y=self.dialog_y + 30,
            )

            # Draw title to screen
            self.screen.blit(title_surface, title_rect)

            # Draw explanatory message if one exists
            if message_text:
                # Render message text (medium font, standard text color)
                message_surface = self.message_font.render(
                    message_text, True, Colors.COORDINATE_TEXT
                )

                # Center message horizontally
                message_rect = message_surface.get_rect(
                    centerx=self.dialog_x + self.dialog_width // 2,
                    y=self.dialog_y + 100,
                )

                # Draw message to screen
                self.screen.blit(message_surface, message_rect)

            # Get current mouse position for hover detection
            mouse_pos = pygame.mouse.get_pos()

            # Render "New Game" button (left button)
            # Check if mouse is hovering over this button
            new_game_hover = self.new_game_button.collidepoint(mouse_pos)

            # Choose button color based on hover state
            new_game_color = (
                Colors.BUTTON_HOVER if new_game_hover else Colors.BUTTON_NORMAL
            )

            # Draw button background rectangle
            pygame.draw.rect(self.screen, new_game_color, self.new_game_button)

            # Draw button border
            pygame.draw.rect(self.screen, Colors.BORDER, self.new_game_button, 2)

            # Render button label text
            new_game_text = self.button_font.render(
                "New Game", True, Colors.BUTTON_TEXT
            )

            # Center text within button rectangle
            new_game_text_rect = new_game_text.get_rect(
                center=self.new_game_button.center
            )

            # Draw text on button
            self.screen.blit(new_game_text, new_game_text_rect)

            # Render "Close" button (right button)
            # Check hover state
            close_hover = self.close_button.collidepoint(mouse_pos)

            # Choose color
            close_color = Colors.BUTTON_HOVER if close_hover else Colors.BUTTON_NORMAL

            # Draw button background
            pygame.draw.rect(self.screen, close_color, self.close_button)

            # Draw button border
            pygame.draw.rect(self.screen, Colors.BORDER, self.close_button, 2)

            # Render button text
            close_text = self.button_font.render("Close", True, Colors.BUTTON_TEXT)

            # Center text in button
            close_text_rect = close_text.get_rect(center=self.close_button.center)

            # Draw text
            self.screen.blit(close_text, close_text_rect)

            # Update the entire display with all drawn elements
            # flip() refreshes the whole screen (vs update() for partial refresh)
            pygame.display.flip()

            # -------------------- Event Processing --------------------

            # Process all pending events in the queue
            # This loop handles user input (keyboard, mouse, window events)
            for event in pygame.event.get():
                # Handle window close button (X button)
                if event.type == pygame.QUIT:
                    # User closed window - exit application
                    return "close"

                # Handle keyboard input
                elif event.type == pygame.KEYDOWN:
                    # ESC key - quick exit
                    if event.key == pygame.K_ESCAPE:
                        return "close"

                    # N key - quick restart
                    # Keyboard shortcut for "New Game"
                    elif event.key == pygame.K_n:
                        return "new_game"

                # Handle mouse clicks
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Only process left mouse button
                    if event.button == 1:  # Left click
                        # Check if click was on "New Game" button
                        if self.new_game_button.collidepoint(event.pos):
                            return "new_game"

                        # Check if click was on "Close" button
                        elif self.close_button.collidepoint(event.pos):
                            return "close"

        # Fallback return - should never be reached in normal operation
        # If loop exits without user choice, default to close
        return "close"

    def _get_result_text(
        self, result_type: str, winner: Optional[str], reason: str
    ) -> tuple:
        """
        Generate appropriate title, message, and color for the game result.

        This helper method translates the result type into user-friendly text
        and selects appropriate color coding for the dialog border and title.

        Args:
            result_type (str): Type of game ending.
                Valid: "checkmate", "stalemate", "draw", "resignation"

            winner (Optional[str]): Winning player ("White", "Black", or None).
                Used for checkmate and resignation results.

            reason (str): Additional context for draw results.
                Examples: "insufficient material", "50-move rule", "threefold repetition"

        Returns:
            tuple: Three-element tuple containing:
                - title_text (str): Main announcement (e.g., "White Wins!", "Draw")
                - message_text (str): Explanatory message (e.g., "Checkmate - White is victorious")
                - color (tuple): RGB color for border/title (win color or draw color)
        """
        # Checkmate - one player checkmated the opponent's king
        if result_type == "checkmate":
            # Announce winner
            title = f"{winner} Wins!"

            # Provide context about how the game was won
            message = f"Checkmate - {winner} is victorious"

            # Use victory color (typically gold/yellow)
            color = Colors.WIN_COLOR if winner else Colors.COORDINATE_TEXT

        # Stalemate - current player has no legal moves but is not in check
        elif result_type == "stalemate":
            # Announce draw
            title = "Draw"

            # Player cannot move but is not in check = automatic draw
            message = "Stalemate - No legal moves available"

            # Use draw color (typically gray)
            color = Colors.DRAW_COLOR

        # Draw by various rules (50-move, repetition, insufficient material, agreement)
        elif result_type == "draw":
            # Announce draw
            title = "Draw"

            # Provide specific reason if available
            if reason:
                message = f"Game drawn by {reason}"
            else:
                # Generic draw message if no specific reason given
                message = "Game is a draw"

            # Use draw color
            color = Colors.DRAW_COLOR

        # Resignation - one player gave up
        elif result_type == "resignation":
            # Announce winner
            title = f"{winner} Wins!"

            # Explain victory was by resignation rather than checkmate
            message = f"Victory by resignation"

            # Use victory color
            # Fallback to standard color if winner not specified (shouldn't happen)
            color = Colors.WIN_COLOR if winner else Colors.COORDINATE_TEXT

        # Fallback for unknown result types (shouldn't happen in normal use)
        else:
            # Generic game over message
            title = "Game Over"
            message = ""

            # Use standard text color (neutral)
            color = Colors.COORDINATE_TEXT

        # Return tuple of (title, message, color) for dialog display
        return title, message, color
