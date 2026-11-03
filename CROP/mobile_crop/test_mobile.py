"""
One-Time Self-Diagnostic and Verification Test Suite for Mobile YouTube Shorts Splitter.
Designed to run on mobile (iOS a-Shell, Android Termux) or desktop.
Zero external dependencies - uses standard library and local FFmpeg.

Run via:
    python test_mobile.py
or:
    python main.py --test
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from config import MobileAppConfig, load_config, save_config
from video_processor import (
    ClipSegment,
    MobileVideoProcessor,
    check_ffmpeg_installed,
    format_duration,
    format_timestamp,
)

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_step(title: str) -> None:
    print(f"\n{CYAN}{BOLD}---> [TEST] {title}{RESET}")


def create_synthetic_test_video(output_file: Path, duration: float = 5.0) -> bool:
    """
    Generate a 1280x720 30fps test video with audio using FFmpeg's built-in lavfi filters.
    Requires no external assets.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration}:size=1280x720:rate=30",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=1000:duration={duration}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(output_file.resolve()),
    ]
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return proc.returncode == 0 and output_file.exists() and output_file.stat().st_size > 1000
    except Exception as exc:
        print(f"{RED}Failed to create synthetic test video: {exc}{RESET}")
        return False


def run_mobile_tests() -> bool:
    """Run complete suite of mobile self-tests."""
    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{CYAN}{BOLD}   MOBILE YOUTUBE SHORTS SPLITTER - SELF-DIAGNOSTIC TEST   {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")

    test_dir = Path("mobile_test_workspace")
    test_dir.mkdir(parents=True, exist_ok=True)

    passed_count = 0
    total_count = 7

    # -------------------------------------------------------------
    # 1. FFmpeg & ffprobe environment check
    # -------------------------------------------------------------
    print_step("1. Checking FFmpeg & ffprobe availability...")
    ffmpeg_ok, ffprobe_ok, msg = check_ffmpeg_installed()
    if ffmpeg_ok and ffprobe_ok:
        print(f"  {GREEN}[PASS]{RESET} FFmpeg and ffprobe are functioning correctly.")
        passed_count += 1
    else:
        print(f"  {RED}[FAIL]{RESET} {msg}")
        return False

    # -------------------------------------------------------------
    # 2. Config system test
    # -------------------------------------------------------------
    print_step("2. Testing configuration load, save & fallback...")
    test_cfg_path = test_dir / "test_config.json"
    cfg = load_config(test_cfg_path)
    cfg.clip_duration = 60
    cfg.video_format = "vertical_blur"
    save_config(cfg, test_cfg_path)

    reloaded = load_config(test_cfg_path)
    if reloaded.clip_duration == 60 and reloaded.video_format == "vertical_blur":
        print(f"  {GREEN}[PASS]{RESET} Configuration persistence verified.")
        passed_count += 1
    else:
        print(f"  {RED}[FAIL]{RESET} Configuration load/save mismatch.")

    # -------------------------------------------------------------
    # 3. Clip duration algorithm test
    # -------------------------------------------------------------
    print_step("3. Testing 60-second clip calculation algorithm...")
    processor = MobileVideoProcessor()

    # 10 minute video (600s) -> 10 clips
    clips_10m = processor.calculate_clips(600.0, 60.0)
    # 10m 30s video (630s) -> 11 clips (10x60s + 1x30s remainder)
    clips_10m30s = processor.calculate_clips(630.0, 60.0)
    # 45s video -> 1 clip
    clips_45s = processor.calculate_clips(45.0, 60.0)

    cond1 = len(clips_10m) == 10 and all(c.duration == 60.0 for c in clips_10m)
    cond2 = len(clips_10m30s) == 11 and clips_10m30s[-1].duration == 30.0
    cond3 = len(clips_45s) == 1 and clips_45s[0].duration == 45.0

    if cond1 and cond2 and cond3:
        print(f"  {GREEN}[PASS]{RESET} 10m -> 10 clips (00:00-10:00).")
        print(f"  {GREEN}[PASS]{RESET} 10m 30s -> 11 clips (10x60s + 30s remainder).")
        print(f"  {GREEN}[PASS]{RESET} 45s -> 1 single clip without data loss.")
        passed_count += 1
    else:
        print(f"  {RED}[FAIL]{RESET} Clip calculation error.")

    # -------------------------------------------------------------
    # 4. Synthetic video generation and ffprobe probing test
    # -------------------------------------------------------------
    print_step("4. Generating synthetic test video and probing metadata...")
    sample_video = test_dir / "sample_test.mp4"
    if not create_synthetic_test_video(sample_video, duration=4.0):
        print(f"  {RED}[FAIL]{RESET} Could not generate test video.")
        shutil.rmtree(test_dir, ignore_errors=True)
        return False

    info = processor.probe_video(sample_video)
    if info.width == 1280 and info.height == 720 and info.has_audio and abs(info.duration - 4.0) < 1.0:
        print(f"  {GREEN}[PASS]{RESET} Probed: {info.width}x{info.height}, {info.formatted_duration}, audio={info.has_audio}")
        passed_count += 1
    else:
        print(f"  {RED}[FAIL]{RESET} Probing returned incorrect values: {info}")

    # -------------------------------------------------------------
    # 5. Render Mode A (Preserve Original)
    # -------------------------------------------------------------
    print_step("5. Rendering Mode A (Preserve original dimensions)...")
    clip_a = ClipSegment(index=1, start_time=0.0, duration=2.0, end_time=2.0, filename="out_mode_a.mp4")
    out_a = test_dir / clip_a.filename

    ok_a, msg_a = processor.render_clip(
        input_path=sample_video,
        clip=clip_a,
        output_path=out_a,
        format_mode="original",
        has_audio=True,
        preset="ultrafast",
        crf=23,
    )

    if ok_a and out_a.exists():
        info_a = processor.probe_video(out_a)
        if info_a.width == 1280 and info_a.height == 720 and info_a.has_audio:
            print(f"  {GREEN}[PASS]{RESET} Mode A generated: {info_a.resolution_str}, audio verified.")
            passed_count += 1
        else:
            print(f"  {RED}[FAIL]{RESET} Mode A stream mismatch: {info_a.resolution_str}")
    else:
        print(f"  {RED}[FAIL]{RESET} Mode A rendering failed: {msg_a}")

    # -------------------------------------------------------------
    # 6. Render Mode B (Vertical Shorts 9:16 Blurred Background)
    # -------------------------------------------------------------
    print_step("6. Rendering Mode B (Vertical Shorts 9:16 - Blurred Background)...")
    clip_b = ClipSegment(index=2, start_time=1.0, duration=2.0, end_time=3.0, filename="out_mode_b_blur.mp4")
    out_b = test_dir / clip_b.filename

    ok_b, msg_b = processor.render_clip(
        input_path=sample_video,
        clip=clip_b,
        output_path=out_b,
        format_mode="vertical_blur",
        has_audio=True,
        resolution="720x1280",  # Test mobile 720x1280 vertical
        preset="ultrafast",
        crf=23,
    )

    if ok_b and out_b.exists():
        info_b = processor.probe_video(out_b)
        if info_b.width == 720 and info_b.height == 1280 and info_b.has_audio:
            print(f"  {GREEN}[PASS]{RESET} Mode B Blurred BG generated: {info_b.resolution_str} (9:16 vertical), audio verified.")
            passed_count += 1
        else:
            print(f"  {RED}[FAIL]{RESET} Mode B Blurred BG stream mismatch: {info_b.resolution_str}")
    else:
        print(f"  {RED}[FAIL]{RESET} Mode B Blurred BG rendering failed: {msg_b}")

    # -------------------------------------------------------------
    # 7. Render Mode B (Vertical Shorts 9:16 Center Crop)
    # -------------------------------------------------------------
    print_step("7. Rendering Mode B (Vertical Shorts 9:16 - Center Crop)...")
    clip_c = ClipSegment(index=3, start_time=1.0, duration=2.0, end_time=3.0, filename="out_mode_b_crop.mp4")
    out_c = test_dir / clip_c.filename

    ok_c, msg_c = processor.render_clip(
        input_path=sample_video,
        clip=clip_c,
        output_path=out_c,
        format_mode="vertical_crop",
        has_audio=True,
        resolution="720x1280",
        preset="ultrafast",
        crf=23,
    )

    if ok_c and out_c.exists():
        info_c = processor.probe_video(out_c)
        if info_c.width == 720 and info_c.height == 1280 and info_c.has_audio:
            print(f"  {GREEN}[PASS]{RESET} Mode B Center Crop generated: {info_c.resolution_str} (9:16 vertical), audio verified.")
            passed_count += 1
        else:
            print(f"  {RED}[FAIL]{RESET} Mode B Center Crop stream mismatch: {info_c.resolution_str}")
    else:
        print(f"  {RED}[FAIL]{RESET} Mode B Center Crop rendering failed: {msg_c}")

    # Clean up workspace
    shutil.rmtree(test_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # Final Result
    # -------------------------------------------------------------
    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    if passed_count == total_count:
        print(f"{GREEN}{BOLD}   >>> ALL {passed_count}/{total_count} DIAGNOSTIC TESTS PASSED SUCCESSFULLY! <<<{RESET}")
        print(f"{GREEN}Your mobile / a-Shell environment is 100% verified and ready to run.{RESET}")
        print(f"{CYAN}{BOLD}{'=' * 65}{RESET}\n")
        return True
    else:
        print(f"{RED}{BOLD}   >>> {passed_count}/{total_count} TESTS PASSED. PLEASE CHECK THE ERRORS ABOVE. <<<{RESET}")
        print(f"{CYAN}{BOLD}{'=' * 65}{RESET}\n")
        return False


if __name__ == "__main__":
    success = run_mobile_tests()
    sys.exit(0 if success else 1)

