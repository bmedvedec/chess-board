"""
Inference Engine Wrapper
-------------------------
Dynamic loader for external chess engine modules with standardized interface.

This module provides a flexible wrapper that can load and interface with external
chess engine implementations.
"""

import sys
import os
import chess
import random
from typing import Optional, List

# =============================================================================
# CONFIGURATION
# =============================================================================
# These settings control which external engine to load and how to find it.

# Path to your external inference engine project directory
# Set this to the absolute path of engine's root folder
# None means no engine is configured (will use random move fallback)
EXTERNAL_ENGINE_PATH = None


# Name of the Python module to import from the external engine project
# This should be the module filename without .py extension
# The module must contain a get_best_move() function
# Default: "inference_engine" (expects inference_engine.py)
ENGINE_MODULE_NAME = "inference_engine"

# Filename of the trained model file (relative to EXTERNAL_ENGINE_PATH)
# Used if engine needs to load a pre-trained neural network
# Set to None if engine doesn't use a model file
MODEL_FILENAME = "model.pt"

# =============================================================================


class EngineWrapper:
    """
    Dynamic loader and interface for external chess engine modules.

    This class handles the complexities of loading external Python modules,
    initializing models, and providing a consistent interface for move generation
    regardless of the underlying engine implementation.
    """

    def __init__(self, engine_path: Optional[str] = None):
        """
        Initialize the engine wrapper with configuration.

        Sets up the wrapper with paths and state tracking, but does not
        actually load the engine yet. Call load_engine() to perform the
        import and model loading.

        Args:
            engine_path (Optional[str], optional): Path to external engine project.
                Overrides the EXTERNAL_ENGINE_PATH constant if provided.
                Should be absolute path to directory containing engine module.
                Defaults to None (uses EXTERNAL_ENGINE_PATH).
        """
        # Use provided path or fall back to global configuration
        self.engine_path = engine_path or EXTERNAL_ENGINE_PATH

        # Module will be imported and stored here by load_engine()
        self.engine_module = None

        # Model object will be loaded and cached here (if engine uses one)
        self.model = None

        # Tracks whether engine is ready to use
        # Set to True after successful load_engine() call
        self.model_loaded = False

        print("[EngineWrapper] Initializing...")

    def load_engine(self):
        """
        Dynamically import engine module and load model if available.

        Returns:
            bool: True if engine loaded successfully, False otherwise.
                Returns True even if model loading fails (model is optional).
                Returns False if path invalid, import fails, or interface missing.
        """
        # Validate engine path is configured
        if self.engine_path is None:
            print("[EngineWrapper] ❌ No engine path configured!")
            print(
                "[EngineWrapper] Please set EXTERNAL_ENGINE_PATH in engine_wrapper.py"
            )
            return False

        # Verify path exists on filesystem
        if not os.path.exists(self.engine_path):
            print(f"[EngineWrapper] ❌ Engine path not found: {self.engine_path}")
            return False

        try:
            # Add engine directory to Python's module search path
            if self.engine_path not in sys.path:
                sys.path.insert(0, self.engine_path)
                print(f"[EngineWrapper] Added to path: {self.engine_path}")

            # Dynamically import the engine module
            self.engine_module = __import__(ENGINE_MODULE_NAME)
            print(f"[EngineWrapper] ✅ Imported module: {ENGINE_MODULE_NAME}")

            # Validate the engine provides required interface
            # Every engine MUST have get_best_move() function
            if not hasattr(self.engine_module, "get_best_move"):
                print(
                    "[EngineWrapper] ❌ Engine module missing 'get_best_move' function"
                )
                return False

            # Optionally load pre-trained model (for ML engines)
            # load_model() function is optional - not all engines need it
            if hasattr(self.engine_module, "load_model"):
                # Build full path to model file
                model_path = os.path.join(self.engine_path, MODEL_FILENAME)

                # Check if model file exists
                if os.path.exists(model_path):
                    print(f"[EngineWrapper] Loading model from: {model_path}")

                    # Call engine's load_model function to load weights
                    # Model type depends on engine
                    self.model = self.engine_module.load_model(model_path)

                    print("[EngineWrapper] ✅ Model loaded successfully")
                else:
                    # Model file missing
                    print(f"[EngineWrapper] ⚠️ Model file not found: {model_path}")
                    print(
                        "[EngineWrapper] Will try to use engine without pre-loaded model"
                    )

            # Mark engine as successfully loaded
            # True even if model loading failed (model is optional)
            self.model_loaded = True
            print("[EngineWrapper] ✅ Engine ready")
            return True

        except ImportError as e:
            # Module import failed - module doesn't exist or has import errors
            print(f"[EngineWrapper] ❌ Failed to import engine: {e}")
            return False

        except Exception as e:
            # Catch-all for other errors (model loading, attribute errors, etc.)
            # Prevents engine failures from crashing the GUI
            print(f"[EngineWrapper] ❌ Error loading engine: {e}")
            return False

    def get_best_move(
        self,
        board: chess.Board,
        move_history: Optional[List[str]] = None,
        time_limit: float = 5.0,
        search_depth: Optional[int] = None,
        temperature: float = 1.0,
    ) -> str:
        """
        Request best move from engine with automatic validation and fallback.

        This is the main interface for getting moves from the engine. It handles
        calling the external engine, validating the response, and falling back
        to random moves if anything goes wrong.

        Args:
            board (chess.Board): Current position to analyze.
                Standard python-chess Board object with current game state.

            move_history (Optional[List[str]], optional): Game move history in UCI format.
                List of move strings like ["e2e4", "e7e5", ...].
                Some engines use this for opening books or position context.
                Defaults to None.

            time_limit (float, optional): Maximum thinking time in seconds.
                Engine should return best move within this limit.
                Defaults to 5.0 seconds.

            search_depth (Optional[int], optional): Search depth or iteration count.
                Interpretation is engine-specific:
                - MCTS engines: Number of simulations
                - Minimax engines: Ply depth
                - Neural networks: Might be ignored
                Defaults to None (engine uses its default).

            temperature (float, optional): Move selection randomness (0.0 to 2.0+).
                - 0.0: Always select highest-scored move (deterministic)
                - 1.0: Balanced stochastic selection (default)
                - >1.0: More random/exploratory moves
                Defaults to 1.0.

        Returns:
            str: UCI format move string (e.g., "e2e4", "e7e5", "e7e8q" for promotion).
                Always returns a valid, legal move.
                Falls back to random move on any error.
        """
        # Check if engine is loaded and ready
        # If not, immediately fall back to random moves
        if not self.model_loaded or self.engine_module is None:
            print("[EngineWrapper] ⚠️ Engine not loaded, using fallback (random move)")
            return self._get_random_move(board)

        try:
            # Call the external engine's get_best_move function
            # Pass all parameters - engine uses what it needs, ignores the rest
            # This allows flexibility in engine implementations
            move_uci = self.engine_module.get_best_move(
                board=board,
                move_history=move_history,
                time_limit=time_limit,
                search_depth=search_depth,
                temperature=temperature,
                model=self.model,  # Pass pre-loaded model if available
            )

            # Validate that the returned move is legal
            # This protects against buggy engines or model errors
            try:
                # Parse UCI string into Move object
                # from_uci() raises ValueError if string is invalid
                move = chess.Move.from_uci(move_uci)

                # Check if move is actually legal in current position
                # Engines should only return legal moves, but verify to be safe
                if move in board.legal_moves:
                    # Move is valid and legal - return it
                    return move_uci
                else:
                    # Engine returned illegal move - fall back to random
                    print(f"[EngineWrapper] ⚠️ Engine returned illegal move: {move_uci}")
                    return self._get_random_move(board)

            except ValueError:
                # UCI string is malformed - can't even parse it
                print(f"[EngineWrapper] ⚠️ Engine returned invalid UCI: {move_uci}")
                return self._get_random_move(board)

        except Exception as e:
            # Catch any other errors from engine execution
            # Prevents engine bugs from crashing the entire game
            print(f"[EngineWrapper] ❌ Engine error: {e}")
            print("[EngineWrapper] Falling back to random move")
            return self._get_random_move(board)

    def _get_random_move(self, board: chess.Board) -> str:
        """
        Generate a random legal move as last-resort fallback.

        This method is called when the engine fails or returns invalid moves.
        It ensures the game can always continue, even without a working engine.

        Args:
            board (chess.Board): Current position to generate move from.

        Returns:
            str: Randomly selected legal move in UCI format.

        Raises:
            ValueError: If no legal moves available (game over position).
        """
        # Get all legal moves for current position
        legal_moves = list(board.legal_moves)

        # Check if any moves available
        if not legal_moves:
            raise ValueError("No legal moves available")

        # Pick random move uniformly
        move = random.choice(legal_moves)

        # Convert Move object to UCI string
        return move.uci()

    def is_loaded(self) -> bool:
        """
        Check if engine is successfully loaded and ready to use.

        Returns:
            bool: True if engine initialized successfully, False otherwise.
        """
        return self.model_loaded


