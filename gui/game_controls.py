"""
Game Controls
-------------
Interactive UI panel for game management operations in the chess application.

This module provides a complete control panel system for managing chess games,
including saving games to PGN format, loading previously saved games, and
resigning from the current game. It features both a button-based control panel
and modal dialogs for file operations.
"""

import pygame
import os
from typing import Optional, Tuple
from datetime import datetime
from gui.colors import Colors


class GameControls:
    """
    Interactive control panel for chess game management operations.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        width: int,
        icon_size: int = 50,
        spacing: int = 10,
    ):
        """
        Initialize game controls panel with button layout.

        Creates a vertical stack of buttons for game control operations.

        Args:
            screen (pygame.Surface): Main pygame display surface.
                Used for rendering buttons and text.

            x (int): Left edge X coordinate of control panel.
                All buttons will be aligned to this X position.

            y (int): Top edge Y coordinate of control panel.
                First button starts at this Y position.

            width (int): Width of all buttons in pixels.
                All buttons in the panel have identical width.

            icon_size (int, optional): Height of each button in pixels.
                Defaults to 50.

            spacing (int, optional): Vertical space between buttons in pixels.
                Defaults to 10.
        """
        # Store display surface reference
        self.screen = screen

        # Panel positioning - defines top-left corner and dimensions
        self.x = x
        self.y = y
        self.width = width
        self.icon_size = icon_size
        self.spacing = spacing

        # Fonts
        self.tooltip_font = pygame.font.SysFont("Arial", 12)

        # Initialize button dictionary
        self.buttons = {}
        self._create_buttons()

        # Track which button mouse is hovering over (None if no hover)
        # Updated each frame during draw() call
        self.hover_button = None
        self.hover_time = 0
        self.tooltip_delay = 30  # Frames before showing tooltip

    def _create_buttons(self):
        """
        Create all control buttons with calculated positions.

        Builds a dictionary of buttons arranged vertically in the panel.
        """
        # Calculate horizontal positions for 5 buttons
        total_buttons = 5
        total_width = (total_buttons * self.icon_size) + (
            (total_buttons - 1) * self.spacing
        )
        start_x = self.x + (self.width - total_width) // 2  # Center buttons

        button_x = start_x

        # Button 1: New Game
        self.buttons["new_game"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "New Game (R)",
            "enabled": True,
            "icon": "refresh",
        }
        button_x += self.icon_size + self.spacing

        # Button 2: Change Time Control
        self.buttons["change_time"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Change Time Control (T)",
            "enabled": True,
            "icon": "clock",
        }
        button_x += self.icon_size + self.spacing

        # Button 3: Save
        self.buttons["save_pgn"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Save Game (PGN)",
            "enabled": True,
            "icon": "save",
        }
        button_x += self.icon_size + self.spacing

        # Button 4: Load
        self.buttons["load_pgn"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Load Game (PGN)",
            "enabled": True,
            "icon": "load",
        }
        button_x += self.icon_size + self.spacing

        # Button 5: Resign
        self.buttons["resign"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Resign",
            "enabled": True,
            "icon": "resign",
        }

    def draw(self):
        """
        Render all icon buttons with hover effects and tooltips.
        """
        # Get current mouse position to detect hover
        mouse_pos = pygame.mouse.get_pos()
        current_hover = None

        # Draw each button with appropriate styling
        for button_id, button in self.buttons.items():
            # Extract button data
            rect = button["rect"]
            enabled = button["enabled"]
            icon_type = button["icon"]

            # Check if mouse is hovering over this button
            is_hover = rect.collidepoint(mouse_pos) and enabled

            if is_hover:
                # Track which button is currently hovered
                current_hover = button_id

            # Determine button colors based on state
            if not enabled:
                # Disabled state: Dark gray background, dimmed text
                bg_color = (60, 60, 60)
                icon_color = (100, 100, 100)
            elif is_hover:
                # Hover state: Bright highlight color
                bg_color = Colors.BUTTON_HOVER
                icon_color = (255, 255, 255)
            else:
                # Normal state: Standard button color
                bg_color = Colors.BUTTON_NORMAL
                icon_color = (220, 220, 220)

            # Draw button background
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)

            # Draw button border
            pygame.draw.rect(self.screen, Colors.BORDER, rect, 2, border_radius=5)

            # Draw icon
            self._draw_icon(icon_type, rect, icon_color)

        # Handle hover tracking for tooltips
        if current_hover != self.hover_button:
            self.hover_button = current_hover
            self.hover_time = 0
        elif current_hover:
            self.hover_time += 1

        # Draw tooltip if hovering long enough
        if self.hover_button and self.hover_time > self.tooltip_delay:
            self._draw_tooltip(self.hover_button, mouse_pos)

    def _draw_icon(
        self, icon_type: str, rect: pygame.Rect, color: Tuple[int, int, int]
    ):
        """
        Draw icon inside button rectangle.

        Args:
            icon_type (str): Type of icon to draw.
                Valid types: "refresh", "save", "load", "resign"

            rect (pygame.Rect): Rectangle area to draw icon within.

            color (Tuple[int, int, int]): Color of icon.
        """
        # Calculate center and size for icon drawing
        center_x = rect.centerx
        center_y = rect.centery
        size = rect.width // 3

        if icon_type == "refresh":
            # Circular arrow (new game)
            # Draw circular arrow using arc and triangle
            radius = size
            # Main arc
            arc_rect = pygame.Rect(
                center_x - radius, center_y - radius, radius * 2, radius * 2
            )
            pygame.draw.arc(self.screen, color, arc_rect, 0.5, 5.8, 3)

            # Arrow head (triangle)
            arrow_points = [
                (center_x + radius - 5, center_y - radius + 5),
                (center_x + radius + 5, center_y - radius - 5),
                (center_x + radius + 8, center_y - radius + 8),
            ]
            pygame.draw.polygon(self.screen, color, arrow_points)

        elif icon_type == "save":
            # Floppy disk icon
            # Outer rectangle
            save_rect = pygame.Rect(
                center_x - size, center_y - size, size * 2, size * 2
            )
            pygame.draw.rect(self.screen, color, save_rect, 2)

            # Top notch (cutout)
            notch_rect = pygame.Rect(
                center_x + size // 2, center_y - size, size // 2, size // 2
            )
            pygame.draw.rect(self.screen, Colors.BUTTON_NORMAL, notch_rect)
            pygame.draw.line(
                self.screen,
                color,
                (center_x + size // 2, center_y - size),
                (center_x + size, center_y - size // 2),
                2,
            )

            # Inner rectangle (disk shutter)
            inner_rect = pygame.Rect(
                center_x - size + 4, center_y - size // 2, size * 2 - 8, size + 2
            )
            pygame.draw.rect(self.screen, color, inner_rect, 2)

        elif icon_type == "load":
            # Folder icon
            # Folder body
            folder_rect = pygame.Rect(
                center_x - size, center_y - size // 2, size * 2, size + 4
            )
            pygame.draw.rect(self.screen, color, folder_rect, 2)

            # Folder tab
            tab_rect = pygame.Rect(
                center_x - size, center_y - size - 4, size, size // 2
            )
            pygame.draw.rect(self.screen, color, tab_rect, 2)

        elif icon_type == "resign":
            # White flag icon
            # Flag pole
            pole_x = center_x - size
            pygame.draw.line(
                self.screen,
                color,
                (pole_x, center_y - size),
                (pole_x, center_y + size),
                3,
            )

            # Flag (waving shape)
            flag_points = [
                (pole_x, center_y - size),
                (pole_x + size * 1.5, center_y - size + 4),
                (pole_x + size * 1.3, center_y - size // 2 + 2),
                (pole_x + size * 1.5, center_y),
                (pole_x, center_y - 2),
            ]
            pygame.draw.polygon(self.screen, color, flag_points)
            pygame.draw.polygon(self.screen, color, flag_points, 2)

    def _draw_tooltip(self, button_id: str, mouse_pos: Tuple[int, int]):
        """
        Draw tooltip near mouse cursor.

        Args:
            button_id (str): ID of button to show tooltip for.
                Valid IDs: "save_pgn", "load_pgn", "resign"

            mouse_pos (Tuple[int, int]): Current mouse position (x, y).
                Used to position tooltip.
        """
        # Get tooltip text from button dictionary
        tooltip_text = self.buttons[button_id]["tooltip"]
        text_surface = self.tooltip_font.render(tooltip_text, True, (255, 255, 255))

        # Position tooltip below mouse cursor
        tooltip_x = mouse_pos[0] - text_surface.get_width() // 2
        tooltip_y = mouse_pos[1] + 20

        # Create background rectangle
        padding = 5
        tooltip_rect = pygame.Rect(
            tooltip_x - padding,
            tooltip_y - padding,
            text_surface.get_width() + padding * 2,
            text_surface.get_height() + padding * 2,
        )

        # Draw tooltip background
        pygame.draw.rect(self.screen, (50, 50, 50), tooltip_rect, border_radius=3)
        pygame.draw.rect(self.screen, Colors.BORDER, tooltip_rect, 1, border_radius=3)

        # Draw tooltip text
        self.screen.blit(text_surface, (tooltip_x, tooltip_y))

    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click and detect which button was clicked.

        Args:
            pos (Tuple[int, int]): Mouse click position as (x, y) coordinates.
                Typically from pygame.event.pos for MOUSEBUTTONDOWN events.

        Returns:
            Optional[str]: Button ID that was clicked, or None if no button hit.
                Possible return values:
                - "save_pgn": Save button was clicked
                - "load_pgn": Load button was clicked
                - "resign": Resign button was clicked
                - None: Click was outside all buttons or on disabled button
        """
        # Check each button to see if click intersects it
        for button_id, button in self.buttons.items():
            # Only enabled buttons respond to clicks
            if button["enabled"] and button["rect"].collidepoint(pos):
                return button_id

        # No button was clicked
        return None

    def set_button_enabled(self, button_id: str, enabled: bool):
        """
        Enable or disable a specific button.

        Args:
            button_id (str): ID of button to modify.
                Valid IDs: "save_pgn", "load_pgn", "resign"

            enabled (bool): True to enable button, False to disable it.
        """
        # Check that button ID exists before modifying
        if button_id in self.buttons:
            self.buttons[button_id]["enabled"] = enabled


