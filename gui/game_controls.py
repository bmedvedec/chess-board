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
from utils.config import Config
import tkinter as tk
from tkinter import filedialog


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

        # Initialize button dictionary and create buttons first
        self.buttons = {}
        self._create_buttons()

        # Load PNG icon images (must be after _create_buttons)
        self.icon_images = {}
        self._load_icons()

        # Track which button mouse is hovering over (None if no hover)
        # Updated each frame during draw() call
        self.hover_button = None
        self.hover_time = 0
        self.tooltip_delay = 30  # Frames before showing tooltip

        # Initialize tkinter root (hidden) for file dialogs
        self._init_tk_root()

    def _init_tk_root(self):
        """
        Initialize hidden tkinter root window for file dialogs.

        This creates a Tk root that remains hidden but allows us to
        use native file dialogs without showing a tkinter window.
        """
        try:
            self.tk_root = tk.Tk()
            self.tk_root.withdraw()  # Hide the root window
            self.tk_root.attributes("-topmost", True)  # Keep dialogs on top
            print("[GameControls] Tkinter initialized for file dialogs")
        except Exception as e:
            print(f"[GameControls] ⚠️ Failed to initialize tkinter: {e}")
            self.tk_root = None

    def _load_icons(self):
        """
        Load PNG icon images from assets/icons directory.

        Loads and caches icon images for all buttons. Falls back to
        colored rectangles if images cannot be loaded.
        """
        # Extract unique icon filenames from button definitions
        icon_files = set()
        for button in self.buttons.values():
            if "icon" in button and button["icon"]:
                icon_files.add(button["icon"])

        for icon_file in icon_files:
            icon_path = os.path.join(Config.ICONS_DIR, icon_file)
            try:
                if os.path.exists(icon_path):
                    # Load icon and scale to button size
                    original = pygame.image.load(icon_path).convert_alpha()
                    scaled = pygame.transform.smoothscale(
                        original, (self.icon_size - 10, self.icon_size - 10)
                    )
                    self.icon_images[icon_file] = scaled
                    print(f"[GameControls] Loaded icon: {icon_file}")
                else:
                    print(f"[GameControls] ⚠️ Icon not found: {icon_path}")
                    self.icon_images[icon_file] = None
            except Exception as e:
                print(f"[GameControls] ❌ Error loading {icon_file}: {e}")
                self.icon_images[icon_file] = None

    def _create_buttons(self):
        """
        Create all control buttons with calculated positions.

        Builds a dictionary of buttons arranged vertically in the panel.
        """
        # Calculate horizontal positions for 4 buttons
        total_buttons = 4
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
            "icon": "play.png",
        }
        button_x += self.icon_size + self.spacing

        # Button 3: Save
        self.buttons["save_pgn"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Save Game (PGN)",
            "enabled": True,
            "icon": "save.png",
        }
        button_x += self.icon_size + self.spacing

        # Button 4: Load
        self.buttons["load_pgn"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Load Game (PGN)",
            "enabled": True,
            "icon": "load.png",
        }
        button_x += self.icon_size + self.spacing

        # Button 5: Resign
        self.buttons["resign"] = {
            "rect": pygame.Rect(button_x, self.y, self.icon_size, self.icon_size),
            "tooltip": "Resign",
            "enabled": True,
            "icon": "resign.png",
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
            icon_file = button["icon"]

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

            # Draw icon (PNG or fallback)
            if (
                icon_file in self.icon_images
                and self.icon_images[icon_file] is not None
            ):
                # Draw PNG icon centered in button
                icon_image = self.icon_images[icon_file]
                icon_rect = icon_image.get_rect(center=rect.center)

                # Apply dimming effect if disabled
                if not enabled:
                    # Create dimmed version
                    dimmed = icon_image.copy()
                    dimmed.set_alpha(100)
                    self.screen.blit(dimmed, icon_rect)
                else:
                    self.screen.blit(icon_image, icon_rect)
            else:
                # Fallback: Draw colored rectangle if icon failed to load
                fallback_rect = pygame.Rect(
                    rect.centerx - 15, rect.centery - 15, 30, 30
                )
                fallback_color = (150, 150, 150) if enabled else (80, 80, 80)
                pygame.draw.rect(self.screen, fallback_color, fallback_rect)

        # Handle hover tracking for tooltips
        if current_hover != self.hover_button:
            self.hover_button = current_hover
            self.hover_time = 0
        elif current_hover:
            self.hover_time += 1

        # Draw tooltip if hovering long enough
        if self.hover_button and self.hover_time > self.tooltip_delay:
            self._draw_tooltip(self.hover_button, mouse_pos)

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

    def show_save_dialog(self, default_name: Optional[str] = None) -> Optional[str]:
        """
        Show native OS save file dialog to get save location.

        Opens the system's native file save dialog (Windows Explorer on Windows,
        Finder on Mac, etc.) allowing the user to choose where to save the game.

        Args:
            default_name (Optional[str], optional): Default filename suggestion.
                If None, auto-generates timestamp-based name.
                Defaults to None.

        Returns:
            Optional[str]: Full file path selected by user, or None if cancelled.
                Example: "C:/Users/Username/Documents/my_game.pgn"
        """
        if self.tk_root is None:
            print("[GameControls] ⚠️ Tkinter not available, cannot show file dialog")
            return None

        try:
            # Generate default filename if not provided
            if default_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_name = f"chess_game_{timestamp}.pgn"

            # Ensure .pgn extension
            if not default_name.endswith(".pgn"):
                default_name += ".pgn"

            # Get user's documents folder as initial directory
            initial_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(initial_dir):
                initial_dir = os.path.expanduser("~")

            # Show native save dialog
            filepath = filedialog.asksaveasfilename(
                parent=self.tk_root,
                title="Save Chess Game",
                initialdir=initial_dir,
                initialfile=default_name,
                defaultextension=".pgn",
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            )

            # Process tkinter events to ensure dialog closes properly
            self.tk_root.update()

            # Return filepath (or None if user cancelled)
            return filepath if filepath else None

        except Exception as e:
            print(f"[GameControls] ❌ Error showing save dialog: {e}")
            return None

    def show_load_dialog(self) -> Optional[str]:
        """
        Show native OS open file dialog to select game to load.

        Opens the system's native file open dialog allowing the user to browse
        and select a PGN file from any location on their computer.

        Returns:
            Optional[str]: Full file path selected by user, or None if cancelled.
                Example: "C:/Users/Username/Downloads/saved_game.pgn"
        """
        if self.tk_root is None:
            print("[GameControls] ⚠️ Tkinter not available, cannot show file dialog")
            return None

        try:
            # Get user's documents folder as initial directory
            initial_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(initial_dir):
                initial_dir = os.path.expanduser("~")

            # Show native open dialog
            filepath = filedialog.askopenfilename(
                parent=self.tk_root,
                title="Load Chess Game",
                initialdir=initial_dir,
                defaultextension=".pgn",
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            )

            # Process tkinter events to ensure dialog closes properly
            self.tk_root.update()

            # Return filepath (or None if user cancelled)
            return filepath if filepath else None

        except Exception as e:
            print(f"[GameControls] ❌ Error showing load dialog: {e}")
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
