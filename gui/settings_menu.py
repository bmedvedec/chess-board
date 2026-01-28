"""
Settings Menu Module
--------------------
Provides an in-game modal settings menu for adjusting game configuration options
in real-time without restarting the application.
"""

from tkinter import font
import pygame
from typing import Optional, Tuple
from gui.colors import Colors
from utils.config import Config
import tkinter as tk
from tkinter import filedialog
import os

from utils.config_persistence import save_config_to_file


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

        # Tkinter for file dialogs
        self._init_tk_root()

        # Browse buttons for file_select types
        self.browse_buttons = {}

        # Scrolling support
        self.scroll_offset = 0  # Current scroll position (positive = scrolled down)
        self.content_height = 0  # Total height of all settings rows
        self.scroll_speed = 40  # Pixels per scroll event
        self.scroll_bar_width = 8
        self.scroll_bar_color = (120, 120, 120)
        self.scroll_bar_active_color = (180, 180, 180)

    def _init_tk_root(self):
        """
        Initialize hidden tkinter root window for file dialogs.
        """
        try:
            self.tk_root = tk.Tk()
            self.tk_root.withdraw()  # Hide the root window
            self.tk_root.attributes("-topmost", True)  # Keep dialogs on top
            print("[SettingsMenu] Tkinter initialized for file dialogs")
        except Exception as e:
            print(f"[SettingsMenu] ⚠️ Failed to initialize tkinter: {e}")
            self.tk_root = None

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
            "enable_premove": {
                "label": "Enable Premoves",
                "value": Config.ENABLE_PREMOVE,
                "type": "toggle",
            },
            "show_fps": {
                "label": "Show FPS Counter",
                "value": Config.SHOW_FPS,
                "type": "toggle",
            },
            "use_uci_engine": {
                "label": "Use UCI Engine (e.g., Stockfish)",
                "value": Config.USE_UCI_ENGINE,
                "type": "toggle",
            },
            "uci_engine_path": {
                "label": "UCI Engine Path",
                "value": Config.UCI_ENGINE_PATH,
                "type": "file_select",
            },
            "engine_time_limit": {
                "label": "Engine Time Limit (s)",
                "value": Config.ENGINE_TIME_LIMIT,
                "type": "slider",
                "min": 0.1,
                "max": 30.0,
            },
            "engine_skill_level": {
                "label": "Engine Skill Level",
                "value": Config.ENGINE_SKILL_LEVEL,
                "type": "slider",
                "min": 0,
                "max": 20,
            },
            "engine_max_depth": {
                "label": "Max Search Depth (0=unlimited)",
                "value": Config.ENGINE_MAX_DEPTH or 0,
                "type": "slider",
                "min": 0,
                "max": 25,
            },
        }

    def _create_ui_elements(self):
        """
        Create and position all setting UI elements (labels, toggles, sliders, browse).
        """
        self.setting_rects = {}
        self.browse_buttons = {}  # reset

        base_y = self.menu_y + 90
        x_label = self.menu_x + 40
        row_height = 42
        gap = 6

        ordered_keys = list(self.settings.keys())  # keeps the order from dict

        y = base_y
        for key in ordered_keys:
            setting = self.settings[key]
            rect = pygame.Rect(x_label, y, self.menu_width - 80, row_height)
            self.setting_rects[key] = rect

            # Special handling for UCI engine path row → add Browse button
            if key == "uci_engine_path":
                browse_rect = pygame.Rect(
                    self.menu_x + self.menu_width - 140,
                    y + (row_height - 26) // 2,
                    85,
                    26,
                )
                self.browse_buttons[key] = browse_rect

            y += row_height + gap

        self.content_height = y - base_y + 20

        # Close button (unchanged)
        button_width = 120
        button_height = 40
        self.close_button = pygame.Rect(
            self.menu_x + (self.menu_width - button_width) // 2,
            self.menu_y + self.menu_height - 60,
            button_width,
            button_height,
        )

    def show(self) -> bool:
        """
        Display the settings menu and handle user interaction (modal).

        Blocks the main game loop and enters a self-contained event loop for the
        settings menu. Renders the menu overlay, handles user clicks on toggles
        and sliders, supports continuous slider dragging, mouse wheel scrolling,
        and applies changes to Config in real-time. Returns when user closes the menu.

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

            # -------------------- Render Settings Items (Scrollable) --------------------

            # Get current mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()

            # Clip drawing to content area + enforce right padding
            content_area = pygame.Rect(
                self.menu_x + 20,
                self.menu_y + 90,
                self.menu_width - 40,
                self.menu_height - 170,
            )
            old_clip = self.screen.get_clip()
            self.screen.set_clip(content_area)

            # Draw each setting item with scroll offset
            for setting_key, rect in self.setting_rects.items():
                # Apply scroll offset to y-position
                draw_rect = rect.copy()
                draw_rect.y -= self.scroll_offset

                # Skip if entirely off-screen
                if (
                    draw_rect.bottom < content_area.top
                    or draw_rect.top > content_area.bottom
                ):
                    continue

                self._draw_setting_item(setting_key, draw_rect, mouse_pos)

            self.screen.set_clip(old_clip)

            # -------------------- Render Scrollbar if Needed --------------------

            if self.content_height > content_area.height:
                scrollable_height = content_area.height
                total_content = self.content_height
                thumb_height = max(
                    30, int(scrollable_height * scrollable_height / total_content)
                )
                thumb_y = content_area.top + int(
                    (self.scroll_offset / (total_content - scrollable_height))
                    * (scrollable_height - thumb_height)
                )

                # Track background
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    (
                        self.menu_x + self.menu_width - 20,
                        content_area.top,
                        self.scroll_bar_width,
                        content_area.height,
                    ),
                    border_radius=4,
                )

                # Thumb (hover color if mouse over)
                thumb_color = (
                    self.scroll_bar_active_color
                    if content_area.collidepoint(mouse_pos)
                    else self.scroll_bar_color
                )
                pygame.draw.rect(
                    self.screen,
                    thumb_color,
                    (
                        self.menu_x + self.menu_width - 20,
                        thumb_y,
                        self.scroll_bar_width,
                        thumb_height,
                    ),
                    border_radius=4,
                )

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

                # Event: Mouse Wheel (Scrolling)
                elif event.type == pygame.MOUSEWHEEL:
                    # Scroll up (negative y) or down (positive y)
                    scroll_amount = -event.y * self.scroll_speed  # Negative for up
                    self.scroll_offset = max(
                        0,
                        min(
                            self.scroll_offset + scroll_amount,
                            max(0, self.content_height - content_area.height),
                        ),
                    )

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        # Check if close button was clicked
                        if self.close_button.collidepoint(event.pos):
                            if settings_changed:
                                self._apply_settings()
                                save_config_to_file()
                                running = False

                        # ────────────────────────────────────────────────
                        # NEW: Check Browse button click (UCI engine path)
                        # ────────────────────────────────────────────────
                        if "uci_engine_path" in self.browse_buttons:
                            original_btn_rect = self.browse_buttons["uci_engine_path"]
                            drawn_btn_rect = original_btn_rect.copy()
                            drawn_btn_rect.y -= self.scroll_offset

                            if drawn_btn_rect.collidepoint(event.pos):
                                self._select_engine_file()
                                settings_changed = True
                                continue  # skip other setting checks

                        # ────────────────────────────────────────────────
                        # Existing: Check if any setting item was clicked
                        # ────────────────────────────────────────────────
                        for setting_key, rect in self.setting_rects.items():
                            # Create offset rect for hit detection
                            offset_rect = rect.copy()
                            offset_rect.y -= self.scroll_offset

                            if offset_rect.collidepoint(event.pos):
                                setting = self.settings[setting_key]

                                # ───────────────────────────────
                                # Handle slider click & drag start
                                # ───────────────────────────────
                                if setting["type"] == "slider":
                                    dragging_slider = setting_key
                                    adjusted_pos = (
                                        event.pos[0],
                                        event.pos[1] + self.scroll_offset,
                                    )
                                    self._handle_setting_click(
                                        setting_key, adjusted_pos, rect
                                    )
                                    settings_changed = True
                                    self._apply_settings()
                                    save_config_to_file()

                                # ───────────────────────────────
                                # Handle toggle click
                                # ───────────────────────────────
                                else:
                                    adjusted_pos = (
                                        event.pos[0],
                                        event.pos[1] + self.scroll_offset,
                                    )
                                    self._handle_setting_click(
                                        setting_key, adjusted_pos, rect
                                    )
                                    settings_changed = True
                                    self._apply_settings()
                                    save_config_to_file()

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

                        # Adjust mouse pos for scroll offset
                        adjusted_pos = (event.pos[0], event.pos[1] + self.scroll_offset)

                        # Update slider value based on new mouse position
                        self._handle_setting_click(dragging_slider, adjusted_pos, rect)

                        # Mark as changed and apply to Config
                        settings_changed = True
                        self._apply_settings()
                        save_config_to_file()

        # Menu closed, return whether any settings were changed
        if settings_changed:
            if save_config_to_file():
                print("[SettingsMenu] Configuration saved successfully.")
            else:
                print("[SettingsMenu] Warning: Could not save settings to config.json")

        return settings_changed

    def _draw_setting_item(
        self, setting_key: str, rect: pygame.Rect, mouse_pos: Tuple[int, int]
    ):
        setting = self.settings[setting_key]
        is_hover = rect.collidepoint(mouse_pos)

        bg_color = (60, 60, 60) if is_hover else (50, 50, 50)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, (80, 80, 80), rect, 1, border_radius=5)

        # Label
        label = self.label_font.render(setting["label"], True, (220, 220, 220))
        self.screen.blit(label, (rect.x + 15, rect.centery - label.get_height() // 2))

        # Control
        if setting["type"] == "toggle":
            self._draw_toggle(rect, setting["value"])

        elif setting["type"] == "slider":
            self._draw_slider(rect, setting)

        elif setting["type"] == "file_select":
            self._draw_file_path(rect, setting, mouse_pos)

    def _draw_toggle(self, rect: pygame.Rect, value: bool):
        """
        Render a toggle switch control (smaller size).

        Args:
            rect: pygame.Rect
                The parent setting item rectangle (for positioning)
            value: bool
                Current toggle state (True = on, False = off)
        """
        # Toggle Dimensions & Position (smaller)
        toggle_width = 48
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
        Render a slider control with draggable handle (smaller size).

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
        # Slider Dimensions & Position (smaller)
        slider_width = 140

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

    def _draw_file_path(
        self, rect: pygame.Rect, setting: dict, mouse_pos: Tuple[int, int]
    ):
        """Draw path + Browse button without overlap or overflow"""
        if "uci_engine_path" not in self.browse_buttons:
            return

        original_btn_rect = self.browse_buttons["uci_engine_path"]
        drawn_btn_rect = original_btn_rect.copy()
        drawn_btn_rect.y -= self.scroll_offset

        # Skip if off-screen
        content_top = self.menu_y + 90
        content_bottom = content_top + (self.menu_height - 170)
        content_right = self.menu_x + self.menu_width - 25
        if (
            drawn_btn_rect.bottom < content_top
            or drawn_btn_rect.top > content_bottom
            or drawn_btn_rect.right > content_right
        ):
            return

        # ── Path text ───────────────────────────────────────────────────────────
        full_path = setting["value"] or "Not selected"

        # Calculate available space **first** (always needed)
        label_width = self.label_font.size("UCI Engine Path")[0]
        label_end_x = rect.x + 15 + label_width + 25  # after label + reasonable gap

        max_path_px = drawn_btn_rect.left - label_end_x - 15  # gap before button

        # Now shorten path
        if full_path == "Not selected":
            display_path = "Not selected"
        else:
            # Try full path first
            display_path = full_path
            if self.label_font.size(display_path)[0] <= max_path_px:
                pass  # fits → show full

            else:
                # Keep full filename + as much parent path as possible
                filename = os.path.basename(full_path)
                parent_path = os.path.dirname(full_path)
                parts = parent_path.split(os.sep)

                current_path = filename
                for part in reversed(parts):
                    if not part:
                        continue
                    test_path = part + os.sep + current_path
                    test_px = self.label_font.size("..." + test_path)[0]

                    if test_px <= max_path_px:
                        current_path = test_path
                    else:
                        break

                display_path = "..." + current_path

                # Final safety truncation if still too long
                if self.label_font.size(display_path)[0] > max_path_px:
                    max_chars = int(max_path_px / 9) - 3
                    display_path = "..." + display_path[-max_chars:]

        path_surf = self.label_font.render(display_path, True, (180, 180, 180))
        path_x = label_end_x
        path_y = rect.centery - path_surf.get_height() // 2

        if path_x < rect.x:
            path_x = rect.x + 15

        self.screen.blit(path_surf, (path_x, path_y))

        # ── Browse button ───────────────────────────────────────────────────────
        is_hover = drawn_btn_rect.collidepoint(mouse_pos)

        btn_color = (110, 110, 110) if is_hover else (90, 90, 90)
        pygame.draw.rect(self.screen, btn_color, drawn_btn_rect, border_radius=5)
        pygame.draw.rect(
            self.screen, (140, 140, 140), drawn_btn_rect, 1, border_radius=5
        )

        btn_text = self.button_font.render("Browse", True, (255, 255, 255))
        text_x = drawn_btn_rect.centerx - btn_text.get_width() // 2
        text_y = drawn_btn_rect.centery - btn_text.get_height() // 2
        self.screen.blit(btn_text, (text_x, text_y))

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
            slider_width = 140
            slider_x = rect.right - slider_width - 15

            # Extract click X coordinate
            click_x = pos[0]

            # Calculate relative position within slider (0 to slider_width)
            # Clamp to slider bounds (can't go outside track)
            relative_x = max(0, min(slider_width, click_x - slider_x))

            # Normalize to 0.0-1.0 range
            # relative_x=0 → normalized=0.0 (min value)
            # relative_x=140 → normalized=1.0 (max value)
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

    def _select_engine_file(self):
        """Open file dialog to select UCI engine executable"""
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the empty Tk window
            root.attributes("-topmost", True)  # Keep dialog above pygame window

            filepath = filedialog.askopenfilename(
                title="Select UCI Engine Executable",
                initialdir=os.path.expanduser("~"),  # Start in home folder
                filetypes=[
                    (
                        "Executables",
                        "*.exe *.bin *",
                    ),  # Windows + common engine extensions
                    ("All files", "*.*"),
                ],
            )

            if filepath:  # User selected a file
                self.settings["uci_engine_path"]["value"] = filepath.strip()

                # Nice UX: auto-enable UCI engine if path is selected and it was off
                if not self.settings["use_uci_engine"]["value"]:
                    self.settings["use_uci_engine"]["value"] = True

                # Optional: print for debugging
                print(f"Selected engine: {filepath}")

        except Exception as e:
            print(f"Error opening file dialog: {e}")

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
        setattr(Config, "ENABLE_PREMOVE", self.settings["enable_premove"]["value"])
        setattr(Config, "SHOW_FPS", self.settings["show_fps"]["value"])
        setattr(Config, "USE_UCI_ENGINE", self.settings["use_uci_engine"]["value"])
        setattr(Config, "UCI_ENGINE_PATH", self.settings["uci_engine_path"]["value"])
        setattr(
            Config, "ENGINE_TIME_LIMIT", self.settings["engine_time_limit"]["value"]
        )
        setattr(
            Config, "ENGINE_SKILL_LEVEL", self.settings["engine_skill_level"]["value"]
        )
        depth_val = self.settings["engine_max_depth"]["value"]
        setattr(Config, "ENGINE_MAX_DEPTH", depth_val if depth_val > 0 else None)
        print(
            "[SettingsMenu] Settings applied. Restart the application for engine changes to take effect."
        )