class SimplePGNDialog:
    """
    Modal dialog for PGN file save/load operations with text input.

    This class provides a simple text-based file dialog for entering filenames
    when saving or loading chess games in PGN format.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize PGN dialog with centered layout.

        Calculates positions for all dialog elements (title, input field,
        buttons) based on screen dimensions to center the dialog.

        Args:
            screen (pygame.Surface): Main pygame display surface.
                Used to determine screen size for centering and for rendering.
        """
        # Store screen reference for rendering
        self.screen = screen

        # Dialog box dimensions
        self.dialog_width = 500
        self.dialog_height = 200

        # Center dialog on screen
        self.dialog_x = (screen.get_width() - self.dialog_width) // 2
        self.dialog_y = (screen.get_height() - self.dialog_height) // 2

        # Create fonts for dialog text
        self.title_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 18)

        # Text input field rectangle
        self.input_rect = pygame.Rect(
            self.dialog_x + 50,
            self.dialog_y + 80,
            self.dialog_width - 100,
            40,
        )

        # Button positioning
        button_y = self.dialog_y + 140

        # OK button: Left of center
        self.ok_button = pygame.Rect(self.dialog_x + 100, button_y, 120, 40)

        # Cancel button: Right of center
        self.cancel_button = pygame.Rect(self.dialog_x + 280, button_y, 120, 40)

    def show_save_dialog(self, default_name: Optional[str] = None) -> Optional[str]:
        """
        Show modal dialog to get filename for saving current game.

        Displays a text input dialog with a suggested filename based on current
        timestamp. User can accept the suggestion, modify it, or cancel.

        Args:
            default_name (Optional[str], optional): Custom default filename.
                If None, auto-generates timestamp-based name like:
                "chess_game_20250115_143022.pgn"
                Defaults to None.

        Returns:
            Optional[str]: Filename entered by user (without directory path).
                - "my_game.pgn": User confirmed with filename
                - None: User cancelled (pressed Cancel or Escape)
        """
        # Generate timestamp-based default if none provided
        if default_name is None:
            # Format: chess_game_YYYYMMDD_HHMMSS.pgn
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"chess_game_{timestamp}.pgn"

        # Show input dialog with "Save Game" title
        return self._show_input_dialog("Save Game", "Filename:", default_name)

    def show_load_dialog(self) -> Optional[str]:
        """
        Show modal dialog to get filename for loading saved game.

        Returns:
            Optional[str]: Filename entered by user (without directory path).
                - "my_game.pgn": User confirmed with filename
                - None: User cancelled (pressed Cancel or Escape)
        """
        # Show input dialog with "Load Game" title and empty default
        return self._show_input_dialog("Load Game", "Filename:", "")

    def _show_input_dialog(
        self, title: str, prompt: str, default_text: str
    ) -> Optional[str]:
        """
        Display modal text input dialog and block until user responds.

        This is the core dialog rendering method that runs its own event loop,
        blocking the main game loop until the user either confirms or cancels.

        Args:
            title (str): Dialog title text displayed at top.
                Examples: "Save Game", "Load Game"

            prompt (str): Label for input field.
                Examples: "Filename:", "Enter name:"

            default_text (str): Pre-filled text in input field.
                User can modify or clear this. Empty string for no default.

        Returns:
            Optional[str]: User's final input text, or None if cancelled.
                - "my_game": User pressed OK or Enter with text
                - "": User pressed OK with empty field (returns empty string, not None)
                - None: User pressed Cancel, Escape, or closed window
        """
        # ==================== Initialize overlay and input state ====================

        # Create semi-transparent black overlay to dim background
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))

        # Initialize input field with default text
        input_text = default_text

        # Cursor blinking state
        cursor_visible = True
        cursor_timer = 0

        # ==================== Modal event loop ====================

        running = True
        while running:
            # -------------------- Rendering Phase --------------------

            # Draw darkening overlay over entire screen
            self.screen.blit(overlay, (0, 0))

            # Create rectangle for dialog background
            dialog_rect = pygame.Rect(
                self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height
            )

            # Fill dialog background
            pygame.draw.rect(self.screen, Colors.BACKGROUND, dialog_rect)

            # Draw dialog border
            pygame.draw.rect(self.screen, Colors.BORDER, dialog_rect, 3)

            # Render title text
            title_surface = self.title_font.render(title, True, Colors.COORDINATE_TEXT)

            # Center title horizontally
            title_rect = title_surface.get_rect(
                centerx=self.dialog_x + self.dialog_width // 2, y=self.dialog_y + 20
            )

            # Draw title
            self.screen.blit(title_surface, title_rect)

            # Render prompt text
            prompt_surface = self.text_font.render(prompt, True, Colors.COORDINATE_TEXT)

            prompt_rect = prompt_surface.get_rect(
                x=self.input_rect.x, y=self.input_rect.y - 25
            )

            # Draw prompt label
            self.screen.blit(prompt_surface, prompt_rect)

            # Fill input box with dark gray background
            pygame.draw.rect(self.screen, (60, 60, 60), self.input_rect)

            # Draw input box border (2px)
            pygame.draw.rect(self.screen, Colors.COORDINATE_TEXT, self.input_rect, 2)

            # Render current input text in white
            text_surface = self.text_font.render(input_text, True, (255, 255, 255))

            text_rect = text_surface.get_rect(
                x=self.input_rect.x + 10, centery=self.input_rect.centery
            )

            # Draw input text
            self.screen.blit(text_surface, text_rect)

            # Increment cursor blink timer
            cursor_timer += 1

            # Toggle cursor visibility every 30 frames (blink effect)
            if cursor_timer > 30:
                cursor_visible = not cursor_visible
                cursor_timer = 0  # Reset timer

            # Only draw cursor when it's in "visible" phase of blink
            if cursor_visible:
                # Calculate horizontal cursor position (after text)
                cursor_x = text_rect.right + 2

                # Calculate vertical cursor position
                cursor_y1 = self.input_rect.y + 8
                cursor_y2 = self.input_rect.bottom - 8

                # Draw vertical white line as cursor
                pygame.draw.line(
                    self.screen,
                    (255, 255, 255),
                    (cursor_x, cursor_y1),
                    (cursor_x, cursor_y2),
                    2,
                )

            # Get current mouse position for hover detection
            mouse_pos = pygame.mouse.get_pos()

            # OK Button
            # Check if mouse is hovering over OK button
            ok_hover = self.ok_button.collidepoint(mouse_pos)
            # Use hover color if hovering, normal color otherwise
            ok_color = Colors.BUTTON_HOVER if ok_hover else Colors.BUTTON_NORMAL
            # Fill button background
            pygame.draw.rect(self.screen, ok_color, self.ok_button)
            # Draw button border
            pygame.draw.rect(self.screen, Colors.BORDER, self.ok_button, 2)
            # Render "OK" text
            ok_text = self.text_font.render("OK", True, Colors.BUTTON_TEXT)
            # Center text in button
            ok_text_rect = ok_text.get_rect(center=self.ok_button.center)
            # Draw button text
            self.screen.blit(ok_text, ok_text_rect)

            # Cancel Button
            # Check if mouse is hovering over Cancel button
            cancel_hover = self.cancel_button.collidepoint(mouse_pos)
            # Use hover color if hovering, normal color otherwise
            cancel_color = Colors.BUTTON_HOVER if cancel_hover else Colors.BUTTON_NORMAL
            # Fill button background
            pygame.draw.rect(self.screen, cancel_color, self.cancel_button)
            # Draw button border
            pygame.draw.rect(self.screen, Colors.BORDER, self.cancel_button, 2)
            # Render "Cancel" text
            cancel_text = self.text_font.render("Cancel", True, Colors.BUTTON_TEXT)
            # Center text in button
            cancel_text_rect = cancel_text.get_rect(center=self.cancel_button.center)
            # Draw button text
            self.screen.blit(cancel_text, cancel_text_rect)

            # Update display with all drawn elements
            pygame.display.flip()

            # -------------------- Event Handling Phase --------------------

            for event in pygame.event.get():
                # Window close event
                if event.type == pygame.QUIT:
                    # User closed window - treat as cancel
                    return None

                # Key press event
                elif event.type == pygame.KEYDOWN:
                    # Enter key: Confirm and return input
                    if event.key == pygame.K_RETURN:
                        # Return input text, or None if empty
                        return input_text if input_text else None

                    # Escape key: Cancel and return None
                    elif event.key == pygame.K_ESCAPE:
                        return None

                    # Backspace: Delete last character
                    elif event.key == pygame.K_BACKSPACE:
                        # String slicing removes last character
                        # If input_text is empty, slicing has no effect
                        input_text = input_text[:-1]

                    # All other keys: Attempt to add character
                    else:
                        # Check if key produces a printable character
                        if event.unicode and event.unicode.isprintable():
                            # Enforce maximum filename length
                            if len(input_text) < 50:
                                # Append character to input string
                                input_text += event.unicode

                # Mouse click event
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Only handle left mouse button
                    if event.button == 1:
                        # Check if OK button was clicked
                        if self.ok_button.collidepoint(event.pos):
                            # Return input text, or None if empty
                            return input_text if input_text else None

                        # Check if Cancel button was clicked
                        elif self.cancel_button.collidepoint(event.pos):
                            # Cancel operation - return None
                            return None

        # Fallback return None (should not reach here)
        return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
