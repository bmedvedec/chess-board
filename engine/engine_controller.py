"""
Engine Controller
-----------------
Thread-based chess engine controller for non-blocking move calculation.

This module provides two controller implementations for managing chess engine
move calculations: a threaded version for responsive GUIs and a simple blocking
version for debugging or single-threaded environments.
"""

import threading
import queue
import time
import chess
from typing import Optional, Callable

from engine.engine_wrapper import get_best_move, is_engine_ready


class EngineController:
    """
    Threaded chess engine controller for non-blocking move calculation.

    This class manages engine move calculations in a separate worker thread,
    allowing the GUI to remain responsive during engine thinking. It uses
    a queue-based communication pattern for thread-safe result delivery.
    """

    def __init__(self):
        """
        Initialize the engine controller with default state.

        Sets up the thread communication infrastructure and initializes
        all state flags to their idle values.
        """
        # Flag indicating engine is currently calculating a move
        # Prevents concurrent move requests which would interfere with each other
        self.thinking = False

        # Thread-safe queue for passing calculated moves from worker to main thread
        # Queue.Queue provides synchronized access without manual locking
        self.move_queue = queue.Queue()

        # Reference to the active worker thread (None when idle)
        # Allows monitoring and joining if needed
        self.current_thread: Optional[threading.Thread] = None

        # Cooperative cancellation flag
        # Set to True to request worker thread to stop early
        self.stop_thinking = False

        print("[EngineController] Initialized")

    def request_move(
        self,
        board: chess.Board,
        move_history: list,
        time_limit: float = 5.0,
        search_depth: Optional[int] = None,
        temperature: float = 1.0,
        callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Request engine to calculate best move asynchronously (non-blocking).

        This method starts a background thread to calculate the engine's move,
        allowing the calling thread (typically the GUI) to continue processing
        events.

        Args:
            board (chess.Board): Current board position to analyze.
                Will be deep-copied to prevent race conditions with main thread.

            move_history (list): List of UCI move strings played in the game.
                Some engines use this for opening book lookup or position context.
                Will be deep-copied to ensure thread safety.

            time_limit (float, optional): Maximum thinking time in seconds.
                Defaults to 5.0. Engine will try to return best move within this limit.
                Actual time may vary based on engine implementation.

            search_depth (Optional[int], optional): Search depth or iteration count.
                Interpretation depends on engine (e.g., MCTS iterations, alpha-beta depth).
                None means use engine's default depth. Defaults to None.

            temperature (float, optional): Move selection randomness (0.0 to 2.0+).
                - 0.0: Always pick best move (deterministic)
                - 1.0: Balanced exploration (default)
                - >1.0: More random/exploratory moves
                Higher values add variety to engine play style.

            callback (Optional[Callable[[str], None]], optional): Function to call
                when move is ready. Receives UCI move string as argument.
                Called from worker thread - ensure callback is thread-safe.
                Defaults to None (poll via get_move_if_ready instead).
        """
        # Check if already calculating a move
        # Only one move calculation allowed at a time to prevent thread conflicts
        if self.thinking:
            print("[EngineController] ⚠️ Already thinking, ignoring request")
            return

        # Verify engine is initialized and ready to receive commands
        if not is_engine_ready():
            print("[EngineController] ⚠️ Engine not ready")

            # If callback provided, try to recover by returning a random legal move
            # This prevents the game from freezing when engine is unavailable
            if callback:
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    import random

                    callback(random.choice(legal_moves).uci())
            return

        # Clear any stale results from previous move calculations
        # Prevents accidentally reading old results from a previous request
        while not self.move_queue.empty():
            try:
                # Non-blocking get - remove items until queue empty
                self.move_queue.get_nowait()
            except queue.Empty:
                # Queue is empty, nothing left to clear
                break

        # Update state flags to indicate calculation in progress
        self.thinking = True  # Prevents concurrent requests
        self.stop_thinking = False  # Reset cancellation flag

        # Create and start worker thread for engine calculation
        # Daemon thread automatically terminates when main program exits
        self.current_thread = threading.Thread(
            target=self._engine_worker,  # Worker function to run
            args=(
                board.copy(),  # Deep copy to prevent main thread modifications
                move_history.copy(),  # Deep copy for thread safety
                time_limit,
                search_depth,
                temperature,
                callback,
            ),
            daemon=True,  # Don't prevent program exit
        )
        # Start thread - returns immediately, calculation runs in background
        self.current_thread.start()

        print("[EngineController] Started thinking...")

    def _engine_worker(
        self,
        board: chess.Board,
        move_history: list,
        time_limit: float,
        search_depth: Optional[int],
        temperature: float,
        callback: Optional[Callable[[str], None]],
    ):
        """
        Worker thread function that performs engine calculation and delivers results.

        Args:
            board (chess.Board): Deep copy of board position to analyze.
                Isolated from main thread to prevent race conditions.

            move_history (list): Deep copy of move history for engine context.
                Some engines use this for opening book or repetition detection.

            time_limit (float): Maximum calculation time in seconds.
                Engine should return best move found within this limit.

            search_depth (Optional[int]): Search depth or iteration count.
                Engine-specific interpretation (MCTS iterations, alpha-beta depth, etc.).

            temperature (float): Move selection randomness parameter (0.0 to 2.0+).
                Controls determinism vs exploration in engine's move choice.

            callback (Optional[Callable[[str], None]]): Optional function to call with result.
                Receives UCI move string. Called from this worker thread.
        """
        # Record start time to measure actual thinking duration
        start_time = time.time()

        try:
            # Call the underlying engine to calculate best move
            # This is a BLOCKING call that may take several seconds
            # Safe to block here because we're in a separate thread
            move_uci = get_best_move(
                board=board,
                move_history=move_history,
                time_limit=time_limit,
                search_depth=search_depth,
                temperature=temperature,
            )

            # Calculate how long the engine actually took
            elapsed = time.time() - start_time

            # Check if move was cancelled while we were calculating
            if self.stop_thinking:
                print("[EngineController] Thinking cancelled")
                # Don't queue result, just exit worker thread
                return

            # Queue the calculated move for main thread to retrieve
            # Queue.put() is thread-safe, no lock needed
            self.move_queue.put(move_uci)

            # Log successful calculation with timing information
            print(f"[EngineController] Move calculated in {elapsed:.2f}s: {move_uci}")

            # Invoke callback if one was provided
            # Callback runs in THIS worker thread, so it must be thread-safe
            if callback:
                callback(move_uci)

        except Exception as e:
            # Catch any errors during engine calculation
            # Prevents worker thread from crashing silently
            print(f"[EngineController] ❌ Error during thinking: {e}")

            # Queue None to signal error condition to main thread
            self.move_queue.put(None)

        finally:
            # ALWAYS reset thinking flag, even if exception occurred
            # Critical for state consistency - prevents getting stuck in "thinking" state
            # Without this, subsequent requests would be rejected forever
            self.thinking = False

    def get_move_if_ready(self) -> Optional[str]:
        """
        Poll for calculated move without blocking (non-blocking check).

        This method checks if the engine has finished calculating and a result
        is available in the queue. It returns immediately whether or not a move
        is ready, making it suitable for polling in game loops.

        Returns:
            Optional[str]: UCI move string if available, None otherwise.
                - "e2e4", "e7e5", etc.: Valid UCI move string
                - None: Either still calculating OR an error occurred
        """
        try:
            # Attempt to retrieve move from queue without waiting
            # get_nowait() raises queue.Empty if nothing available
            move = self.move_queue.get_nowait()
            return move
        except queue.Empty:
            # No move available yet - either still calculating or not started
            return None

    def is_thinking(self) -> bool:
        """
        Check if engine is currently calculating a move.

        Returns:
            bool: True if engine is actively thinking, False otherwise.
        """
        return self.thinking

    def cancel_thinking(self):
        """
        Request cancellation of current engine calculation (best-effort).

        Sets the stop_thinking flag that the worker thread can check to abort
        early. This is a cooperative cancellation mechanism - the worker must
        explicitly check the flag. Cancellation may not occur immediately.
        """
        # Only attempt cancellation if actually thinking
        if self.thinking:
            print("[EngineController] Cancelling engine thinking...")

            # Set flag that worker thread can check
            # Worker will see this after get_best_move() returns
            self.stop_thinking = True

            # Immediately mark as not thinking to prevent new requests
            # Worker will also set this to False in finally block
            self.thinking = False

    def wait_for_move(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Block until engine returns a move or timeout occurs (blocking wait).

        This method waits for the engine calculation to complete, blocking
        the calling thread until a result is available or the timeout expires.
        Unlike get_move_if_ready(), this method does not return immediately.

        Args:
            timeout (Optional[float], optional): Maximum wait time in seconds.
                - None: Wait indefinitely until move ready (default)
                - float: Wait at most this many seconds

        Returns:
            Optional[str]: UCI move string or None on timeout/error.
                - "e2e4", "e7e5", etc.: Valid UCI move from engine
                - None: Timeout occurred OR engine error
        """
        try:
            # Block until move available or timeout expires
            # Queue.get() waits (blocks) until item available
            move = self.move_queue.get(timeout=timeout)

            # Clear thinking flag now that we have result
            self.thinking = False

            return move

        except queue.Empty:
            # Timeout occurred - no move available in time
            print("[EngineController] ⚠️ Move request timed out")

            # Attempt to cancel the thinking (best effort)
            # May not actually stop engine, but clears our state
            self.cancel_thinking()

            return None


# =============================================================================
# SIMPLE BLOCKING API
# =============================================================================
# The SimpleEngineController provides a synchronous alternative to the threaded
# EngineController. It blocks the calling thread during engine calculation,
# making it simpler to use but unsuitable for GUI applications.


class SimpleEngineController:
    """
    Synchronous blocking engine controller (no threading).

    This is a simplified alternative to EngineController that calls the engine
    directly without any threading. The calling thread blocks during engine
    calculation, which will freeze the GUI if called from the main thread.
    """

    def __init__(self):
        """
        Initialize simple blocking controller.

        No state tracking needed since everything is synchronous.
        """
        print("[SimpleEngineController] Initialized (blocking mode)")

    def get_move(
        self,
        board: chess.Board,
        move_history: list,
        time_limit: float = 5.0,
        search_depth: Optional[int] = None,
        temperature: float = 1.0,
    ) -> Optional[str]:
        """
        Calculate and return engine move (BLOCKS until complete).

        This method directly calls the engine and waits for the result,
        blocking the calling thread for the entire calculation duration.

        Args:
            board (chess.Board): Current board position to analyze.
                Not copied - engine operates on this instance directly.

            move_history (list): List of UCI move strings played in game.
                Used by some engines for opening book or context.

            time_limit (float, optional): Maximum thinking time in seconds.
                Defaults to 5.0. Engine returns best move within this limit.

            search_depth (Optional[int], optional): Search depth or iterations.
                Engine-specific interpretation. None uses engine default.

            temperature (float, optional): Move selection randomness (0.0-2.0+).
                - 0.0: Deterministic (always best move)
                - 1.0: Balanced (default)
                - >1.0: More random/exploratory

        Returns:
            Optional[str]: UCI move string or None on error.
                - "e2e4", "e7e5", etc.: Valid UCI move
                - None: Engine not ready or calculation error
        """
        # Check if engine is initialized and ready
        # Early exit if engine unavailable
        if not is_engine_ready():
            print("[SimpleEngineController] ⚠️ Engine not ready")
            return None

        try:
            # Inform user that blocking calculation is starting
            print("[SimpleEngineController] Thinking...")

            # Record start time for performance measurement
            start_time = time.time()

            # Call engine directly - THIS BLOCKS for up to time_limit seconds
            move_uci = get_best_move(
                board=board,
                move_history=move_history,
                time_limit=time_limit,
                search_depth=search_depth,
                temperature=temperature,
            )

            # Calculate actual time spent
            elapsed = time.time() - start_time

            print(
                f"[SimpleEngineController] Move calculated in {elapsed:.2f}s: {move_uci}"
            )

            return move_uci

        except Exception as e:
            # Catch and log any errors during calculation
            # Prevents exception from propagating to caller
            print(f"[SimpleEngineController] ❌ Error: {e}")
            return None
