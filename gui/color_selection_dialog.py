"""
Color Selection Dialog
----------------------
Modal dialog for selecting which color to play before game start.

This module provides a simple dialog that appears at game startup, allowing
the user to choose whether they want to play as White, Black, or have the
color randomly assigned.
"""

import pygame
import random
from gui.colors import Colors


class ColorSelectionDialog:
    """
    Modal dialog for selecting player color before game starts.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize color selection dialog with layout.

        Args:
            screen: pygame.Surface for rendering
        """
        self.screen = screen

        # Dialog dimensions
        self.dialog_width = 500
        self.dialog_height = 350

        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.desc_font = pygame.font.SysFont("Arial", 14)

        # Button dimensions
        self.button_width = 380
        self.button_height = 60
        self.button_spacing = 15

        print("[ColorSelectionDialog] Initialized")

    def _calculate_positions(self):
        """
        Calculate dialog and button positions based on current screen size.
        Called every frame to handle window resizing.
        """
        # Get current screen dimensions
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Center dialog on current screen
        self.dialog_x = (screen_width - self.dialog_width) // 2
        self.dialog_y = (screen_height - self.dialog_height) // 2

        # Calculate button positions (centered vertically)
        start_y = self.dialog_y + 100

        # White button
        self.white_button = pygame.Rect(
            self.dialog_x + (self.dialog_width - self.button_width) // 2,
            start_y,
            self.button_width,
            self.button_height,
        )

        # Black button
        self.black_button = pygame.Rect(
            self.dialog_x + (self.dialog_width - self.button_width) // 2,
            start_y + self.button_height + self.button_spacing,
            self.button_width,
            self.button_height,
        )

        # Random button
        self.random_button = pygame.Rect(
            self.dialog_x + (self.dialog_width - self.button_width) // 2,
            start_y + 2 * (self.button_height + self.button_spacing),
            self.button_width,
            self.button_height,
        )

    def show(self) -> str:
        """
        Display color selection dialog and wait for user choice.

        Blocks until user selects a color or closes the dialog.

        Returns:
            str: Selected color
                - "white": User chose to play as White
                - "black": User chose to play as Black
                - Will randomly return "white" or "black" if Random selected
        """
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))

        running = True
        while running:
            # -------------------- Rendering --------------------
            # Handle window resizing
            self._calculate_positions()

            # Draw overlay
            self.screen.blit(overlay, (0, 0))

            # Draw dialog background
            dialog_rect = pygame.Rect(
                self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height
            )
            pygame.draw.rect(self.screen, (45, 45, 45), dialog_rect, border_radius=10)
            pygame.draw.rect(
                self.screen, Colors.BORDER, dialog_rect, 3, border_radius=10
            )

            # Draw title
            title = self.title_font.render("Choose Your Color", True, (255, 255, 255))
            title_rect = title.get_rect(
                centerx=self.dialog_x + self.dialog_width // 2,
                y=self.dialog_y + 25,
            )
            self.screen.blit(title, title_rect)

            # Draw separator
            pygame.draw.line(
                self.screen,
                Colors.BORDER,
                (self.dialog_x + 40, self.dialog_y + 70),
                (self.dialog_x + self.dialog_width - 40, self.dialog_y + 70),
                2,
            )

            # Get mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()

            # Draw White button
            self._draw_button(
                self.white_button,
                "Play as White",
                "You move first",
                mouse_pos,
                (240, 240, 240),
            )

            # Draw Black button
            self._draw_button(
                self.black_button,
                "Play as Black",
                "Engine moves first",
                mouse_pos,
                (60, 60, 60),
            )

            # Draw Random button
            self._draw_button(
                self.random_button,
                "Random Color",
                "50/50 chance for each side",
                mouse_pos,
                (150, 150, 150),
            )

            # Update display
            pygame.display.flip()

            # -------------------- Event Handling --------------------

            for event in pygame.event.get():
                # Window close - default to white
                if event.type == pygame.QUIT:
                    return "white"

                # Keyboard shortcuts
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        return "white"
                    elif event.key == pygame.K_b:
                        return "black"
                    elif event.key == pygame.K_r:
                        # Random selection
                        return random.choice(["white", "black"])
                    elif event.key == pygame.K_ESCAPE:
                        # Default to white on escape
                        return "white"

                # Mouse click
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # Check which button was clicked
                        if self.white_button.collidepoint(event.pos):
                            return "white"
                        elif self.black_button.collidepoint(event.pos):
                            return "black"
                        elif self.random_button.collidepoint(event.pos):
                            # Random selection
                            color = random.choice(["white", "black"])
                            print(f"[ColorSelection] Random color selected: {color}")
                            return color

        # Fallback (should never reach)
        return "white"

    def _draw_button(
        self,
        rect: pygame.Rect,
        text: str,
        description: str,
        mouse_pos: tuple,
        accent_color: tuple,
    ):
        """
        Draw a color selection button with hover effect.

        Args:
            rect: Button rectangle
            text: Main button text (e.g., "Play as White")
            description: Subtitle text (e.g., "You move first")
            mouse_pos: Current mouse position for hover detection
            accent_color: RGB color for the accent bar on the left
        """
        # Check hover state
        is_hover = rect.collidepoint(mouse_pos)

        # Choose background color
        if is_hover:
            bg_color = (70, 70, 80)
        else:
            bg_color = (55, 55, 55)

        # Draw button background
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)

        # Draw border
        pygame.draw.rect(self.screen, Colors.BORDER, rect, 2, border_radius=5)

        # Draw colored accent bar on left side
        accent_rect = pygame.Rect(rect.x + 5, rect.y + 5, 8, rect.height - 10)
        pygame.draw.rect(self.screen, accent_color, accent_rect, border_radius=2)

        # Draw main text (button label)
        text_surface = self.button_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(x=rect.x + 30, centery=rect.centery - 10)
        self.screen.blit(text_surface, text_rect)

        # Draw description text (smaller, below main text)
        desc_surface = self.desc_font.render(description, True, (180, 180, 180))
        desc_rect = desc_surface.get_rect(x=rect.x + 30, centery=rect.centery + 12)
        self.screen.blit(desc_surface, desc_rect)

        # Draw keyboard shortcut hint in bottom-right of button
        if "White" in text:
            shortcut = "W"
        elif "Black" in text:
            shortcut = "B"
        else:
            shortcut = "R"

        shortcut_surface = self.desc_font.render(shortcut, True, (120, 120, 120))
        shortcut_rect = shortcut_surface.get_rect(
            right=rect.right - 15, centery=rect.centery
        )
        self.screen.blit(shortcut_surface, shortcut_rect)
