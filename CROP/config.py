"""
Configuration module for the YouTube Shorts Video Splitter.
Manages application settings and persistent user preferences in config.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path("config.json")


@dataclass
class AppConfig:
    """Application configuration settings."""

    input_video: str = "video/video.mp4"
    output_dir: str = "output/shorts"
    clip_duration: int = 60
    # format modes: 'original', 'vertical_blur', 'vertical_crop'
    video_format: str = "vertical_blur"
    output_resolution: str = "1080x1920"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 18
    preset: str = "fast"
    stream_copy_original: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppConfig:
        """Create AppConfig from dictionary with safe fallback defaults."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """
    Load configuration from config.json.
    If the file does not exist, create it with default values.
    """
    if not config_path.exists():
        config = AppConfig()
        save_config(config, config_path)
        return config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AppConfig.from_dict(data)
    except Exception:
        # If config is corrupted, fall back to default
        config = AppConfig()
        save_config(config, config_path)
        return config


def save_config(config: AppConfig, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Save configuration to config.json."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=4)

