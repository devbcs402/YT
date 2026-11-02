"""
Video processor module for YouTube Shorts Video Splitter.
Handles FFmpeg/ffprobe integration, stream validation, clip calculations,
video transcoding, vertical Shorts conversions, and output verification.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class ClipSegment:
    """Represents a time segment to be split into a short clip."""

    index: int
    start_time: float
    duration: float
    end_time: float
    filename: str

    @property
    def formatted_start(self) -> str:
        return format_timestamp(self.start_time)

    @property
    def formatted_end(self) -> str:
        return format_timestamp(self.end_time)

    @property
    def formatted_range(self) -> str:
        return f"{self.formatted_start} - {self.formatted_end}"


@dataclass
class VideoInfo:
    """Metadata of a probed video file."""

    path: Path
    filename: str
    duration: float
    file_size_bytes: int
    width: int
    height: int
    aspect_ratio: str
    fps: float
    video_codec: str
    has_audio: bool
    audio_codec: Optional[str] = None
    audio_channels: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    bitrate: Optional[int] = None

    @property
    def formatted_duration(self) -> str:
        return format_duration(self.duration)

    @property
    def formatted_size(self) -> str:
        return format_file_size(self.file_size_bytes)

    @property
    def resolution_str(self) -> str:
        return f"{self.width}x{self.height}"


def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS."""
    secs = int(round(seconds))
    hrs = secs // 3600
    mins = (secs % 3600) // 60
    rem_secs = secs % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{rem_secs:02d}"
    return f"{mins:02d}:{rem_secs:02d}"


def format_duration(seconds: float) -> str:
    """Format duration into a friendly string (e.g. '10m 25s' or '01:15:20')."""
    total_seconds = int(round(seconds))
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    rem_secs = total_seconds % 60
    if hrs > 0:
        return f"{hrs}h {mins}m {rem_secs}s ({format_timestamp(seconds)})"
    return f"{mins}m {rem_secs}s ({format_timestamp(seconds)})"


def format_file_size(bytes_count: int) -> str:
    """Format bytes into readable MB or GB string."""
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    if bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def check_ffmpeg_installed() -> Tuple[bool, bool, str]:
    """
    Check if ffmpeg and ffprobe are available in PATH.
    Returns: (ffmpeg_found, ffprobe_found, detailed_status_or_guide)
    """
    ffmpeg_bin = shutil.which("ffmpeg")
    ffprobe_bin = shutil.which("ffprobe")

    ffmpeg_ok = ffmpeg_bin is not None
    ffprobe_ok = ffprobe_bin is not None

    if ffmpeg_ok and ffprobe_ok:
        return True, True, "FFmpeg and ffprobe are installed and ready."

    missing = []
    if not ffmpeg_ok:
        missing.append("ffmpeg")
    if not ffprobe_ok:
        missing.append("ffprobe")

    install_instructions = (
        f"[ERROR] Required tool(s) missing from PATH: {', '.join(missing)}\n\n"
        "How to install FFmpeg on Windows:\n\n"
        "Option 1: Using Windows Package Manager (Winget - Recommended)\n"
        "  Open PowerShell and run:\n"
        "    winget install Gyan.FFmpeg\n\n"
        "Option 2: Using Chocolatey\n"
        "  Open PowerShell as Administrator and run:\n"
        "    choco install ffmpeg\n\n"
        "Option 3: Manual Installation\n"
        "  1. Download the release build from: https://www.gyan.dev/ffmpeg/builds/\n"
        "     (Download 'ffmpeg-release-essentials.zip')\n"
        "  2. Extract the archive to C:\\ffmpeg\n"
        "  3. Add C:\\ffmpeg\\bin to your System PATH environment variable.\n"
        "  4. Restart your PowerShell or terminal window.\n"
    )
    return ffmpeg_ok, ffprobe_ok, install_instructions


