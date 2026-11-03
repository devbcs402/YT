"""
Configuration manager for Mobile YouTube Shorts Video Splitter.
Tailored for mobile environments (iOS a-Shell / Android Termux) and desktop.
Zero external dependencies - standard library only.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path("config.json")


@dataclass
class MobileAppConfig:
    """Configuration settings for mobile-friendly video splitting."""

    input_video: str = "video/video.mp4"
    output_dir: str = "output/shorts"
    clip_duration: int = 60
    # format options: 'original', 'vertical_blur', 'vertical_crop'
    video_format: str = "vertical_blur"
    # resolution: '1080x1920' (Full HD) or '720x1280' (Faster on battery/mobile)
    output_resolution: str = "1080x1920"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 20
    preset: str = "fast"
    stream_copy_original: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MobileAppConfig:
        """Create config from dictionary with safe fallbacks."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> MobileAppConfig:
    """
    Load configuration from config.json.
    Creates default file if it doesn't exist or is corrupted.
    """
    if not config_path.exists():
        cfg = MobileAppConfig()
        save_config(cfg, config_path)
        return cfg

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return MobileAppConfig.from_dict(data)
    except Exception:
        cfg = MobileAppConfig()
        save_config(cfg, config_path)
        return cfg


def save_config(config: MobileAppConfig, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Save configuration to config.json."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=4)

