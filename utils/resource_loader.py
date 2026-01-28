import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, "_MEIPASS", None)
        if base_path is None:
            raise AttributeError("_MEIPASS not found")
    except AttributeError:
        # In dev mode, go up one directory from utils/ to project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)