class VideoProcessor:
    """Encapsulates video analysis, clipping, and conversion logic."""

    def __init__(self) -> None:
        pass

    def probe_video(self, video_path: Path) -> VideoInfo:
        """
        Probe input video file using ffprobe and return structured VideoInfo.
        Raises FileNotFoundError if file does not exist, or ValueError if corrupted/invalid.
        """
        if not video_path.exists():
            raise FileNotFoundError(
                f"Source video not found at: {video_path.resolve()}\n"
                f"Please place your video file at '{video_path}' and try again."
            )

        if video_path.is_dir():
            raise ValueError(f"Path is a directory, not a video file: {video_path}")

        file_size = video_path.stat().st_size
        if file_size == 0:
            raise ValueError(f"Video file is empty (0 bytes): {video_path}")

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(video_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            raise RuntimeError(
                "ffprobe executable was not found. Please install FFmpeg."
            )

        if result.returncode != 0:
            err_msg = result.stderr.strip() or "Unknown ffprobe error"
            raise ValueError(
                f"Unable to read video file '{video_path.name}'. Details: {err_msg}"
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse ffprobe output: {exc}")

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        # Find first video stream
        video_stream = None
        audio_stream = None
        for stream in streams:
            codec_type = stream.get("codec_type")
            if codec_type == "video" and video_stream is None:
                video_stream = stream
            elif codec_type == "audio" and audio_stream is None:
                audio_stream = stream

        if not video_stream:
            raise ValueError(
                f"File '{video_path.name}' does not contain any valid video stream."
            )

        # Calculate duration
        duration_str = format_info.get("duration") or video_stream.get("duration")
        if not duration_str or float(duration_str) <= 0:
            # Fallback: check audio stream duration
            if audio_stream and audio_stream.get("duration"):
                duration_str = audio_stream.get("duration")
            else:
                raise ValueError(
                    f"Could not determine valid duration for '{video_path.name}'."
                )

        duration = float(duration_str)
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        # Calculate aspect ratio
        dar = video_stream.get("display_aspect_ratio")
        if not dar and width > 0 and height > 0:
            gcd = math.gcd(width, height)
            dar = f"{width // gcd}:{height // gcd}"
        elif not dar:
            dar = "Unknown"

        # Frame rate
        fps = 0.0
        r_fps = video_stream.get("r_frame_rate", "0/0")
        if "/" in r_fps:
            num, den = r_fps.split("/")
            try:
                num_f, den_f = float(num), float(den)
                if den_f != 0:
                    fps = round(num_f / den_f, 2)
            except ValueError:
                fps = 0.0

        video_codec = video_stream.get("codec_name", "unknown")
        bitrate_str = format_info.get("bit_rate")
        bitrate = int(bitrate_str) if bitrate_str and bitrate_str.isdigit() else None

        has_audio = audio_stream is not None
        audio_codec = audio_stream.get("codec_name") if audio_stream else None
        audio_channels = audio_stream.get("channels") if audio_stream else None
        audio_sr = (
            int(audio_stream.get("sample_rate", 0)) if audio_stream else None
        )

        return VideoInfo(
            path=video_path,
            filename=video_path.name,
            duration=duration,
            file_size_bytes=file_size,
            width=width,
            height=height,
            aspect_ratio=dar,
            fps=fps,
            video_codec=video_codec,
            has_audio=has_audio,
            audio_codec=audio_codec,
            audio_channels=audio_channels,
            audio_sample_rate=audio_sr,
            bitrate=bitrate,
        )

    @staticmethod
    def calculate_clips(
        duration: float, clip_duration: float = 60.0
    ) -> List[ClipSegment]:
        """
        Calculate non-overlapping, non-skipping clip segments for a given video duration.
        - Automatically detects number of clips.
        - Exact 60s clips where possible.
        - Shorter final clip if remaining duration is < 60s.
        - Never loses final portion.
        - Handles videos <= 60s as a single clip.
        """
        if duration <= 0 or clip_duration <= 0:
            return []

        segments: List[ClipSegment] = []
        current_time = 0.0
        clip_index = 1

        # Determine zero-padding width based on estimated total clips
        estimated_total = max(1, math.ceil(duration / clip_duration))
        pad_width = max(2, len(str(estimated_total)))

        while current_time < duration:
            remaining = duration - current_time
            # If the remainder is minuscule (<0.05 seconds), don't produce a redundant micro-clip
            if remaining < 0.05:
                break

            seg_duration = min(clip_duration, remaining)
            end_time = current_time + seg_duration

            # Guard against floating-point inaccuracies pushing beyond duration
            if end_time > duration:
                end_time = duration
                seg_duration = end_time - current_time

            filename = f"short_{clip_index:0{pad_width}d}.mp4"
            segments.append(
                ClipSegment(
                    index=clip_index,
                    start_time=round(current_time, 3),
                    duration=round(seg_duration, 3),
                    end_time=round(end_time, 3),
                    filename=filename,
                )
            )

            current_time = end_time
            clip_index += 1

        return segments

    def build_ffmpeg_args(
        self,
        input_path: Path,
        clip: ClipSegment,
        output_path: Path,
        format_mode: str,
        has_audio: bool,
        stream_copy_original: bool = False,
        crf: int = 18,
        preset: str = "fast",
    ) -> List[str]:
        """
        Construct argument list for FFmpeg command without using shell=True.
        Supports:
          - 'original': Keeps original dimensions and aspect ratio.
          - 'vertical_blur': 9:16 (1080x1920) with blurred background and fitted foreground.
          - 'vertical_crop': 9:16 (1080x1920) center crop preserving subject.
        """
        args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]

        # Fast and accurate seek: specify start before -i, duration with -t
        args.extend(["-ss", f"{clip.start_time:.3f}"])
        args.extend(["-i", str(input_path.resolve())])
        args.extend(["-t", f"{clip.duration:.3f}"])

        # Timestamp normalization
        args.extend(["-avoid_negative_ts", "make_zero"])

        if format_mode == "original" and stream_copy_original:
            # Stream copy mode: fast cut without re-encoding
            args.extend(["-c", "copy"])
        elif format_mode == "original":
            # High-quality accurate re-encode
            args.extend(
                [
                    "-c:v",
                    "libx264",
                    "-crf",
                    str(crf),
                    "-preset",
                    preset,
                    "-pix_fmt",
                    "yuv420p",
                ]
            )
            if has_audio:
                args.extend(["-map", "0:v:0", "-map", "0:a:0?", "-c:a", "aac", "-b:a", "192k"])
            else:
                args.extend(["-map", "0:v:0", "-an"])

        elif format_mode == "vertical_blur":
            # 9:16 vertical Shorts with blurred background & centered full video
            filter_complex = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=20:5[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
            )
            args.extend(["-filter_complex", filter_complex])
            args.extend(["-map", "[v]"])
            args.extend(
                [
                    "-c:v",
                    "libx264",
                    "-crf",
                    str(crf),
                    "-preset",
                    preset,
                    "-pix_fmt",
                    "yuv420p",
                ]
            )
            if has_audio:
                args.extend(["-map", "0:a:0?", "-c:a", "aac", "-b:a", "192k"])
            else:
                args.extend(["-an"])

        elif format_mode == "vertical_crop":
            # 9:16 vertical Shorts center crop
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
            args.extend(["-vf", vf])
            args.extend(
                [
                    "-c:v",
                    "libx264",
                    "-crf",
                    str(crf),
                    "-preset",
                    preset,
                    "-pix_fmt",
                    "yuv420p",
                ]
            )
            if has_audio:
                args.extend(["-map", "0:v:0", "-map", "0:a:0?", "-c:a", "aac", "-b:a", "192k"])
            else:
                args.extend(["-map", "0:v:0", "-an"])
        else:
            raise ValueError(f"Unknown format mode: {format_mode}")

        # Web optimization for smooth YouTube upload playback
        args.extend(["-movflags", "+faststart"])
        args.append(str(output_path.resolve()))
        return args

    def render_clip(
        self,
        input_path: Path,
        clip: ClipSegment,
        output_path: Path,
        format_mode: str,
        has_audio: bool,
        stream_copy_original: bool = False,
        crf: int = 18,
        preset: str = "fast",
        on_status: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Render a single clip to the target output path.
        Returns: (success: bool, message: str)
        Gracefully handles cancellation (Ctrl+C) and cleans up partial files.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = self.build_ffmpeg_args(
            input_path=input_path,
            clip=clip,
            output_path=output_path,
            format_mode=format_mode,
            has_audio=has_audio,
            stream_copy_original=stream_copy_original,
            crf=crf,
            preset=preset,
        )

        if on_status:
            on_status("Encoding...")

        proc = None
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            _, stderr = proc.communicate()

            if proc.returncode != 0:
                if output_path.exists():
                    output_path.unlink(missing_ok=True)
                err_text = stderr.strip() if stderr else "Unknown FFmpeg error"
                return False, f"FFmpeg failed (code {proc.returncode}): {err_text}"

        except KeyboardInterrupt:
            if proc:
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except Exception:
                    pass
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            raise

        except Exception as exc:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return False, f"Process execution failed: {str(exc)}"

        # Verification step
        if on_status:
            on_status("Verifying...")

        valid, verify_msg = self.verify_clip(output_path, clip.duration, has_audio)
        if not valid:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return False, f"Verification failed: {verify_msg}"

        return True, "Success"

    def verify_clip(
        self, clip_path: Path, expected_duration: float, should_have_audio: bool
    ) -> Tuple[bool, str]:
        """
        Verify that the output clip file exists, is non-empty, and contains valid streams.
        """
        if not clip_path.exists():
            return False, "Output file does not exist."

        size = clip_path.stat().st_size
        if size < 1024:  # less than 1KB is definitely invalid
            return False, f"Output file is suspiciously small ({size} bytes)."

        try:
            info = self.probe_video(clip_path)
        except Exception as exc:
            return False, f"ffprobe could not validate output: {exc}"

        # Duration check with generous tolerance (±2.5 seconds or keyframe variance)
        tolerance = 2.5
        if abs(info.duration - expected_duration) > tolerance and info.duration < (expected_duration * 0.8):
            return (
                False,
                f"Duration mismatch: expected {expected_duration:.2f}s, got {info.duration:.2f}s",
            )

        if should_have_audio and not info.has_audio:
            return False, "Source contains audio, but output clip is missing audio."

        return True, "Valid"


def get_available_source_candidates() -> List[Path]:
    """
    Search for possible input video files in canonical and common locations:
    e.g. video/video.mp4, videos/video.mp4, videos/video.mp4.mkv, etc.
    """
    candidates: List[Path] = []
    canonical = Path("video/video.mp4")
    if canonical.exists():
        candidates.append(canonical)

    search_dirs = [Path("video"), Path("videos"), Path(".")]
    valid_exts = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}

    for s_dir in search_dirs:
        if s_dir.exists() and s_dir.is_dir():
            for item in s_dir.iterdir():
                if item.is_file() and item.suffix.lower() in valid_exts:
                    if item not in candidates:
                        candidates.append(item)

    return candidates
