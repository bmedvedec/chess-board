"""
Player Clock Display
-------------------
Compact clock display for a single player in the chess application.

This module provides a streamlined clock component designed to fit next to
the captured pieces display. Each player gets their own independent clock.
"""

import pygame
import time
from typing import Optional, Tuple
from gui.colors import Colors


class PlayerClock:
    """
    Compact clock display for a single chess player.

    Designed to fit in a horizontal 50px tall strip next to captured pieces.
    Shows player name and remaining time with color-coded urgency indicators.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        player_name: str,
        player_color: bool,
        time_control: Optional[int] = None,
    ):
        """
        Initialize player clock with position and time control.

        Args:
            screen: pygame.Surface for rendering
            x, y: Top-left corner position
            width, height: Clock dimensions (typically width=~240, height=50)
            player_name: Display name ("White" or "Black")
            player_color: chess.WHITE or chess.BLACK
            time_control: Starting time in seconds (None = unlimited)
        """
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.player_name = player_name
        self.player_color = player_color
        self.time_control = time_control

        # Fonts
        self.label_font = pygame.font.SysFont("Arial", 11, bold=True)
        self.time_font = pygame.font.SysFont("Courier New", 22, bold=True)

        # Time tracking
        self.time_remaining = time_control
        self.is_active = False  # Is this player's clock running?
        self.last_update_time = None
        self.paused = True

    def start(self):
        """Start the clock (unpause)."""
        self.paused = False
        self.last_update_time = time.time()

    def pause(self):
        """Pause the clock."""
        if not self.paused:
            self.update()  # Update time before pausing
            self.paused = True

    def resume(self):
        """Resume the clock after pause."""
        if self.paused:
            self.last_update_time = time.time()
            self.paused = False

    def activate(self):
        """Activate this player's clock (their turn to move)."""
        self.is_active = True
        self.last_update_time = time.time()

    def deactivate(self):
        """Deactivate this player's clock (not their turn)."""
        if self.is_active:
            self.update()  # Save time before deactivating
            self.is_active = False

    def update(self):
        """Update time remaining if clock is active and not paused."""
        if self.paused or not self.is_active or self.time_remaining is None:
            return

        if self.last_update_time is None:
            self.last_update_time = time.time()
            return

        current_time = time.time()
        elapsed = current_time - self.last_update_time
        self.last_update_time = current_time

        # Deduct time, clamp to 0
        self.time_remaining = max(0, self.time_remaining - elapsed)

    def draw(self):
        """Render the player clock."""
        # Update time if active
        if not self.paused:
            self.update()

        # Background color based on active state
        if self.is_active and not self.paused:
            bg_color = (60, 60, 80)  # Highlighted when active
        else:
            bg_color = (40, 40, 40)  # Dark gray when inactive

        # Create rectangle
        rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Draw background
        pygame.draw.rect(self.screen, bg_color, rect)

        # Draw border (thicker if active)
        border_width = 2 if self.is_active else 1
        pygame.draw.rect(self.screen, Colors.BORDER, rect, border_width)

        # Draw player name label (small, top-left)
        name_color = (255, 255, 255) if self.player_color else (150, 150, 150)
        name_surface = self.label_font.render(self.player_name, True, name_color)
        name_rect = name_surface.get_rect(x=self.x + 8, y=self.y + 4)
        self.screen.blit(name_surface, name_rect)

        # Draw time
        if self.time_remaining is None:
            # Unlimited time
            time_str = "∞"
            time_color = (255, 255, 255)
        else:
            # Format time as MM:SS
            minutes = int(self.time_remaining) // 60
            seconds = int(self.time_remaining) % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            # Color based on urgency
            if self.time_remaining < 60:
                time_color = (255, 100, 100)  # Red - critical
            elif self.time_remaining < 300:
                time_color = (255, 200, 100)  # Orange - warning
            else:
                time_color = (255, 255, 255)  # White - normal

        # Render time (large, centered)
        time_surface = self.time_font.render(time_str, True, time_color)
        time_rect = time_surface.get_rect(
            centerx=self.x + self.width // 2, y=self.y + 22  # Below player name
        )
        self.screen.blit(time_surface, time_rect)

    def is_time_expired(self) -> bool:
        """Check if time has run out."""
        if self.time_control is None:
            return False
        return self.time_remaining is not None and self.time_remaining <= 0

    def reset(self, time_control: Optional[int] = None):
        """Reset clock to initial state."""
        if time_control is not None:
            self.time_control = time_control
        self.time_remaining = self.time_control
        self.is_active = False
        self.last_update_time = None
        self.paused = True

    def get_time_remaining(self) -> Optional[float]:
        """Get current time remaining in seconds."""
        return self.time_remaining