# Standalone functions for PGN file I/O operations.
# These can be used independently of the GameControls classes.


def save_pgn_to_file(pgn_string: str, filename: str) -> bool:
    """
    Save chess game in PGN format to disk.

    Writes the provided PGN string to a file in the "saved_games" directory.

    Args:
        pgn_string (str): Complete PGN formatted game data.
            Should include headers (Event, Date, etc.) and move sequence.

        filename (str): Filename to save as (with or without .pgn extension).
            Examples: "my_game", "my_game.pgn" (both work)
            Will be saved to: saved_games/[filename].pgn

    Returns:
        bool: True if file saved successfully, False if error occurred.
    """
    try:
        # Ensure filename has proper extension
        # Prevents double extensions like "game.pgn.pgn"
        if not filename.endswith(".pgn"):
            filename += ".pgn"

        # Create saved_games directory if it doesn't exist
        # exist_ok=True prevents error if directory already exists
        os.makedirs("saved_games", exist_ok=True)

        # Build full path: saved_games/filename.pgn
        filepath = os.path.join("saved_games", filename)

        # Write PGN string to file
        with open(filepath, "w") as f:
            f.write(pgn_string)

        # Log success with full path for user confirmation
        print(f"[GameControls] ✅ Saved game to: {filepath}")
        return True

    except Exception as e:
        # Catch all file I/O errors (permissions, disk full, etc.)
        print(f"[GameControls] ❌ Error saving PGN: {e}")
        return False


