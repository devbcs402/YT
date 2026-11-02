"""
Configuration manager for the Python Video Downloader.
Handles loading, saving, and updating user preferences from config.json.
"""

import os
import json
from pathlib import Path

DEFAULT_DOWNLOAD_DIR = r"D:\VideoDownloads"

DEFAULT_CONFIG = {
    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "quality_mode": "best",
    "container_preference": "mp4",
    "auto_download": True
}


def get_config_path():
    """Return the absolute path to config.json located in the project directory."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config(config_path=None):
    """
    Load configuration from config.json.
    Falls back to DEFAULT_CONFIG if file is missing or invalid.
    """
    path = config_path or get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = {**DEFAULT_CONFIG, **data}
                return config
        except Exception:
            pass

    # Save default config if not present
    save_config(DEFAULT_CONFIG, path)
    return dict(DEFAULT_CONFIG)


def save_config(config, config_path=None):
    """Save configuration dictionary to config.json."""
    path = config_path or get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save config to {path}: {e}")
        return False


def set_download_dir(new_dir, config_path=None):
    """Update and persist the download directory."""
    config = load_config(config_path)
    clean_dir = os.path.abspath(new_dir.strip().strip('"').strip("'"))
    ensure_download_dir(clean_dir)
    config["download_dir"] = clean_dir
    save_config(config, config_path)
    return clean_dir


def ensure_download_dir(dir_path):
    """Ensure the target download directory exists on disk."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"[ERROR] Could not create download directory '{dir_path}': {e}")
        return False

