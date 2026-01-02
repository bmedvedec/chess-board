"""
Sound Manager
-------------
Manages sound effects for chess moves and game events with automatic fallback.

This module provides a comprehensive audio feedback system for the chess application.
It handles loading sound files, generating synthesized fallback sounds, and playing
appropriate audio for different game events (moves, captures, check, castling, etc.).
"""

import pygame
import os
from utils.config import Config


class SoundManager:
    """
    Manages game sound effects with file loading and synthesized fallback.

    This class provides a complete audio feedback system for chess game events.
    It automatically handles pygame mixer initialization, loads sound files from
    the configured directory, and falls back to synthesized sounds if files are
    unavailable.
    """

    def __init__(self):
        """
        Initialize sound manager with pygame mixer and load all sounds.

        Raises:
            No exceptions raised - all errors are caught and logged.
            Failed initialization results in self.enabled = False.
        """
        self.enabled = Config.ENABLE_SOUNDS
        self.volume = Config.SOUND_VOLUME

        # Initialize pygame mixer if sounds are enabled
        if self.enabled:
            try:
                # Initialize audio system with default settings
                pygame.mixer.init()
                print("[SoundManager] Initialized successfully")
            except pygame.error as e:
                # If audio init fails (no sound card, etc.), disable sounds
                print(f"[SoundManager] Failed to initialize: {e}")
                self.enabled = False

        # Create empty sound effects dictionary
        self.sounds = {}

        # Load sound files if enabled
        if self.enabled:
            self._load_sounds()

    def _load_sounds(self):
        """
        Load all sound effect files from configured directory.

        This method attempts to load WAV files for each game event from the
        directory specified by Config.SOUNDS_DIR.
        """
        # Get sounds directory from configuration
        sound_dir = Config.SOUNDS_DIR

        # Define mapping from event names to WAV filenames
        # Keys match the event types used throughout the application
        sound_files = {
            "move": "move.wav",
            "capture": "capture.wav",
            "check": "check.wav",
            "castle": "castle.wav",
            "promote": "promote.wav",
            "game_start": "game-start.wav",
            "game_end": "game-end.wav",
            "illegal": "illegal.wav",
        }

        # Iterate through each sound file and attempt to load
        for sound_name, filename in sound_files.items():
            # Build full path to sound file
            filepath = os.path.join(sound_dir, filename)

            try:
                # Check if file exists before attempting load
                if os.path.exists(filepath):
                    # Load WAV file as pygame Sound object
                    sound = pygame.mixer.Sound(filepath)

                    # Apply configured volume level
                    sound.set_volume(self.volume)

                    # Store in sounds dictionary
                    self.sounds[sound_name] = sound

                    print(f"[SoundManager] Loaded: {filename}")
                else:
                    # File not found - store None placeholder
                    self.sounds[sound_name] = None

            except pygame.error as e:
                # Load failed (corrupt file, wrong format, etc.)
                print(f"[SoundManager] Failed to load {filename}: {e}")
                self.sounds[sound_name] = None

        # Check if any sounds successfully loaded
        if not any(self.sounds.values()):
            # No files loaded - generate programmatic sounds
            print("[SoundManager] No sound files found, using synthesized sounds")
            self._create_synthesized_sounds()

    def _create_synthesized_sounds(self):
        """
        Create simple synthesized sounds if no audio files are available.

        This method generates beep sounds programmatically using NumPy to create
        sine wave audio. Each game event gets a unique frequency and duration to
        make them distinguishable. Synthesized sounds use envelope shaping (fade
        in/out) to avoid clicking artifacts.

        Raises:
            Catches all exceptions and prints error message.
            If synthesis fails, sounds remain None (silent).
        """
        try:
            # Standard move sound: 440 Hz (A4), 100ms, moderate volume
            self.sounds["move"] = self._generate_beep(440, 100, 0.3)

            # Capture sound: 330 Hz (E4), 150ms, slightly louder
            self.sounds["capture"] = self._generate_beep(330, 150, 0.4)

            # Check sound: 880 Hz (A5), 120ms, loud
            self.sounds["check"] = self._generate_beep(880, 120, 0.5)

            # Castle sound: 523 Hz (C5), 150ms, moderate volume
            self.sounds["castle"] = self._generate_beep(523, 150, 0.35)

            # Promotion sound: 1047 Hz (C6), 120ms, moderate-loud
            self.sounds["promote"] = self._generate_beep(1047, 120, 0.4)

            # Game start sound: 523 Hz (C5), 100ms, moderate volume
            self.sounds["game_start"] = self._generate_beep(523, 100, 0.3)

            # Game end sound: 392 Hz (G4), 200ms, moderate volume
            self.sounds["game_end"] = self._generate_beep(392, 200, 0.35)

            # Illegal move sound: 220 Hz (A3), 80ms, quiet
            self.sounds["illegal"] = self._generate_beep(220, 80, 0.25)

            print("[SoundManager] Created synthesized sounds")

        except Exception as e:
            # If NumPy unavailable or synthesis fails
            print(f"[SoundManager] Failed to create synthesized sounds: {e}")

    def _generate_beep(
        self, frequency: int, duration_ms: int, volume: float
    ) -> pygame.mixer.Sound:
        """
        Generate a simple beep sound using sine wave synthesis.

        This method creates a pure tone (sine wave) at the specified frequency
        with fade-in/fade-out envelope to prevent clicking artifacts. The sound
        is generated as 16-bit PCM stereo audio suitable for pygame playback.

        Args:
            frequency (int): Sound frequency in Hertz (Hz).
                Typical range: 220-1047 Hz for musical notes.
                Lower = deeper, higher = brighter.
                Example: 440 Hz is standard A4 tuning note.

            duration_ms (int): Sound duration in milliseconds.
                Typical range: 80-200 ms for game sound effects.
                Shorter = quicker, snappier sounds.
                Longer = more noticeable, emphasized sounds.

            volume (float): Sound amplitude multiplier (0.0 to 1.0).
                0.0 = silent, 1.0 = maximum amplitude.
                Typical range: 0.25-0.5 to avoid clipping.

        Returns:
            pygame.mixer.Sound: Playable sound object with synthesized beep.
                Can be played with .play() method.
                Already in stereo 16-bit PCM format.
        """
        import numpy as np

        # Sample rate: 22050 Hz (22.05 kHz)
        # Standard for game audio - half of CD quality (44.1 kHz)
        sample_rate = 22050

        # Calculate total number of samples needed
        n_samples = int(sample_rate * duration_ms / 1000)

        # Create time array from 0 to duration (in seconds)
        t = np.linspace(0, duration_ms / 1000, n_samples, False)

        # Generate sine wave using formula: sin(2π * f * t)
        wave = np.sin(frequency * t * 2 * np.pi)

        # Create envelope (amplitude envelope over time)
        # Start as array of all 1.0 (full amplitude)
        envelope = np.ones(n_samples)

        # Calculate fade length (10% of total duration)
        # Ensures smooth transitions without clicks
        fade_samples = int(0.1 * n_samples)

        # Create fade-in ramp (0.0 → 1.0 over first 10%)
        # Linear ramp prevents clicking at sound start
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)

        # Create fade-out ramp (1.0 → 0.0 over last 10%)
        # Linear ramp prevents clicking at sound end
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

        # Apply envelope to wave by element-wise multiplication
        # Shapes the amplitude over time
        wave = wave * envelope

        # Scale wave to 16-bit range and apply volume
        wave = (wave * 32767 * volume).astype(np.int16)

        # Convert mono to stereo by duplicating channel
        stereo_wave = np.column_stack((wave, wave))

        # Convert NumPy array to pygame Sound object
        sound = pygame.sndarray.make_sound(stereo_wave)

        return sound

    def play_move_sound(self, is_capture: bool = False, is_check: bool = False):
        """
        Play appropriate sound for a move based on move type.

        Sound Priority:
        ---------------
        1. Check (highest) - if is_check=True
        2. Capture (medium) - if is_capture=True and is_check=False
        3. Move (default) - if both False

        Args:
            is_capture (bool, optional): True if move captured opponent piece.
                Plays lower-pitched "capture" sound.
                Defaults to False.

            is_check (bool, optional): True if move puts opponent king in check.
                Plays high-pitched "check" alert sound.
                Takes priority over is_capture if both True.
                Defaults to False.
        """
        # Exit early if sounds disabled
        if not self.enabled:
            return

        # Check takes priority (most important feedback)
        if is_check:
            self._play("check")

        # Capture is second priority
        elif is_capture:
            self._play("capture")

        # Default to standard move sound
        else:
            self._play("move")

    def play_castle_sound(self):
        """
        Play sound for castling move (kingside or queenside).
        """
        if self.enabled:
            self._play("castle")

    def play_promotion_sound(self):
        """
        Play sound for pawn promotion.
        """
        if self.enabled:
            self._play("promote")

    def play_game_start_sound(self):
        """
        Play sound when game starts or resets.
        """
        if self.enabled:
            self._play("game_start")

    def play_game_end_sound(self):
        """
        Play sound when game ends (checkmate, stalemate, draw, resignation).
        """
        if self.enabled:
            self._play("game_end")

    def play_illegal_move_sound(self):
        """
        Play sound for illegal move attempt.
        """
        if self.enabled:
            self._play("illegal")

    def _play(self, sound_name: str):
        """
        Internal method to play a sound effect by name.

        This private helper method handles the actual sound playback with error
        checking. It verifies the sound exists and is loaded before attempting
        playback. Used by all public play_*_sound() methods.

        Args:
            sound_name (str): Name of sound to play from self.sounds dictionary.
                Valid values: "move", "capture", "check", "castle", "promote",
                             "game_start", "game_end", "illegal"
        """
        # Verify sound exists in dictionary and is loaded (not None)
        if sound_name in self.sounds and self.sounds[sound_name] is not None:
            try:
                # Play sound asynchronously (returns immediately)
                # Sound plays in background via pygame.mixer
                self.sounds[sound_name].play()

            except pygame.error as e:
                # Log playback errors but don't crash
                print(f"[SoundManager] Error playing {sound_name}: {e}")

    def set_volume(self, volume: float):
        """
        Set volume for all sounds.

        Args:
            volume (float): Volume level between 0.0 (silent) and 1.0 (max).
                Values outside this range are automatically clamped.
                - 0.0 = completely silent
                - 0.5 = half volume
                - 1.0 = maximum volume
        """
        # Clamp volume to valid range [0.0, 1.0]
        self.volume = max(0.0, min(1.0, volume))

        # Apply new volume to all loaded sounds
        for sound in self.sounds.values():
            # Skip unloaded sounds (None entries)
            if sound is not None:
                # Update pygame Sound object volume
                sound.set_volume(self.volume)

    def set_enabled(self, enabled: bool):
        """
        Enable or disable sound playback.

        Args:
            enabled (bool): True to enable sound playback, False to disable.
        """
        self.enabled = enabled

    def stop_all(self):
        """
        Stop all currently playing sounds immediately.
        """
        if self.enabled:
            # Affects all sounds currently playing via pygame.mixer
            pygame.mixer.stop()
