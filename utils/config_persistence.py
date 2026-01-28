# utils/config_persistence.py
import json
import os
import sys
from typing import Dict, Any
from utils.config import Config


# Get directory where the main script / exe lives
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # PyInstaller / frozen exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Normal Python run
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def save_config_to_file() -> bool:
    """Save current Config values we care about to JSON file."""
    data: Dict[str, Any] = {
        ""
        # Engine / gameplay
        "USE_UCI_ENGINE": Config.USE_UCI_ENGINE,
        "UCI_ENGINE_PATH": Config.UCI_ENGINE_PATH,
        "ENGINE_TIME_LIMIT": Config.ENGINE_TIME_LIMIT,
        "ENGINE_MAX_DEPTH": Config.ENGINE_MAX_DEPTH,
        "ENGINE_SKILL_LEVEL": Config.ENGINE_SKILL_LEVEL,
        "MCTS_ITERATIONS": Config.MCTS_ITERATIONS,
        "TEMPERATURE": Config.TEMPERATURE,
        # Visual / UX
        "ANIMATE_MOVES": Config.ANIMATE_MOVES,
        "ANIMATION_SPEED": Config.ANIMATION_SPEED,
        "SHOW_LAST_MOVE": Config.SHOW_LAST_MOVE,
        "SHOW_COORDINATES": Config.SHOW_COORDINATES,
        "SHOW_CAPTURED_PIECES": Config.SHOW_CAPTURED_PIECES,
        "ENABLE_PREMOVE": Config.ENABLE_PREMOVE,
        "SHOW_FPS": Config.SHOW_FPS,
        # Audio
        "ENABLE_SOUNDS": Config.ENABLE_SOUNDS,
        "SOUND_VOLUME": Config.SOUND_VOLUME,
        # Board orientation (important!)
        "FLIP_BOARD": Config.FLIP_BOARD,
        # Less common / rarely changed, but good to persist
        "HUMAN_COLOR": Config.HUMAN_COLOR,
        "DEBUG_MODE": Config.DEBUG_MODE,
        "LOG_MOVES": Config.LOG_MOVES,
    }

    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[ConfigPersistence] Settings saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"[ConfigPersistence] Failed to save config: {type(e).__name__}: {e}")
        return False


def load_config_from_file() -> bool:
    """Load saved values from JSON and override Config defaults."""
    if not os.path.exists(CONFIG_FILE):
        print(
            f"[ConfigPersistence] No config file found ({CONFIG_FILE}) → using defaults"
        )
        return False

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Apply only known/safe keys — ignore unknown/old ones
        mappings = {
            "USE_UCI_ENGINE": lambda v: setattr(Config, "USE_UCI_ENGINE", bool(v)),
            "UCI_ENGINE_PATH": lambda v: setattr(Config, "UCI_ENGINE_PATH", str(v)),
            "ENGINE_TIME_LIMIT": lambda v: setattr(
                Config, "ENGINE_TIME_LIMIT", float(v)
            ),
            "ENGINE_MAX_DEPTH": lambda v: setattr(
                Config, "ENGINE_MAX_DEPTH", int(v) if v is not None else None
            ),
            "ENGINE_SKILL_LEVEL": lambda v: setattr(
                Config, "ENGINE_SKILL_LEVEL", int(v)
            ),
            "MCTS_ITERATIONS": lambda v: setattr(Config, "MCTS_ITERATIONS", int(v)),
            "TEMPERATURE": lambda v: setattr(Config, "TEMPERATURE", float(v)),
            "ANIMATE_MOVES": lambda v: setattr(Config, "ANIMATE_MOVES", bool(v)),
            "ANIMATION_SPEED": lambda v: setattr(Config, "ANIMATION_SPEED", int(v)),
            "SHOW_LAST_MOVE": lambda v: setattr(Config, "SHOW_LAST_MOVE", bool(v)),
            "SHOW_COORDINATES": lambda v: setattr(Config, "SHOW_COORDINATES", bool(v)),
            "SHOW_CAPTURED_PIECES": lambda v: setattr(
                Config, "SHOW_CAPTURED_PIECES", bool(v)
            ),
            "ENABLE_PREMOVE": lambda v: setattr(Config, "ENABLE_PREMOVE", bool(v)),
            "SHOW_FPS": lambda v: setattr(Config, "SHOW_FPS", bool(v)),
            "ENABLE_SOUNDS": lambda v: setattr(Config, "ENABLE_SOUNDS", bool(v)),
            "SOUND_VOLUME": lambda v: setattr(Config, "SOUND_VOLUME", float(v)),
            "FLIP_BOARD": lambda v: setattr(Config, "FLIP_BOARD", bool(v)),
            "HUMAN_COLOR": lambda v: setattr(Config, "HUMAN_COLOR", str(v).lower()),
            "DEBUG_MODE": lambda v: setattr(Config, "DEBUG_MODE", bool(v)),
            "LOG_MOVES": lambda v: setattr(Config, "LOG_MOVES", bool(v)),
        }

        applied = 0
        for key, value in data.items():
            if key in mappings:
                try:
                    mappings[key](value)
                    applied += 1
                except Exception as e:
                    print(f"[ConfigPersistence] Failed to apply {key} = {value!r}: {e}")

        print(f"[ConfigPersistence] Loaded {applied} settings from {CONFIG_FILE}")
        if applied > 0 and Config.USE_UCI_ENGINE:
            print(f"  → UCI engine: enabled, path = {Config.UCI_ENGINE_PATH}")
        return applied > 0

    except Exception as e:
        print(f"[ConfigPersistence] Failed to load config: {e}")
        return False
