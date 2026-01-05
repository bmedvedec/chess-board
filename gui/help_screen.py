"""
Help Screen Module
-------------------
This module provides a comprehensive modal help screen overlay that displays
game instructions, keyboard shortcuts, visual indicators, and feature descriptions
for the chess application. It creates a professional, user-friendly interface for
players to learn controls and gameplay mechanics.
"""

import pygame
from gui.colors import Colors


class HelpScreen:
    """
    Modal help overlay displaying game instructions and keyboard shortcuts.

    This class creates and manages a professional help screen that overlays the
    game with comprehensive instructions, keyboard shortcuts, and feature
    descriptions. The help screen is modal (blocks game interaction), centered,
    and scrollable for long content.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize help screen with layout, fonts, and interactive elements.

        Creates a centered modal help panel with all necessary fonts, calculates
        positioning for centered display, sets up the close button, and initializes
        scrolling state. The help screen is ready to display immediately after
        initialization.

        Args:
            screen: pygame.Surface
                Main pygame display surface for rendering.
        """
        # Store display surface reference
        self.screen = screen

        # -------------------- Panel Dimensions and Positioning --------------------

        # Panel dimensions (fixed size)
        # 700×600 provides good balance between content space and screen coverage
        self.menu_width = 700
        self.menu_height = 600

        # Calculate centered position on screen
        # Uses current screen dimensions to center dynamically
        self.menu_x = (screen.get_width() - self.menu_width) // 2
        self.menu_y = (screen.get_height() - self.menu_height) // 2

        # -------------------- Font Setup --------------------

        # Title font for main heading "Help & Instructions"
        # Large, bold font for maximum prominence
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)

        # Section header font for category titles
        # Medium size, bold, distinguishes content sections
        self.section_font = pygame.font.SysFont("Arial", 20, bold=True)

        # Body text font for instructions and descriptions
        # Standard readable size for paragraphs and bullet points
        self.text_font = pygame.font.SysFont("Arial", 16)

        # Keyboard key font for shortcut displays
        # Monospaced Courier New for technical feel, looks like keyboard
        self.key_font = pygame.font.SysFont("Courier New", 16, bold=True)

        # Button text font for close button
        # Bold for clear call-to-action
        self.button_font = pygame.font.SysFont("Arial", 16, bold=True)

        # -------------------- Close Button Configuration --------------------

        # Button dimensions
        button_width = 120
        button_height = 40

        # Create close button rectangle
        # Centered horizontally at bottom of panel
        # 60px from bottom provides comfortable margin
        self.close_button = pygame.Rect(
            self.menu_x + (self.menu_width - button_width) // 2,  # Centered X
            self.menu_y + self.menu_height - 60,  # Near bottom
            button_width,
            button_height,
        )

        # -------------------- Scrolling State --------------------

        # Current scroll offset in pixels
        # 0 = content at top, positive = scrolled down
        self.scroll_offset = 0

        # Maximum scroll value (calculated dynamically based on content)
        # Prevents scrolling past end of content
        self.max_scroll = 0

    def show(self):
        """
        Display help screen as modal overlay and block until dismissed.

        This method enters a blocking event loop that displays the help screen
        and processes user input until the user closes it. While the help screen
        is shown, the main game is paused and all interaction is directed to
        the help screen.
        """
        # -------------------- Create Semi-Transparent Overlay --------------------

        # Create overlay surface matching screen dimensions
        # This darkens the game view underneath
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))

        # Set transparency (220 = mostly opaque, 0 = fully transparent, 255 = opaque)
        # High alpha value ensures good readability of help panel
        overlay.set_alpha(220)

        # Fill with black for darkening effect
        overlay.fill((0, 0, 0))

        # -------------------- Help Screen Display Loop --------------------

        # Modal loop flag
        running = True

        while running:
            # -------------------- Draw Overlay Background --------------------

            # Draw semi-transparent overlay over game
            # Darkens everything except help panel for focus
            self.screen.blit(overlay, (0, 0))

            # -------------------- Draw Help Panel Background --------------------

            # Create rectangle for help panel
            menu_rect = pygame.Rect(
                self.menu_x, self.menu_y, self.menu_width, self.menu_height
            )

            # Draw panel background with rounded corners
            # Dark gray background provides contrast for text
            pygame.draw.rect(self.screen, (45, 45, 45), menu_rect, border_radius=10)

            # Draw panel border with rounded corners
            # 3px border defines panel boundaries
            pygame.draw.rect(self.screen, Colors.BORDER, menu_rect, 3, border_radius=10)

            # -------------------- Draw Title --------------------

            # Render main title "Help & Instructions"
            title = self.title_font.render("Help & Instructions", True, (255, 255, 255))

            # Center title horizontally at top of panel
            title_rect = title.get_rect(
                centerx=self.menu_x + self.menu_width // 2, y=self.menu_y + 20
            )

            # Draw title
            self.screen.blit(title, title_rect)

            # -------------------- Draw Separator Line --------------------

            # Draw horizontal line below title
            # Separates title from content sections
            pygame.draw.line(
                self.screen,
                Colors.BORDER,
                (self.menu_x + 40, self.menu_y + 65),  # Start point (left)
                (
                    self.menu_x + self.menu_width - 40,
                    self.menu_y + 65,
                ),  # End point (right)
                2,  # Line thickness
            )

            # -------------------- Draw Help Content (Scrollable) --------------------

            # Draw all help sections with current scroll offset
            # Content may extend beyond visible area (handled by clipping)
            self._draw_content()

            # -------------------- Draw Close Button --------------------

            # Get current mouse position for hover detection
            mouse_pos = pygame.mouse.get_pos()

            # Check if mouse is hovering over close button
            is_hover = self.close_button.collidepoint(mouse_pos)

            # Select button color based on hover state
            # Provides visual feedback for interactivity
            button_color = Colors.BUTTON_HOVER if is_hover else Colors.BUTTON_NORMAL

            # Draw button background with rounded corners
            pygame.draw.rect(
                self.screen, button_color, self.close_button, border_radius=5
            )

            # Draw button border with rounded corners
            # 2px border defines button boundaries
            pygame.draw.rect(
                self.screen, Colors.BORDER, self.close_button, 2, border_radius=5
            )

            # Render "Close" button text
            close_text = self.button_font.render("Close", True, Colors.BUTTON_TEXT)

            # Center text within button
            close_rect = close_text.get_rect(center=self.close_button.center)

            # Draw button text
            self.screen.blit(close_text, close_rect)

            # -------------------- Update Display --------------------

            # Flip display buffers to show rendered frame
            pygame.display.flip()

            # -------------------- Event Processing --------------------

            # Process all pending events
            for event in pygame.event.get():
                # Window close event
                if event.type == pygame.QUIT:
                    return  # Exit help screen

                # Keyboard events
                elif event.type == pygame.KEYDOWN:
                    # ESC or H key: close help screen
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                        return  # Exit help screen

                # Mouse click events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Left mouse button
                    if event.button == 1:
                        # Check if close button was clicked
                        if self.close_button.collidepoint(event.pos):
                            return  # Exit help screen

                # Mouse wheel scrolling events
                elif event.type == pygame.MOUSEWHEEL:
                    # Scroll content up/down based on wheel direction
                    # event.y: positive = scroll up, negative = scroll down
                    # Multiply by 20 for reasonable scroll speed (20px per notch)
                    # Clamp to valid range: -max_scroll to 0
                    self.scroll_offset = max(
                        -self.max_scroll, min(0, self.scroll_offset + event.y * 20)
                    )

    def _draw_content(self):
        """
        Draw all help content sections with scrolling support.

        Renders the complete help content including all sections (How to Play,
        Keyboard Shortcuts, Visual Indicators, Game Controls, Features) with
        automatic layout and scrolling. Content is clipped to visible area to
        prevent overflow.

        The content is drawn with vertical spacing and organized into distinct
        sections. The scroll offset determines which portion of the content is
        visible. Max scroll is calculated based on total content height.
        """
        # -------------------- Content Start Position --------------------

        # Horizontal position for content (left-aligned with padding)
        content_x = self.menu_x + 50

        # Vertical position starts below separator, adjusted by scroll offset
        # scroll_offset is negative when scrolled down
        y = self.menu_y + 85 + self.scroll_offset

        # -------------------- Set Up Clipping Region --------------------

        # Create clipping rectangle to constrain content rendering
        # Prevents content from overflowing panel boundaries
        clip_rect = pygame.Rect(
            self.menu_x + 20,  # Left edge with padding
            self.menu_y + 70,  # Top edge below title/separator
            self.menu_width - 40,  # Width with padding on both sides
            self.menu_height - 150,  # Height leaving space for title and button
        )

        # Set clipping region - only this area will be rendered to
        # Content outside this rect is automatically clipped
        self.screen.set_clip(clip_rect)

        # -------------------- How to Play --------------------

        # Draw section header and get new Y position
        y = self._draw_section("How to Play", content_x, y)

        # Draw bullet points with instructions
        y = self._draw_text("• Click on a piece to select it", content_x + 20, y)
        y = self._draw_text("• Click on highlighted square to move", content_x + 20, y)
        y = self._draw_text("• Or drag and drop pieces to move", content_x + 20, y)
        y = self._draw_text(
            "• Legal moves are shown with dots/circles", content_x + 20, y
        )

        # Add vertical spacing before next section
        y += 15

        # -------------------- Keyboard Shortcuts --------------------

        # Draw section header
        y = self._draw_section("Keyboard Shortcuts", content_x, y)

        # Define all keyboard shortcuts with key and description
        shortcuts = [
            ("R", "Start new game / Reset"),
            ("U", "Undo last move (2 moves)"),
            ("←", "Previous move"),
            ("→", "Next move"),
            ("↑", "First move"),
            ("↓", "Last move"),
            ("S", "Open settings menu"),
            ("H", "Show this help screen"),
            ("ESC", "Close menu / Exit game"),
        ]

        # Draw each shortcut with visual key box
        for key, description in shortcuts:
            y = self._draw_shortcut(key, description, content_x + 20, y)

        # Add vertical spacing before next section
        y += 15

        # -------------------- Visual Indicators --------------------

        # Draw section header
        y = self._draw_section("Visual Indicators", content_x, y)

        # Draw bullet points explaining board highlights
        y = self._draw_text("• Yellow highlight = Last move", content_x + 20, y)
        y = self._draw_text("• Green highlight = Selected piece", content_x + 20, y)
        y = self._draw_text("• Red highlight = King in check", content_x + 20, y)
        y = self._draw_text("• Dots = Legal move destinations", content_x + 20, y)
        y = self._draw_text("• Circles = Capture moves", content_x + 20, y)

        # Add vertical spacing before next section
        y += 15

        # -------------------- Game Controls --------------------

        # Draw section header
        y = self._draw_section("Game Controls", content_x, y)

        # Draw bullet points explaining UI buttons
        y = self._draw_text(
            "• Save Game (PGN) - Export game to file", content_x + 20, y
        )
        y = self._draw_text("• Load Game (PGN) - Import saved game", content_x + 20, y)
        y = self._draw_text("• Resign - Forfeit the current game", content_x + 20, y)

        # Add vertical spacing before next section
        y += 15

        # -------------------- Features --------------------

        # Draw section header
        y = self._draw_section("Features", content_x, y)

        # Draw bullet points listing application features
        y = self._draw_text(
            "• Move animations (smooth piece sliding)", content_x + 20, y
        )
        y = self._draw_text("• Sound effects for moves and captures", content_x + 20, y)
        y = self._draw_text("• Captured pieces display", content_x + 20, y)
        y = self._draw_text("• Move history with scrolling", content_x + 20, y)
        y = self._draw_text("• Game timer (optional)", content_x + 20, y)

        # -------------------- Calculate Maximum Scroll --------------------

        # Calculate how far content extends beyond visible area
        # max_scroll = total_content_height - visible_height
        # Ensures scrolling doesn't go past end of content
        self.max_scroll = max(0, y - (self.menu_y + self.menu_height - 150))

        # -------------------- Clear Clipping Region --------------------

        # Remove clipping constraint
        # Allows other rendering (button, borders) to draw normally
        self.screen.set_clip(None)

    def _draw_section(self, title: str, x: int, y: int) -> int:
        """
        Draw a section header with styled formatting.

        Renders a section title in gold color with larger font to distinguish
        content categories. Automatically advances Y position for subsequent content.

        Args:
            title: str
                Section header text (e.g., "How to Play", "Keyboard Shortcuts")

            x: int
                Horizontal position for left edge of text

            y: int
                Vertical position for top of text

        Returns:
            int
                Updated Y position after this section header (y + 30)
        """
        # Render section title in gold color (255, 200, 100)
        # Gold color provides visual distinction from body text
        text = self.section_font.render(title, True, (255, 200, 100))

        # Draw section header at specified position
        self.screen.blit(text, (x, y))

        # Return new Y position below header (30px spacing)
        # Provides space for section content
        return y + 30

    def _draw_text(self, text: str, x: int, y: int) -> int:
        """
        Draw regular body text line.

        Renders a single line of help text in light gray color. Used for
        bullet points, instructions, and descriptions. Automatically advances
        Y position for next line.

        Args:
            text: str
                Text content to render (e.g., "• Click on a piece to select it")

            x: int
                Horizontal position for left edge of text

            y: int
                Vertical position for top of text

        Returns:
            int
                Updated Y position after this text line (y + 22)
                Ready for drawing next line below

        """
        # Render text in light gray (220, 220, 220)
        # Light color provides good contrast against dark background
        surface = self.text_font.render(text, True, (220, 220, 220))

        # Draw text at specified position
        self.screen.blit(surface, (x, y))

        # Return new Y position below text (22px line height)
        # Spacing appropriate for 16pt font
        return y + 22

    def _draw_shortcut(self, key: str, description: str, x: int, y: int) -> int:
        """
        Draw keyboard shortcut with visual key indicator and description.

        Renders a keyboard shortcut entry with a styled key box (looks like a
        keyboard key) followed by the description text. The key box has rounded
        corners, a background, and border to resemble a physical key.

        Args:
            key: str
                Key label to display in box (e.g., "R", "ESC", "U")
                Short key names fit best (1-3 characters)

            description: str
                Description of what the key does (e.g., "Start new game / Reset")

            x: int
                Horizontal position for left edge of key box

            y: int
                Vertical position for top of key box

        Returns:
            int
                Updated Y position after this shortcut line (y + 28)
                Ready for drawing next shortcut below
        """
        # -------------------- Draw Key Box --------------------

        # Render key text in white with monospace font
        # Courier New gives technical, keyboard-like appearance
        key_surface = self.key_font.render(key, True, (255, 255, 255))

        # Calculate key box width based on text width + padding
        # 16px padding (8px on each side) ensures text isn't cramped
        key_width = key_surface.get_width() + 16

        # Create rectangle for key box
        # Fixed height of 24px works well for 16pt font
        key_rect = pygame.Rect(x, y, key_width, 24)

        # Draw key box background (dark gray)
        # Rounded corners (radius=4) make it look like physical key
        pygame.draw.rect(self.screen, (70, 70, 70), key_rect, border_radius=4)

        # Draw key box border (medium gray, 1px)
        # Defines key boundaries and adds depth
        pygame.draw.rect(self.screen, (120, 120, 120), key_rect, 1, border_radius=4)

        # Center key text within box
        key_text_rect = key_surface.get_rect(center=key_rect.center)

        # Draw key text
        self.screen.blit(key_surface, key_text_rect)

        # -------------------- Draw Description Text --------------------

        # Render description in light gray
        # Same color as regular body text for consistency
        desc_surface = self.text_font.render(description, True, (220, 220, 220))

        # Position description to right of key box
        # 15px gap between key box and text
        # +2px vertical adjustment aligns text baseline with key
        self.screen.blit(desc_surface, (x + key_width + 15, y + 2))

        # -------------------- Return Updated Y Position --------------------

        # Return new Y position below shortcut (28px spacing)
        # Slightly more spacing than regular text for visual separation
        return y + 28
