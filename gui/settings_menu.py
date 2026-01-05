"""
Settings Menu Module
--------------------
Provides an in-game modal settings menu for adjusting game configuration options
in real-time without restarting the application.
"""

import pygame
from typing import Optional, Tuple
from gui.colors import Colors
from utils.config import Config


class SettingsMenu:
    """
    Modal settings menu for adjusting game configuration in real-time.

    Provides an interactive overlay menu with toggle switches and sliders for
    configuring game behavior, visual options, and audio settings. Changes
    apply immediately to the Config system without requiring restart.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the settings menu with layout, fonts, and UI elements.

        Args:
            screen: pygame.Surface
                The main display surface for rendering the menu overlay
        """
        # Store screen reference for rendering
        self.screen = screen

        # Menu panel size
        self.menu_width = 700
        self.menu_height = 650

        # Title font: Large bold for "Settings" header
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)

        # Label font: Medium for setting names and values
        self.label_font = pygame.font.SysFont("Arial", 18)

        # Button font: Smaller bold for close button
        self.button_font = pygame.font.SysFont("Arial", 16, bold=True)

        # Load current configuration values into settings dictionary
        self.settings = self._initialize_settings()

        # Initialize empty dict
        self.setting_rects = {}

    def _calculate_positions(self):
        """
        Calculate dialog and button positions based on current screen size.
        Called every frame to handle window resizing.
        """
        # Get current screen dimensions
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Center menu on screen
        self.menu_x = (screen_width - self.menu_width) // 2
        self.menu_y = (screen_height - self.menu_height) // 2

        # Create close button placeholder
        button_width = 120
        button_height = 40
        self.close_button = pygame.Rect(
            self.menu_x + (self.menu_width - button_width) // 2,
            self.menu_y + self.menu_height - 60,
            button_width,
            button_height,
        )

        # Finalize UI element positioning
        self._create_ui_elements()

    def _initialize_settings(self) -> dict:
        """
        Initialize settings dictionary with current Config values.

        Loads all configurable settings from the Config class and structures them
        into a dictionary format suitable for rendering and user interaction. Each
        setting specifies its label, current value, control type (toggle/slider),
        and for sliders, the valid min/max range.

        Returns:
            dict:
                {
                    "setting_key": {
                        "label": str,
                        "value": bool|int|float,
                        "type": str,
                        "min": int|float,
                        "max": int|float,
                    }
                }
        """
        return {
            "animations": {
                "label": "Enable Animations",
                "value": Config.ANIMATE_MOVES,
                "type": "toggle",
            },
            "animation_speed": {
                "label": "Animation Speed",
                "value": Config.ANIMATION_SPEED,
                "type": "slider",
                "min": 100,
                "max": 500,
            },
            "sounds": {
                "label": "Enable Sounds",
                "value": Config.ENABLE_SOUNDS,
                "type": "toggle",
            },
            "sound_volume": {
                "label": "Sound Volume",
                "value": Config.SOUND_VOLUME,
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
            },
            "show_last_move": {
                "label": "Highlight Last Move",
                "value": Config.SHOW_LAST_MOVE,
                "type": "toggle",
            },
            "show_coordinates": {
                "label": "Show Coordinates",
                "value": Config.SHOW_COORDINATES,
                "type": "toggle",
            },
            "show_captured": {
                "label": "Show Captured Pieces",
                "value": Config.SHOW_CAPTURED_PIECES,
                "type": "toggle",
            },
            "show_fps": {
                "label": "Show FPS Counter",
                "value": Config.SHOW_FPS,
                "type": "toggle",
            },
        }

    def _create_ui_elements(self):
        """
        Create bounding rectangles for all UI elements.

        Calculates and stores pygame.Rect objects for the close button and all
        setting items. These rectangles are used for click detection (determining
        which setting the user clicked) and hover effects (detecting mouse position).
        """
        # Close Button Rectangle
        button_width = 120
        button_height = 40

        # Center button horizontally
        self.close_button = pygame.Rect(
            self.menu_x + (self.menu_width - button_width) // 2,
            self.menu_y + self.menu_height - 60,
            button_width,
            button_height,
        )

        # Setting Item Rectangles
        y_offset = self.menu_y + 80

        # Vertical spacing between settings
        spacing = 55

        # Create rectangle for each setting
        # Loop through all 8 settings in order
        for i, setting_key in enumerate(self.settings.keys()):
            rect = pygame.Rect(
                self.menu_x + 40,
                y_offset + i * spacing,
                self.menu_width - 80,
                40,
            )
            self.setting_rects[setting_key] = rect

    def show(self) -> bool:
        """
        Display the settings menu and handle user interaction (modal).

        Blocks the main game loop and enters a self-contained event loop for the
        settings menu. Renders the menu overlay, handles user clicks on toggles
        and sliders, supports continuous slider dragging, and applies changes to
        Config in real-time. Returns when user closes the menu.

        Returns:
            bool:
                True if any settings were changed during this session
                False if menu was closed without changes
        """
        # -------------------- Create Overlay Surface --------------------

        # Create full-screen semi-transparent black overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))

        running = True  # Event loop control flag
        settings_changed = False  # Track if any setting was modified
        dragging_slider = (
            None  # Track which slider is being dragged (None or setting key)
        )

        while running:
            # -------------------- Render Overlay --------------------
            # Handle window resizing
            self._calculate_positions()

            # Draw semi-transparent overlay over entire screen
            self.screen.blit(overlay, (0, 0))

            # -------------------- Render Menu Panel --------------------

            # Create menu background rectangle
            menu_rect = pygame.Rect(
                self.menu_x, self.menu_y, self.menu_width, self.menu_height
            )

            # Draw dark gray background with rounded corners
            pygame.draw.rect(self.screen, (45, 45, 45), menu_rect, border_radius=10)

            # Draw border around menu panel
            pygame.draw.rect(self.screen, Colors.BORDER, menu_rect, 3, border_radius=10)

            # -------------------- Render Title --------------------

            # Render "Settings" title text
            title = self.title_font.render("Settings", True, (255, 255, 255))
            title_rect = title.get_rect(
                centerx=self.menu_x + self.menu_width // 2,
                y=self.menu_y + 20,
            )
            self.screen.blit(title, title_rect)

            # Draw horizontal separator line below title
            pygame.draw.line(
                self.screen,
                Colors.BORDER,
                (self.menu_x + 40, self.menu_y + 65),
                (self.menu_x + self.menu_width - 40, self.menu_y + 65),
                2,
            )

            # -------------------- Render Settings Items --------------------

            # Get current mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()

            # Draw each setting item (toggle or slider)
            for setting_key, rect in self.setting_rects.items():
                self._draw_setting_item(setting_key, rect, mouse_pos)

            # -------------------- Render Close Button --------------------

            # Check if mouse is hovering over close button
            is_hover = self.close_button.collidepoint(mouse_pos)

            # Choose button color based on hover state
            button_color = Colors.BUTTON_HOVER if is_hover else Colors.BUTTON_NORMAL

            # Draw button background with rounded corners
            pygame.draw.rect(
                self.screen, button_color, self.close_button, border_radius=5
            )

            # Draw button border
            pygame.draw.rect(
                self.screen, Colors.BORDER, self.close_button, 2, border_radius=5
            )

            # Render "Close" button text
            close_text = self.button_font.render("Close", True, Colors.BUTTON_TEXT)
            close_rect = close_text.get_rect(center=self.close_button.center)
            self.screen.blit(close_text, close_rect)

            # -------------------- Update Display --------------------

            # Flip display buffers to show rendered frame
            pygame.display.flip()

            # -------------------- Process Events --------------------

            for event in pygame.event.get():
                # Event: Window Close (X button)
                if event.type == pygame.QUIT:
                    # User closed window, exit menu and return change status
                    return settings_changed

                # Event: Keyboard Input
                elif event.type == pygame.KEYDOWN:
                    # Escape or S key: Close menu and return to game
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_s:
                        return settings_changed

                # Event: Mouse Click
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        # Check if close button was clicked
                        if self.close_button.collidepoint(event.pos):
                            return settings_changed

                        # Check if any setting item was clicked
                        for setting_key, rect in self.setting_rects.items():
                            if rect.collidepoint(event.pos):
                                setting = self.settings[setting_key]

                                # Handle slider click
                                if setting["type"] == "slider":
                                    # Enter dragging mode for continuous adjustment
                                    dragging_slider = setting_key

                                    # Update slider value to click position
                                    self._handle_setting_click(
                                        setting_key, event.pos, rect
                                    )

                                    # Mark as changed and apply to Config
                                    settings_changed = True
                                    self._apply_settings()

                                # Handle toggle click
                                else:
                                    # Flip toggle state
                                    self._handle_setting_click(
                                        setting_key, event.pos, rect
                                    )

                                    # Mark as changed and apply to Config
                                    settings_changed = True
                                    self._apply_settings()

                # Event: Mouse Release
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button released
                        # Exit dragging mode (slider no longer being dragged)
                        dragging_slider = None

                # Event: Mouse Motion
                elif event.type == pygame.MOUSEMOTION:
                    # If user is dragging a slider, update value continuously
                    if dragging_slider is not None:
                        # Get rectangle for the slider being dragged
                        rect = self.setting_rects[dragging_slider]

                        # Update slider value based on new mouse position
                        self._handle_setting_click(dragging_slider, event.pos, rect)

                        # Mark as changed and apply to Config
                        settings_changed = True
                        self._apply_settings()

        # Menu closed, return whether any settings were changed
        return settings_changed

    def _draw_setting_item(
        self, setting_key: str, rect: pygame.Rect, mouse_pos: Tuple[int, int]
    ):
        """
        Render a single setting item (label + control).

        Draws the background, label text, and appropriate control (toggle switch
        or slider) for one setting. Applies hover effect if mouse is over the
        setting item.

        Args:
            setting_key: str
                The key identifying which setting to draw (e.g., "animations")
            rect: pygame.Rect
                The bounding rectangle for this setting item
            mouse_pos: Tuple[int, int]
                Current mouse position (x, y) for hover detection
        """
        # Get setting configuration
        setting = self.settings[setting_key]

        # Check if mouse is hovering over this item
        is_hover = rect.collidepoint(mouse_pos)

        # Draw Background
        bg_color = (60, 60, 60) if is_hover else (50, 50, 50)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)

        # Draw subtle border
        pygame.draw.rect(self.screen, (80, 80, 80), rect, 1, border_radius=5)

        # Draw Label Text
        label = self.label_font.render(setting["label"], True, (220, 220, 220))
        label_rect = label.get_rect(
            x=rect.x + 15,
            centery=rect.centery,
        )
        self.screen.blit(label, label_rect)

        # Draw Control Widget
        if setting["type"] == "toggle":
            # Draw toggle switch (on/off)
            self._draw_toggle(rect, setting["value"])
        elif setting["type"] == "slider":
            # Draw slider with handle
            self._draw_slider(rect, setting)

    def _draw_toggle(self, rect: pygame.Rect, value: bool):
        """
        Render a toggle switch control.

        Args:
            rect: pygame.Rect
                The parent setting item rectangle (for positioning)
            value: bool
                Current toggle state (True = on, False = off)
        """
        # Toggle Dimensions & Position
        toggle_width = 50
        toggle_height = 24

        # Position on right side of parent rect, vertically centered
        toggle_x = rect.right - toggle_width - 15
        toggle_y = rect.centery - toggle_height // 2

        # Draw Toggle Track (Background)
        bg_color = (100, 200, 100) if value else (80, 80, 80)

        # Create toggle track rectangle
        toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_width, toggle_height)

        # Draw with rounded corners (border_radius = half height for pill shape)
        pygame.draw.rect(self.screen, bg_color, toggle_rect, border_radius=12)

        # Draw Toggle Knob (Circle)
        knob_radius = 10

        knob_x = toggle_x + toggle_width - 14 if value else toggle_x + 14
        knob_y = toggle_y + toggle_height // 2

        # Draw white circular knob
        pygame.draw.circle(self.screen, (255, 255, 255), (knob_x, knob_y), knob_radius)

    def _draw_slider(self, rect: pygame.Rect, setting: dict):
        """
        Render a slider control with draggable handle.

        Draws a horizontal track with a progress bar filling from left to the
        current value position, a circular draggable handle at the value position,
        and the current value displayed as text to the left of the slider.

        Args:
            rect: pygame.Rect
                The parent setting item rectangle (for positioning)
            setting: dict
                Setting configuration with keys:
                - "value": Current numeric value (int or float)
                - "min": Minimum allowed value
                - "max": Maximum allowed value
        """
        # Slider Dimensions & Position
        slider_width = 150

        # Position on right side of parent rect, vertically centered
        slider_x = rect.right - slider_width - 15
        slider_y = rect.centery

        # Draw Track (Background Bar)
        track_rect = pygame.Rect(slider_x, slider_y - 2, slider_width, 4)
        pygame.draw.rect(self.screen, (100, 100, 100), track_rect, border_radius=2)

        # Calculate Knob Position
        value = setting["value"]
        min_val = setting["min"]
        max_val = setting["max"]

        # Normalize value to 0.0-1.0 range
        normalized = (value - min_val) / (max_val - min_val)

        # Calculate knob X position based on normalized value
        knob_x = slider_x + int(normalized * slider_width)

        # Draw Progress Bar (Filled Portion)
        progress_rect = pygame.Rect(slider_x, slider_y - 2, knob_x - slider_x, 4)
        pygame.draw.rect(self.screen, Colors.WIN_COLOR, progress_rect, border_radius=2)

        # Draw Knob (Draggable Handle)
        pygame.draw.circle(self.screen, (255, 255, 255), (knob_x, slider_y), 8)

        # Border around knob for definition
        pygame.draw.circle(self.screen, Colors.BORDER, (knob_x, slider_y), 8, 2)

        # Draw Value Text
        if isinstance(value, float):
            value_text = f"{value:.1f}"
        else:
            value_text = str(value)

        # Render value text in gray
        value_surface = self.label_font.render(value_text, True, (180, 180, 180))

        # Position text to left of slider, right-aligned, vertically centered
        value_rect = value_surface.get_rect(
            right=slider_x - 10,
            centery=rect.centery,
        )
        self.screen.blit(value_surface, value_rect)

    def _handle_setting_click(
        self, setting_key: str, pos: Tuple[int, int], rect: pygame.Rect
    ):
        """
        Handle user click on a setting item (toggle or slider).

        For toggles: Flips the boolean value (True ↔ False)
        For sliders: Calculates new value based on click position within slider track

        Args:
            setting_key: str
                The key identifying which setting was clicked
            pos: Tuple[int, int]
                Mouse click position (x, y)
            rect: pygame.Rect
                The setting item's bounding rectangle
        """
        # Get setting configuration
        setting = self.settings[setting_key]

        # Handle Toggle Click
        if setting["type"] == "toggle":
            # Simply flip the boolean value
            setting["value"] = not setting["value"]

        # Handle Slider Click/Drag
        elif setting["type"] == "slider":
            # Slider dimensions (must match _draw_slider)
            slider_width = 150
            slider_x = rect.right - slider_width - 15

            # Extract click X coordinate
            click_x = pos[0]

            # Calculate relative position within slider (0 to slider_width)
            # Clamp to slider bounds (can't go outside track)
            relative_x = max(0, min(slider_width, click_x - slider_x))

            # Normalize to 0.0-1.0 range
            # relative_x=0 → normalized=0.0 (min value)
            # relative_x=150 → normalized=1.0 (max value)
            normalized = relative_x / slider_width

            # Get value range for this slider
            min_val = setting["min"]
            max_val = setting["max"]

            # Map normalized position to actual value
            new_value = min_val + normalized * (max_val - min_val)

            # Round based on original value type
            if isinstance(setting["value"], int):
                # Integer setting: round to nearest int
                setting["value"] = int(new_value)
            else:
                # Float setting: round to 1 decimal place
                setting["value"] = round(new_value, 1)

    def _apply_settings(self):
        """
        Apply current settings values to the Config class.

        Writes all setting values from the self.settings dictionary to their
        corresponding Config class attributes using setattr(). This makes the
        changes visible to all game components that read from Config.
        """
        setattr(Config, "ANIMATE_MOVES", self.settings["animations"]["value"])
        setattr(Config, "ANIMATION_SPEED", self.settings["animation_speed"]["value"])
        setattr(Config, "ENABLE_SOUNDS", self.settings["sounds"]["value"])
        setattr(Config, "SOUND_VOLUME", self.settings["sound_volume"]["value"])
        setattr(Config, "SHOW_LAST_MOVE", self.settings["show_last_move"]["value"])
        setattr(Config, "SHOW_COORDINATES", self.settings["show_coordinates"]["value"])
        setattr(Config, "SHOW_CAPTURED_PIECES", self.settings["show_captured"]["value"])
        setattr(Config, "SHOW_FPS", self.settings["show_fps"]["value"])