# =============================================================================
# SIMPLE API (MODULE-LEVEL SINGLETON)
# =============================================================================
# These functions provide convenient access to a global engine instance.
# This simplifies usage - just call initialize_engine() once, then use
# get_best_move() throughout the application.

# Global singleton engine instance
# None until initialize_engine() is called
_engine_instance: Optional[EngineWrapper] = None


def initialize_engine(engine_path: Optional[str] = None) -> bool:
    """
    Initialize the global chess engine instance (call once at startup).

    This function creates and loads the global engine instance that will be
    used throughout the application.

    Args:
        engine_path (Optional[str], optional): Path to external engine project.
            Overrides EXTERNAL_ENGINE_PATH constant if provided.
            Use this to specify engine path at runtime instead of in config.
            Defaults to None (uses EXTERNAL_ENGINE_PATH).

    Returns:
        bool: True if engine loaded successfully, False if loading failed.
            False means engine not available - game will use random fallback moves.
    """
    global _engine_instance

    # Create new EngineWrapper instance with provided or default path
    _engine_instance = EngineWrapper(engine_path)

    # Attempt to load the engine module and model
    return _engine_instance.load_engine()


def get_best_move(
    board: chess.Board,
    move_history: Optional[List[str]] = None,
    time_limit: float = 5.0,
    search_depth: Optional[int] = None,
    temperature: float = 1.0,
) -> str:
    """
    Get best move from the global engine instance (convenience function).

    Args:
        board (chess.Board): Current position to analyze.

        move_history (Optional[List[str]], optional): Move history in UCI format.
            Defaults to None.

        time_limit (float, optional): Maximum thinking time in seconds.
            Defaults to 5.0.

        search_depth (Optional[int], optional): Search depth or iteration count.
            Defaults to None (engine decides).

        temperature (float, optional): Move selection randomness (0.0 to 2.0+).
            Defaults to 1.0.

    Returns:
        str: UCI format move string. Always returns a valid legal move.

    Raises:
        RuntimeError: If initialize_engine() was not called first.
            This is a programming error - always initialize before use.
    """
    # Check that engine was initialized
    if _engine_instance is None:
        raise RuntimeError("Engine not initialized. Call initialize_engine() first.")

    # Delegate to the wrapper instance's method
    return _engine_instance.get_best_move(
        board=board,
        move_history=move_history,
        time_limit=time_limit,
        search_depth=search_depth,
        temperature=temperature,
    )


def is_engine_ready() -> bool:
    """
    Check if global engine is initialized and ready to use.

    This function checks both that initialize_engine() was called and
    that the engine loaded successfully.

    Returns:
        bool: True if engine ready, False if not initialized or failed to load.
    """
    return _engine_instance is not None and _engine_instance.is_loaded()
