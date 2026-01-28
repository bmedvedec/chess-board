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
from utils.config import Config
import chess.engine

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default path to the built-in dummy engine (relative to project root)
# This will always be used unless a UCI_ENGINE_PATH is provided via Config
DEFAULT_DUMMY_ENGINE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "dummy_engine")
)

# Name of the Python module to import from the dummy engine project
# This should be the module filename without .py extension
# The module must contain a get_best_move() function
ENGINE_MODULE_NAME = "inference_engine"

# Filename of the trained model file (relative to dummy engine path)
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

        By default, this wrapper always uses the built-in dummy engine.
        If Config.UCI_ENGINE_PATH is set, it will attempt to load a UCI engine
        instead and fall back to the dummy engine on failure.

        Args:
            engine_path (Optional[str], optional): Custom path to dummy engine.
                If None, DEFAULT_DUMMY_ENGINE_PATH is used.
        """
        # Always default to dummy engine path unless explicitly overridden
        self.engine_path = engine_path or DEFAULT_DUMMY_ENGINE_PATH

        # Module will be imported and stored here by load_engine()
        self.engine_module = None

        # Model object will be loaded and cached here (if engine uses one)
        self.model = None

        # Tracks whether engine is ready to use
        self.model_loaded = False

        # Engine mode: "dummy" for Python module, "uci" for external UCI engine
        self.mode = "dummy"

        # UCI engine handle (chess.engine.SimpleEngine)
        self.uci_engine = None

        print("[EngineWrapper] Initializing...")

    def load_engine(self):
        """
        Load UCI engine if configured, otherwise fall back to dummy engine.

        Returns:
            bool: True if engine loaded successfully, False otherwise.
        """
        # ------------------------------------------------------------------
        # 1. Try UCI engine if path is set in Config
        # ------------------------------------------------------------------
        if getattr(Config, "UCI_ENGINE_PATH", None):
            try:
                self.uci_engine = chess.engine.SimpleEngine.popen_uci(
                    Config.UCI_ENGINE_PATH
                )
                self.mode = "uci"
                self.model_loaded = True

                print(
                    f"[EngineWrapper] ✅ Loaded UCI engine from: {Config.UCI_ENGINE_PATH}"
                )

                # Optional configuration (e.g. Stockfish Skill Level)
                try:
                    self.uci_engine.configure(
                        {
                            "Skill Level": getattr(Config, "ENGINE_SKILL_LEVEL", 20),
                        }
                    )
                except Exception:
                    # Not all UCI engines support this option
                    pass

                return True
            except Exception as e:
                print(f"[EngineWrapper] ❌ Failed to load UCI engine: {e}")
                print("[EngineWrapper] Falling back to dummy engine")

        # ------------------------------------------------------------------
        # 2. Dummy engine mode (default)
        # ------------------------------------------------------------------
        self.mode = "dummy"

        # Verify path exists on filesystem
        if not os.path.exists(self.engine_path):
            print(f"[EngineWrapper] ❌ Dummy engine path not found: {self.engine_path}")
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
            if not hasattr(self.engine_module, "get_best_move"):
                print(
                    "[EngineWrapper] ❌ Engine module missing 'get_best_move' function"
                )
                return False

            # Optionally load pre-trained model (for ML engines)
            if hasattr(self.engine_module, "load_model") and MODEL_FILENAME:
                model_path = os.path.join(self.engine_path, MODEL_FILENAME)

                if os.path.exists(model_path):
                    print(f"[EngineWrapper] Loading model from: {model_path}")
                    self.model = self.engine_module.load_model(model_path)
                    print("[EngineWrapper] ✅ Model loaded successfully")
                else:
                    print(f"[EngineWrapper] ⚠️ Model file not found: {model_path}")

            self.model_loaded = True
            return True

        except ImportError as e:
            print(f"[EngineWrapper] ❌ Import error: {e}")
            return False
        except Exception as e:
            print(f"[EngineWrapper] ❌ Unexpected error: {e}")
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
        Get best move from the loaded engine (UCI or dummy).

        For UCI: Uses chess.engine.play() with limits.
        For dummy: Delegates to the imported module.

        Returns a legal UCI move string, falling back to random if needed.
        """
        if not self.model_loaded:
            print("[EngineWrapper] ⚠️ Engine not loaded, using random move")
            return self._get_random_move(board)

        if self.mode == "uci":
            if self.uci_engine is None:
                print("[EngineWrapper] UCI engine is None despite mode='uci'")
                return self._get_random_move(board)

            limit = chess.engine.Limit(
                time=getattr(Config, "ENGINE_TIME_LIMIT", time_limit),
                depth=getattr(Config, "ENGINE_MAX_DEPTH", None),
            )
            result = self.uci_engine.play(board, limit, ponder=False)
            if result.move is None:
                return self._get_random_move(board)
            return result.move.uci()

        # Dummy mode
        if self.engine_module is None:
            print("[EngineWrapper] engine_module is None in dummy mode")
            return self._get_random_move(board)

        try:
            move_uci = self.engine_module.get_best_move(
                board=board,
                move_history=move_history,
                time_limit=time_limit,
                search_depth=search_depth,
                temperature=temperature,
                model=self.model,
            )

            # Validate the returned move is legal
            try:
                move = chess.Move.from_uci(move_uci)
                if move in board.legal_moves:
                    return move_uci
                else:
                    print(f"[EngineWrapper] ⚠️ Engine returned illegal move: {move_uci}")
                    return self._get_random_move(board)

            except ValueError:
                print(f"[EngineWrapper] ⚠️ Engine returned invalid UCI: {move_uci}")
                return self._get_random_move(board)

        except Exception as e:
            print(f"[EngineWrapper] ❌ Engine error: {e}")
            print("[EngineWrapper] Falling back to random move")
            return self._get_random_move(board)

    def _get_random_move(self, board: chess.Board) -> str:
        """
        Generate a random legal move as last-resort fallback.
        """
        legal_moves = list(board.legal_moves)

        if not legal_moves:
            raise ValueError("No legal moves available")

        move = random.choice(legal_moves)
        return move.uci()

    def is_loaded(self) -> bool:
        """
        Check if engine is successfully loaded and ready to use.
        """
        return self.model_loaded

    def close(self):
        """
        Cleanly close the engine (for UCI mode).
        """
        if self.mode == "uci" and self.uci_engine:
            self.uci_engine.quit()
            print("[EngineWrapper] UCI engine closed")


# =============================================================================
# SIMPLE API (MODULE-LEVEL SINGLETON)
# =============================================================================

_engine_instance: Optional[EngineWrapper] = None


def initialize_engine(engine_path: Optional[str] = None) -> bool:
    """
    Initialize the global chess engine instance (call once at startup).

    By default, this always loads the dummy engine.
    If Config.UCI_ENGINE_PATH is set, UCI mode is used instead.
    """
    global _engine_instance

    _engine_instance = EngineWrapper(engine_path)
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
    """
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
    """
    return _engine_instance is not None and _engine_instance.is_loaded()


def close_engine():
    """
    Cleanly close the global engine instance.
    """
    if _engine_instance:
        _engine_instance.close()
