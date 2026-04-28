#!/usr/bin/env python3
"""
settings.py — Settings persistence for Duplicate File Detector GUI.

Saves/loads GUI state as JSON in the user's home directory.
"""

import json
import os

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".dedup")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULTS = {
    "scan_path": "",
    "staging_path": "",
    "min_size": 0,
    "follow_symlinks": False,
    "no_default_skip": False,
    "skip_dirs": "",
    "window_x": None,
    "window_y": None,
    "window_width": 820,
    "window_height": 680,
}


def load_settings() -> dict:
    """Load settings from disk, returning defaults for missing keys."""
    result = dict(DEFAULTS)
    try:
        if os.path.isfile(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            result.update(saved)
    except (json.JSONDecodeError, OSError):
        pass
    return result


def save_settings(settings: dict) -> None:
    """Save settings to disk."""
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def reset_settings() -> None:
    """Reset settings file to defaults."""
    save_settings(dict(DEFAULTS))
