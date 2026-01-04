"""
Time Control Dialog
------------------
Modal dialog for selecting chess time control before game start.
"""

import pygame
from typing import Optional, Tuple
from gui.colors import Colors


class TimeControlDialog:
    """
    Modal dialog for selecting game time control.

    Features:
    - Custom time input at top (1-999 minutes)
    - 2-column layout for preset options
    - Common presets: 3, 5, 10, 15, 30 min + Unlimited
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize time control selection dialog.

        Args:
            screen: pygame.Surface for rendering
        """
        self.screen = screen

        # Dialog dimensions
        self.dialog_width = 600
        self.dialog_height = 500

        # Center on screen
        self.dialog_x = (screen.get_width() - self.dialog_width) // 2
        self.dialog_y = (screen.get_height() - self.dialog_height) // 2

        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.desc_font = pygame.font.SysFont("Arial", 14)
        self.input_font = pygame.font.SysFont("Arial", 20)

        # Custom input state
        self.custom_input = ""
        self.input_active = False

        # Custom input box
        self.input_box = pygame.Rect(
            self.dialog_x + 150,
            self.dialog_y + 90,
            120,
            40,
        )

        # "Start" button for custom input
        self.start_button = pygame.Rect(
            self.dialog_x + 280,
            self.dialog_y + 90,
            100,
            40,
        )

        # Time control preset options (seconds, display name, description)
        self.options = [
            (180, "3 min", "Blitz"),
            (300, "5 min", "Blitz"),
            (600, "10 min", "Rapid"),
            (900, "15 min", "Rapid"),
            (1800, "30 min", "Classical"),
            (None, "Unlimited", "No limit"),
        ]

        # Button dimensions for 2-column layout
        self.button_width = 240
        self.button_height = 50
        self.button_spacing = 15
        self.column_spacing = 20

        # Calculate button positions (2 columns)
        self.buttons = []
        start_y = self.dialog_y + 160

        for i, (seconds, name, desc) in enumerate(self.options):
            # Determine column (0 or 1)
            col = i % 2
            row = i // 2

            x = self.dialog_x + 40 + col * (self.button_width + self.column_spacing)
            y = start_y + row * (self.button_height + self.button_spacing)

            button_rect = pygame.Rect(x, y, self.button_width, self.button_height)
            self.buttons.append((button_rect, seconds, name, desc))

    def show(self) -> Optional[int]:
        """
        Display dialog and wait for user selection.

        Returns:
            Optional[int]: Selected time in seconds, or None for unlimited
        """
        # Create overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))

        running = True
        while running:
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
            title = self.title_font.render("Select Time Control", True, (255, 255, 255))
            title_rect = title.get_rect(
                centerx=self.dialog_x + self.dialog_width // 2,
                y=self.dialog_y + 20,
            )
            self.screen.blit(title, title_rect)

            # Draw separator
            pygame.draw.line(
                self.screen,
                Colors.BORDER,
                (self.dialog_x + 40, self.dialog_y + 65),
                (self.dialog_x + self.dialog_width - 40, self.dialog_y + 65),
                2,
            )

            # Draw "Custom:" label
            custom_label = self.desc_font.render(
                "Custom (minutes):", True, (200, 200, 200)
            )
            self.screen.blit(custom_label, (self.dialog_x + 40, self.dialog_y + 100))

            # Draw custom input box
            input_color = (100, 100, 120) if self.input_active else (60, 60, 60)
            pygame.draw.rect(self.screen, input_color, self.input_box)
            pygame.draw.rect(self.screen, Colors.BORDER, self.input_box, 2)

            # Draw input text
            input_display = self.custom_input if self.custom_input else "0"
            input_surface = self.input_font.render(input_display, True, (255, 255, 255))
            input_rect = input_surface.get_rect(center=self.input_box.center)
            self.screen.blit(input_surface, input_rect)

            # Draw "Start" button
            mouse_pos = pygame.mouse.get_pos()
            start_hover = self.start_button.collidepoint(mouse_pos)
            start_color = Colors.BUTTON_HOVER if start_hover else Colors.BUTTON_NORMAL

            pygame.draw.rect(
                self.screen, start_color, self.start_button, border_radius=5
            )
            pygame.draw.rect(
                self.screen, Colors.BORDER, self.start_button, 2, border_radius=5
            )

            start_text = self.button_font.render("Start", True, Colors.BUTTON_TEXT)
            start_text_rect = start_text.get_rect(center=self.start_button.center)
            self.screen.blit(start_text, start_text_rect)

            # Draw separator before presets
            pygame.draw.line(
                self.screen,
                Colors.BORDER,
                (self.dialog_x + 40, self.dialog_y + 145),
                (self.dialog_x + self.dialog_width - 40, self.dialog_y + 145),
                2,
            )

            # Draw preset buttons (2 columns)
            for button_rect, seconds, name, desc in self.buttons:
                is_hover = button_rect.collidepoint(mouse_pos)

                # Button color
                if is_hover:
                    bg_color = Colors.BUTTON_HOVER
                else:
                    bg_color = Colors.BUTTON_NORMAL

                # Draw button
                pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=5)
                pygame.draw.rect(
                    self.screen, Colors.BORDER, button_rect, 2, border_radius=5
                )

                # Draw button text (name)
                text = self.button_font.render(name, True, Colors.BUTTON_TEXT)
                text_rect = text.get_rect(
                    center=(button_rect.centerx, button_rect.centery - 8)
                )
                self.screen.blit(text, text_rect)

                # Draw description (smaller, below name)
                desc_surface = self.desc_font.render(desc, True, (180, 180, 180))
                desc_rect = desc_surface.get_rect(
                    center=(button_rect.centerx, button_rect.centery + 12)
                )
                self.screen.blit(desc_surface, desc_rect)

            # Update display
            pygame.display.flip()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None  # Default to unlimited

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None  # Unlimited

                    elif event.key == pygame.K_RETURN:
                        # Start with custom time
                        if self.custom_input:
                            try:
                                minutes = int(self.custom_input)
                                if 1 <= minutes <= 999:
                                    return minutes * 60
                            except ValueError:
                                pass
                        return None  # If invalid, unlimited

                    elif event.key == pygame.K_BACKSPACE:
                        # Remove last character
                        self.custom_input = self.custom_input[:-1]

                    elif event.unicode.isdigit():
                        # Add digit (max 3 digits)
                        if len(self.custom_input) < 3:
                            self.custom_input += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # Check if input box clicked
                        if self.input_box.collidepoint(event.pos):
                            self.input_active = True
                        else:
                            self.input_active = False

                        # Check if Start button clicked
                        if self.start_button.collidepoint(event.pos):
                            if self.custom_input:
                                try:
                                    minutes = int(self.custom_input)
                                    if 1 <= minutes <= 999:
                                        return minutes * 60
                                except ValueError:
                                    pass
                            return None  # If invalid or empty, unlimited

                        # Check which preset button was clicked
                        for button_rect, seconds, name, desc in self.buttons:
                            if button_rect.collidepoint(event.pos):
                                return seconds

        return None  # Default to unlimited
