"""
Game Clock Display
------------------
Manages and displays game timing with support for chess clocks and time controls.
"""

import pygame
import time
from typing import Optional, Tuple
from gui.colors import Colors


class GameClock:
    """
    Complete game timing system with dual-mode operation.

    This class manages all game timing functionality, supporting both a simple
    elapsed game timer and competitive chess clocks with per-player time controls.
    It handles time tracking, pause/resume, turn switching, and visual display.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        width: int,
        use_chess_clock: bool = False,
        time_control: Optional[int] = None,
    ):
        """
        Initialize game clock with display mode and time control settings.

        Creates a clock instance ready to track and display game time. Sets up
        fonts, initializes timing state, and configures display mode.

        Args:
            screen (pygame.Surface): Main pygame display surface.
                Used for rendering clock display.

            x (int): X-coordinate of clock's top-left corner.
                Typical positioning: 850 (right sidebar).

            y (int): Y-coordinate of clock's top-left corner.
                Typical positioning: 50 (top of sidebar).

            width (int): Clock display width in pixels.
                Should match sidebar width, typically 200 pixels.

            use_chess_clock (bool, optional): Clock display mode.
                - False: Show simple elapsed game time (default)
                - True: Show per-player chess clocks with time controls
                Defaults to False.

            time_control (Optional[int], optional): Time per player in seconds.
                Only used when use_chess_clock=True.
                - None: Unlimited time
                - 180: 3 minutes (blitz chess)
                - 300: 5 minutes (blitz chess)
                - 600: 10 minutes (rapid chess)
                - 900: 15 minutes (rapid chess)
                Defaults to None (unlimited).
        """
        # Store display surface and positioning
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width

        # Store clock mode and time control settings
        self.use_chess_clock = use_chess_clock
        self.time_control = time_control

        # Title font for section headers ("Game Time", etc.)
        self.title_font = pygame.font.SysFont("Arial", 14, bold=True)

        # Large font for time display (clear, readable)
        self.time_font = pygame.font.SysFont("Courier New", 24, bold=True)

        # Small font for player labels ("White", "Black")
        self.label_font = pygame.font.SysFont("Arial", 12)

        # Game start timestamp (None = not started)
        self.game_start_time = None

        # Remaining time for each player (seconds as float)
        self.white_time_remaining = time_control
        self.black_time_remaining = time_control

        # Currently active player (whose clock is running)
        self.active_color = None

        # Last update timestamp for incremental time tracking
        # Prevents time jumps when pausing/resuming
        self.last_update_time = None

        # Pause state (True = frozen, False = counting)
        self.paused = True

    def start_game(self):
        """
        Start the game clock and begin time tracking.

        Captures current timestamp as game start time, initializes timing state,
        and unpauses the clock.
        """
        # Record game start time for total elapsed calculation
        self.game_start_time = time.time()

        # Record update time for incremental time tracking
        self.last_update_time = time.time()

        # Unpause clock to begin counting
        self.paused = False

        print("[GameClock] Game started")

    def pause(self):
        """
        Pause the clock, freezing all time counting.

        Stops time from advancing for both players. Updates current player's
        time before pausing to ensure accuracy.
        """
        # Only pause if currently unpaused
        if not self.paused:
            # Update times before pausing to save current state
            # Ensures no time is lost or duplicated
            self.update()

            self.paused = True

    def resume(self):
        """
        Resume the clock after being paused.

        Restarts time counting from current moment. Resets last_update_time
        to prevent time jump from accumulated pause duration.
        """
        # Only resume if currently paused
        if self.paused:
            # Reset last update time to NOW
            # Prevents time jump from pause duration
            self.last_update_time = time.time()

            self.paused = False

    def switch_turn(self, new_active_color):
        """
        Switch which player's clock is running.

        Called after each move to activate the next player's clock. Updates
        current player's time before switching to ensure accurate time tracking.

        Args:
            new_active_color: Player to activate (chess.WHITE or chess.BLACK).
                The specified player's clock will start counting down.
        """
        if self.use_chess_clock:
            # Update current player's time before switching
            # Deducts elapsed time since last update
            self.update()

            # Activate new player's clock
            self.active_color = new_active_color

            # Reset update timestamp to prevent time jump
            self.last_update_time = time.time()

    def update(self):
        """
        Update active player's time by deducting elapsed duration.

        Calculates time elapsed since last update and subtracts from active
        player's remaining time.
        """
        # Early exit if paused or in game time mode
        if self.paused or not self.use_chess_clock:
            return

        # Early exit if no active player or timing not initialized
        if self.active_color is None or self.last_update_time is None:
            return

        # Get current timestamp
        current_time = time.time()

        # Calculate time elapsed since last update (in seconds)
        elapsed = current_time - self.last_update_time

        # Update last_update_time for next cycle
        # Prevents duplicate time deduction
        self.last_update_time = current_time

        import chess

        # Deduct time from White or Black based on active_color
        if self.active_color == chess.WHITE:
            # White's clock is running
            if self.white_time_remaining is not None:
                # Deduct elapsed time, clamp to 0 minimum
                # max() prevents negative time
                self.white_time_remaining = max(0, self.white_time_remaining - elapsed)
        else:
            # Black's clock is running
            if self.black_time_remaining is not None:
                # Deduct elapsed time, clamp to 0 minimum
                self.black_time_remaining = max(0, self.black_time_remaining - elapsed)

    def draw(self, current_turn=None):
        """
        Render the clock display based on current mode.

        Args:
            current_turn (Optional[int]): Current player's turn.
                - chess.WHITE or chess.BLACK for chess clock mode
                - None or ignored for game time mode
                Used to highlight active player's clock.
        """
        # Route to appropriate draw method based on mode
        if self.use_chess_clock:
            # Draw per-player chess clocks with time controls
            self._draw_chess_clocks(current_turn)
        else:
            # Draw simple elapsed game time
            self._draw_game_time()

    def _draw_game_time(self):
        """
        Draw simple elapsed game time display (game time mode).

        Renders a single clock showing total time elapsed since game start.
        Displays in MM:SS format (or HH:MM:SS if over 1 hour). Time freezes
        while paused to preserve pause state.
        """
        # Calculate time elapsed since game start
        if self.game_start_time is None:
            # Game hasn't started yet
            elapsed_seconds = 0
        else:
            if self.paused:
                # While paused, use last recorded elapsed time
                elapsed_seconds = getattr(self, "_last_elapsed", 0)
            else:
                # Game running: calculate current elapsed time
                elapsed_seconds = int(time.time() - self.game_start_time)

                # Cache current elapsed time for pause state
                self._last_elapsed = elapsed_seconds

        # Break down seconds into hours, minutes, seconds
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        # Format based on duration
        if hours > 0:
            # Long game: show hours (HH:MM:SS)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            # Short game: show only minutes (MM:SS)
            time_str = f"{minutes:02d}:{seconds:02d}"

        # Create background rectangle (50px height for single display)
        bg_rect = pygame.Rect(self.x, self.y, self.width, 50)

        # Fill with dark gray background
        pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)

        # Draw border (1px thin border)
        pygame.draw.rect(self.screen, Colors.BORDER, bg_rect, 1)

        # Render "Game Time" title
        label = self.title_font.render("Game Time", True, Colors.COORDINATE_TEXT)

        # Center horizontally at top of display
        label_rect = label.get_rect(centerx=self.x + self.width // 2, y=self.y + 5)

        # Draw title
        self.screen.blit(label, label_rect)

        # Render time string in large font with white color
        time_surface = self.time_font.render(time_str, True, (255, 255, 255))

        # Center horizontally below title
        time_rect = time_surface.get_rect(
            centerx=self.x + self.width // 2, y=self.y + 25
        )

        # Draw time
        self.screen.blit(time_surface, time_rect)

    def _draw_chess_clocks(self, current_turn):
        """
        Draw per-player chess clocks with time controls (chess clock mode).

        Renders two separate clock sections stacked vertically, one for White
        and one for Black. The active player's clock is highlighted and their
        time counts down. Low time triggers color warnings.

        Args:
            current_turn: Current player's turn (chess.WHITE or chess.BLACK).
                Used to determine which clock to highlight as active.
        """
        import chess

        # Update active player's time if not paused
        if not self.paused:
            self.update()

        # Height of each player's clock section
        section_height = 45

        # Total height for both sections plus gap
        total_height = section_height * 2 + 10

        # Determine if White's clock is currently active
        is_white_active = current_turn == chess.WHITE

        # Draw White's clock section at top position
        self._draw_clock_section(
            "White",
            self.white_time_remaining,
            self.y,
            is_white_active,
            (255, 255, 255),
        )

        # Determine if Black's clock is currently active
        is_black_active = current_turn == chess.BLACK

        # Draw Black's clock section below White's with 10px gap
        self._draw_clock_section(
            "Black",
            self.black_time_remaining,
            self.y + section_height + 10,
            is_black_active,
            (100, 100, 100),
        )

    def _draw_clock_section(
        self,
        player_name: str,
        time_remaining: Optional[float],
        y_pos: int,
        is_active: bool,
        text_color: Tuple[int, int, int],
    ):
        """
        Draw a single player's clock section with time and status indicators.

        Renders one player's clock display with background, player name, time
        remaining, and visual feedback for active state and low time warnings.

        Args:
            player_name (str): Player identifier ("White" or "Black").
                Displayed in top-left of section.

            time_remaining (Optional[float]): Time left in seconds.
                - None: Unlimited time (shows ∞ symbol)
                - Float: Remaining seconds (shown as MM:SS)

            y_pos (int): Vertical position for top of this section.
                Used to stack White and Black sections vertically.

            is_active (bool): Whether this player's clock is currently running.
                - True: Blue-gray background, thick border
                - False: Dark gray background, thin border

            text_color (Tuple[int, int, int]): RGB color for player name label.
                Typically (255, 255, 255) for White, (100, 100, 100) for Black.
        """
        # Choose background color based on active state
        if is_active and not self.paused:
            # Active player: highlighted blue-gray background
            bg_color = (60, 60, 80)
        else:
            # Inactive player or paused: dark gray background
            bg_color = (40, 40, 40)

        # Create rectangle for this clock section (45px height)
        bg_rect = pygame.Rect(self.x, y_pos, self.width, 45)

        # Fill background with selected color
        pygame.draw.rect(self.screen, bg_color, bg_rect)

        # Draw border (thicker if active for visual emphasis)
        pygame.draw.rect(self.screen, Colors.BORDER, bg_rect, 2 if is_active else 1)

        # Render player name ("White" or "Black")
        name_surface = self.label_font.render(player_name, True, text_color)

        # Position in top-left with padding
        name_rect = name_surface.get_rect(x=self.x + 10, y=y_pos + 5)

        # Draw player name
        self.screen.blit(name_surface, name_rect)

        # Handle unlimited time vs. timed game
        if time_remaining is None:
            # Unlimited time: display infinity symbol
            time_str = "∞"
            time_color = (255, 255, 255)  # White
        else:
            # Calculate minutes and seconds from total seconds
            minutes = int(time_remaining) // 60
            seconds = int(time_remaining) % 60

            # Format as MM:SS (e.g., "05:30")
            time_str = f"{minutes:02d}:{seconds:02d}"

            # Select color based on urgency
            if time_remaining < 60:
                # Critical: less than 1 minute left
                time_color = (255, 100, 100)  # Red
            elif time_remaining < 300:
                # Warning: less than 5 minutes left
                time_color = (255, 200, 100)  # Orange
            else:
                # Normal: plenty of time
                time_color = (255, 255, 255)  # White

        # Render time string in large font with warning color
        time_surface = self.time_font.render(time_str, True, time_color)

        # Center horizontally, position below player name
        time_rect = time_surface.get_rect(
            centerx=self.x + self.width // 2, y=y_pos + 20
        )

        # Draw time
        self.screen.blit(time_surface, time_rect)

    def is_time_expired(self) -> Optional[bool]:
        """
        Check if either player has run out of time.

        Determines if time expiration has occurred in chess clock mode. Used
        to detect when a player loses on time. Only applies when time control
        is enabled.

        Returns:
            Optional[int]: Player who ran out of time, or None.
                - chess.WHITE: White's time expired (Black wins on time)
                - chess.BLACK: Black's time expired (White wins on time)
                - None: No time expiration (game continues)
        """
        # Early exit if not using chess clocks or no time control
        # Game time mode or unlimited time = no expiration possible
        if not self.use_chess_clock or self.time_control is None:
            return None

        import chess

        # Check if White's time has expired
        if self.white_time_remaining is not None and self.white_time_remaining <= 0:
            return chess.WHITE  # White lost on time

        # Check if Black's time has expired
        if self.black_time_remaining is not None and self.black_time_remaining <= 0:
            return chess.BLACK  # Black lost on time

        # Neither player has expired time
        return None

    def reset(self):
        """
        Reset clock to initial state for a new game.

        Clears all timing state and restores default values. Time limits are
        reset to configured time_control. Clock starts in paused state.
        """
        # Clear game start timestamp (game not started)
        self.game_start_time = None

        # Reset player times to configured time control
        self.white_time_remaining = self.time_control
        self.black_time_remaining = self.time_control

        # Clear active player (no clock running)
        self.active_color = None

        # Clear update timestamp
        self.last_update_time = None

        # Set to paused state (frozen until start_game())
        self.paused = True