def load_pgn_from_file(filename: str) -> Optional[str]:
    """
    Load chess game in PGN format from disk.

    Reads a PGN file and returns its contents as a string. Searches for the
    file in multiple locations to provide flexibility:
    1. Current working directory (direct path)
    2. saved_games/ subdirectory

    Args:
        filename (str): Filename to load (with or without .pgn extension).
            Examples: "my_game", "my_game.pgn" (both work)
            Searches in:
            - ./my_game.pgn
            - ./saved_games/my_game.pgn

    Returns:
        Optional[str]: PGN file contents as string, or None if not found/error.
            - String: Successfully loaded PGN data
            - None: File not found or error occurred
    """
    try:
        # Ensure filename has proper extension
        # Prevents issues with partial filename matching
        if not filename.endswith(".pgn"):
            filename += ".pgn"

        # Define multiple search paths for flexibility
        # Allows loading from either current directory or saved_games
        possible_paths = [
            filename,  # Try direct path first (./filename.pgn)
            os.path.join("saved_games", filename),  # Then try saved_games/filename.pgn
        ]

        # Search each possible location
        for filepath in possible_paths:
            # Check if file exists at this path
            if os.path.exists(filepath):
                # Open and read entire file contents
                # Uses text mode ("r") to read as string
                with open(filepath, "r") as f:
                    pgn_string = f.read()

                # Log success with path that was found
                print(f"[GameControls] ✅ Loaded game from: {filepath}")

                # Return PGN data
                return pgn_string

        # If we reach here, file wasn't found in any location
        print(f"[GameControls] ❌ File not found: {filename}")
        return None

    except Exception as e:
        # Catch all file I/O errors (permissions, encoding issues, etc.)
        print(f"[GameControls] ❌ Error loading PGN: {e}")
        return None
