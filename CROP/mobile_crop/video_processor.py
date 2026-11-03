"""
Video processor module for Mobile YouTube Shorts Video Splitter.
Features adaptive mobile encoder detection (Apple VideoToolbox / libx264),
pure-FFmpeg metadata probing (zero ffprobe dependency required),
and mobile-resilient video filtering.
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
    """Format duration into a friendly string."""
    total_seconds = int(round(seconds))
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    rem_secs = total_seconds % 60
    if hrs > 0:
        return f"{hrs}h {mins}m {rem_secs}s ({format_timestamp(seconds)})"
    return f"{mins}m {rem_secs}s ({format_timestamp(seconds)})"


def format_file_size(bytes_count: int) -> str:
    """Format bytes into readable KB, MB, or GB string."""
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    if bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def check_ffmpeg_installed() -> Tuple[bool, bool, str]:
    """
    Check if ffmpeg is available.
    Supports both traditional PATH binaries and mobile embedded environments (e.g., iOS a-Shell).
    Returns: (ffmpeg_found, ffprobe_found, detailed_status_or_guide)
    Note: ffprobe is OPTIONAL since this module has built-in pure FFmpeg fallback probing.
    """
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffprobe_ok = shutil.which("ffprobe") is not None

    if not ffmpeg_ok:
        try:
            res = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if res.returncode == 0:
                ffmpeg_ok = True
        except Exception:
            pass

    if not ffprobe_ok:
        try:
            res = subprocess.run(
                ["ffprobe", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if res.returncode == 0:
                ffprobe_ok = True
        except Exception:
            pass

    if ffmpeg_ok:
        probe_status = "ffprobe active" if ffprobe_ok else "pure FFmpeg parser active"
        return True, ffprobe_ok, f"FFmpeg is available ({probe_status})."

    # FFmpeg is completely missing
    if sys.platform == "darwin" or "a-shell" in os.environ.get("SHELL", "").lower():
        instructions = (
            "[ERROR] FFmpeg command not found in your mobile environment.\n\n"
            "On iOS:\n"
            "  - Install 'a-Shell' from the App Store.\n"
            "  - In a-Shell, test running 'ffmpeg -version'.\n"
        )
    elif os.name == "nt":
        instructions = (
            "[ERROR] FFmpeg missing from PATH.\n\n"
            "Install FFmpeg on Windows via PowerShell:\n"
            "  winget install Gyan.FFmpeg\n"
        )
    else:
        instructions = (
            "[ERROR] FFmpeg missing.\n\n"
            "Install on Android Termux: pkg install ffmpeg\n"
            "Install on Ubuntu/Debian:  sudo apt install ffmpeg\n"
        )

    return False, ffprobe_ok, instructions


# Cache detected capabilities so we don't query subprocess repeatedly
_CACHED_ENCODER_INFO: Optional[Tuple[str, List[str]]] = None
_CACHED_AUDIO_INFO: Optional[List[str]] = None
_CACHED_BLUR_FILTER: Optional[str] = None


def detect_video_encoder() -> Tuple[str, List[str]]:
    """
    Detect the best working H.264 video encoder on this device:
    - On iOS (a-Shell): 'h264_videotoolbox' (Apple hardware accelerated, no GPL libx264)
    - On Android / Linux / Windows: 'libx264' (software) or 'h264_mediacodec'
    - Fallback: default FFmpeg encoder
    Returns: (encoder_name, encoder_cli_flags)
    """
    global _CACHED_ENCODER_INFO
    if _CACHED_ENCODER_INFO is not None:
        return _CACHED_ENCODER_INFO

    try:
        proc = subprocess.run(
            ["ffmpeg", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        stdout = proc.stdout or ""
    except Exception:
        stdout = ""

    if "h264_videotoolbox" in stdout:
        # Apple VideoToolbox (iOS / macOS hardware accelerated)
        # Note: VideoToolbox uses -b:v or -q:v, does NOT accept -crf or -preset
        _CACHED_ENCODER_INFO = (
            "h264_videotoolbox",
            ["-c:v", "h264_videotoolbox", "-b:v", "4M", "-pix_fmt", "yuv420p"],
        )
    elif "libx264" in stdout:
        _CACHED_ENCODER_INFO = (
            "libx264",
            ["-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p"],
        )
    elif "h264_mediacodec" in stdout:
        _CACHED_ENCODER_INFO = (
            "h264_mediacodec",
            ["-c:v", "h264_mediacodec", "-b:v", "4M", "-pix_fmt", "yuv420p"],
        )
    else:
        _CACHED_ENCODER_INFO = (
            "default",
            ["-pix_fmt", "yuv420p"],
        )

    return _CACHED_ENCODER_INFO


def detect_audio_encoder() -> List[str]:
    """Detect available AAC or compatible audio encoder."""
    global _CACHED_AUDIO_INFO
    if _CACHED_AUDIO_INFO is not None:
        return _CACHED_AUDIO_INFO

    try:
        proc = subprocess.run(
            ["ffmpeg", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        stdout = proc.stdout or ""
    except Exception:
        stdout = ""

    if " aac " in stdout or "aac" in stdout:
        _CACHED_AUDIO_INFO = ["-c:a", "aac", "-b:a", "192k"]
    else:
        _CACHED_AUDIO_INFO = ["-c:a", "copy"]

    return _CACHED_AUDIO_INFO


def detect_blur_filter() -> str:
    """Detect working blur filter (boxblur vs gblur vs subtle dimming)."""
    global _CACHED_BLUR_FILTER
    if _CACHED_BLUR_FILTER is not None:
        return _CACHED_BLUR_FILTER

    try:
        proc = subprocess.run(
            ["ffmpeg", "-filters"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        stdout = proc.stdout or ""
    except Exception:
        stdout = ""

    if "boxblur" in stdout:
        _CACHED_BLUR_FILTER = "boxblur=20:5"
    elif "gblur" in stdout:
        _CACHED_BLUR_FILTER = "gblur=sigma=20"
    else:
        # Fallback if no blur filter was compiled into mobile build
        _CACHED_BLUR_FILTER = "eq=brightness=-0.3"

    return _CACHED_BLUR_FILTER


class MobileVideoProcessor:
    """Mobile and desktop video processor with adaptive encoder & fallback probing."""

    def __init__(self) -> None:
        pass

    def probe_video(self, video_path: Path) -> VideoInfo:
        """
        Probe input video file.
        Attempts ffprobe first; if ffprobe is missing (e.g. on iOS a-Shell),
        seamlessly parses metadata from pure FFmpeg output.
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

        # Check if ffprobe is callable
        has_ffprobe = shutil.which("ffprobe") is not None
        if not has_ffprobe:
            try:
                res = subprocess.run(
                    ["ffprobe", "-version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                has_ffprobe = res.returncode == 0
            except Exception:
                has_ffprobe = False

        if has_ffprobe:
            try:
                return self._probe_with_ffprobe(video_path, file_size)
            except Exception:
                # If ffprobe fails for any reason, fall back to pure FFmpeg
                pass

        return self._probe_with_ffmpeg(video_path, file_size)

    def _probe_with_ffprobe(self, video_path: Path, file_size: int) -> VideoInfo:
        """Probe metadata using ffprobe JSON output."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(video_path.resolve()),
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise ValueError(result.stderr.strip() or "ffprobe error")

        data = json.loads(result.stdout)
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = None
        audio_stream = None
        for stream in streams:
            codec_type = stream.get("codec_type")
            if codec_type == "video" and video_stream is None:
                video_stream = stream
            elif codec_type == "audio" and audio_stream is None:
                audio_stream = stream

        if not video_stream:
            raise ValueError(f"No video stream found in '{video_path.name}'.")

        duration_str = format_info.get("duration") or video_stream.get("duration")
        if not duration_str or float(duration_str) <= 0:
            if audio_stream and audio_stream.get("duration"):
                duration_str = audio_stream.get("duration")
            else:
                raise ValueError("Could not determine video duration.")

        duration = float(duration_str)
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        dar = video_stream.get("display_aspect_ratio")
        if not dar and width > 0 and height > 0:
            gcd = math.gcd(width, height)
            dar = f"{width // gcd}:{height // gcd}"
        elif not dar:
            dar = "Unknown"

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
        audio_sr = int(audio_stream.get("sample_rate", 0)) if audio_stream else None

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

    def _probe_with_ffmpeg(self, video_path: Path, file_size: int) -> VideoInfo:
        """
        Pure FFmpeg fallback video metadata parser.
        Works in environments where ffprobe is missing (e.g. iOS a-Shell).
        """
        cmd = ["ffmpeg", "-hide_banner", "-i", str(video_path.resolve())]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        stderr = proc.stderr or ""

        # Duration match: Duration: 00:05:23.45, start: 0.000000, bitrate: 1234 kb/s
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
        if not dur_match:
            raise ValueError(
                f"Could not determine video duration for '{video_path.name}' using FFmpeg."
            )

        hrs, mins, secs = dur_match.groups()
        duration = int(hrs) * 3600 + int(mins) * 60 + float(secs)

        # Resolution & Video stream
        v_match = re.search(r"Stream.*Video:\s*([^\s,]+).*?,\s*(\d{2,5})x(\d{2,5})", stderr)
        if not v_match:
            raise ValueError(f"No video stream found in '{video_path.name}'.")

        video_codec = v_match.group(1)
        width = int(v_match.group(2))
        height = int(v_match.group(3))

        fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", stderr)
        fps = float(fps_match.group(1)) if fps_match else 30.0

        dar_match = re.search(r"DAR\s*(\d+:\d+)", stderr)
        if dar_match:
            dar = dar_match.group(1)
        elif width > 0 and height > 0:
            gcd = math.gcd(width, height)
            dar = f"{width // gcd}:{height // gcd}"
        else:
            dar = "Unknown"

        bitrate_match = re.search(r"bitrate:\s*(\d+)\s*kb/s", stderr)
        bitrate = int(bitrate_match.group(1)) * 1000 if bitrate_match else None

        a_match = re.search(r"Stream.*Audio:\s*([^\s,]+)", stderr)
        has_audio = a_match is not None
        audio_codec = a_match.group(1) if a_match else None

        sr_match = re.search(r"(\d+)\s*Hz", stderr)
        audio_sr = int(sr_match.group(1)) if sr_match else None

        ch_match = re.search(r"(stereo|mono|(\d+)\s*channels)", stderr)
        audio_channels = (
            2
            if ch_match and "stereo" in ch_match.group(1)
            else (1 if ch_match and "mono" in ch_match.group(1) else None)
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
        """Calculate sequential, non-overlapping 60s segments without losing remainder."""
        if duration <= 0 or clip_duration <= 0:
            return []

        segments: List[ClipSegment] = []
        current_time = 0.0
        clip_index = 1

        estimated_total = max(1, math.ceil(duration / clip_duration))
        pad_width = max(2, len(str(estimated_total)))

        while current_time < duration:
            remaining = duration - current_time
            if remaining < 0.05:
                break

            seg_duration = min(clip_duration, remaining)
            end_time = current_time + seg_duration

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
        resolution: str = "1080x1920",
        stream_copy_original: bool = False,
        **kwargs,
    ) -> List[str]:
        """
        Build argument list for FFmpeg command.
        Uses adaptive mobile encoder detection (h264_videotoolbox on iOS, libx264 on desktop).
        """
        try:
            w_str, h_str = resolution.split("x")
            out_w, out_h = int(w_str), int(h_str)
        except Exception:
            out_w, out_h = 1080, 1920

        encoder_name, v_flags = detect_video_encoder()
        a_flags = detect_audio_encoder()
        blur_filter = detect_blur_filter()

        args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]

        args.extend(["-ss", f"{clip.start_time:.3f}"])
        args.extend(["-i", str(input_path.resolve())])
        args.extend(["-t", f"{clip.duration:.3f}"])
        args.extend(["-avoid_negative_ts", "make_zero"])

        if format_mode == "original" and stream_copy_original:
            args.extend(["-c", "copy"])
        elif format_mode == "original":
            args.extend(v_flags)
            if has_audio:
                args.extend(["-map", "0:v:0", "-map", "0:a:0?"])
                args.extend(a_flags)
            else:
                args.extend(["-map", "0:v:0", "-an"])

        elif format_mode == "vertical_blur":
            filter_complex = (
                f"[0:v]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
                f"crop={out_w}:{out_h},{blur_filter}[bg];"
                f"[0:v]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
            )
            args.extend(["-filter_complex", filter_complex])
            args.extend(["-map", "[v]"])
            args.extend(v_flags)
            if has_audio:
                args.extend(["-map", "0:a:0?"])
                args.extend(a_flags)
            else:
                args.extend(["-an"])

        elif format_mode == "vertical_crop":
            vf = f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h}"
            args.extend(["-vf", vf])
            args.extend(v_flags)
            if has_audio:
                args.extend(["-map", "0:v:0", "-map", "0:a:0?"])
                args.extend(a_flags)
            else:
                args.extend(["-map", "0:v:0", "-an"])
        else:
            raise ValueError(f"Unknown format mode: {format_mode}")

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
        resolution: str = "1080x1920",
        stream_copy_original: bool = False,
        on_status: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> Tuple[bool, str]:
        """Encode a single clip to destination path with verification."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = self.build_ffmpeg_args(
            input_path=input_path,
            clip=clip,
            output_path=output_path,
            format_mode=format_mode,
            has_audio=has_audio,
            resolution=resolution,
            stream_copy_original=stream_copy_original,
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
                return False, f"FFmpeg error: {err_text}"

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
            return False, f"Execution failed: {str(exc)}"

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
        """Validate output clip file size, duration, and streams."""
        if not clip_path.exists():
            return False, "Output file does not exist."

        size = clip_path.stat().st_size
        if size < 1024:
            return False, f"Output file is suspiciously small ({size} bytes)."

        try:
            info = self.probe_video(clip_path)
        except Exception as exc:
            return False, f"Probe verification failed: {exc}"

        tolerance = 2.5
        if abs(info.duration - expected_duration) > tolerance and info.duration < (
            expected_duration * 0.8
        ):
            return (
                False,
                f"Duration mismatch: expected {expected_duration:.2f}s, got {info.duration:.2f}s",
            )

        if should_have_audio and not info.has_audio:
            return False, "Audio track is missing from output clip."

        return True, "Valid"


# Compatibility alias
VideoProcessor = MobileVideoProcessor


def find_candidate_videos() -> List[Path]:
    """Look for video files in video/, current dir, and parent dir."""
    candidates: List[Path] = []
    canonical = Path("video/video.mp4")
    if canonical.exists():
        candidates.append(canonical)

    search_dirs = [Path("video"), Path("."), Path("../video"), Path("..")]
    valid_exts = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}

    for s_dir in search_dirs:
        if s_dir.exists() and s_dir.is_dir():
            try:
                for item in s_dir.iterdir():
                    if item.is_file() and item.suffix.lower() in valid_exts:
                        if item not in candidates:
                            candidates.append(item)
            except Exception:
                pass

    return candidates
