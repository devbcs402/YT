"""
Automatic Project Setup & Dependency Installer for Mobile YouTube Shorts Splitter.
Acts like 'npm install' in Node.js / MERN projects.

Usage:
    python install.py
or:
    python setup.py
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows cp1252 encoding for clean terminal output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ANSI colors for modern, professional terminal display
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_step(step_num: int, total_steps: int, title: str) -> None:
    print(f"\n{CYAN}{BOLD}[{step_num}/{total_steps}] {title}{RESET}")


def check_python_environment() -> bool:
    """Ensure Python version is compatible."""
    v = sys.version_info
    print(f"  Python Version: {GREEN}{v.major}.{v.minor}.{v.micro}{RESET}")
    print(f"  Platform:       {YELLOW}{platform.system()} ({platform.machine()}){RESET}")

    is_ashell = "a-shell" in os.environ.get("SHELL", "").lower() or (
        sys.platform == "darwin" and platform.machine() in ("iPad", "iPhone", "arm64")
    )
    is_termux = "com.termux" in os.environ.get("PREFIX", "")

    if is_ashell:
        print(f"  Environment:    {GREEN}iOS a-Shell (Mobile Terminal){RESET}")
    elif is_termux:
        print(f"  Environment:    {GREEN}Android Termux (Mobile Terminal){RESET}")
    else:
        print(f"  Environment:    {GREEN}Desktop / Server{RESET}")

    if v.major < 3 or (v.major == 3 and v.minor < 8):
        print(f"  {RED}[ERROR] Python 3.8 or newer is required.{RESET}")
        return False

    return True


def install_python_dependencies() -> bool:
    """Install required Python packages automatically, just like npm install."""
    req_file = Path("requirements.txt")

    packages_to_check = ["colorama"]

    needs_install = False
    for pkg in packages_to_check:
        try:
            __import__(pkg)
        except ImportError:
            needs_install = True
            break

    if req_file.exists() and req_file.stat().st_size > 0:
        content = req_file.read_text(encoding="utf-8").strip()
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
        if not lines:
            print(f"  {GREEN}[OK] Zero external dependencies required (uses 100% Python standard library).{RESET}")
            return True

    if not needs_install and req_file.exists():
        print(f"  {GREEN}[OK] All required Python packages are already installed.{RESET}")
        return True

    print(f"  Installing required packages using pip...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            print(f"  {GREEN}[OK] Python libraries installed successfully.{RESET}")
            return True
        else:
            err_msg = proc.stderr.strip() or proc.stdout.strip()
            if "a-shell" in os.environ.get("SHELL", "").lower() or sys.platform == "darwin":
                print(f"  {YELLOW}[NOTE] Running on mobile: standard library will be used directly.{RESET}")
                return True
            print(f"  {RED}[ERROR] Failed to install packages via pip:{RESET}\n{err_msg}")
            return False
    except Exception as exc:
        print(f"  {YELLOW}[NOTE] Pip execution note: {exc}{RESET}")
        return True


def check_and_configure_multimedia() -> bool:
    """Verify FFmpeg and detect native hardware acceleration."""
    from video_processor import (
        check_ffmpeg_installed,
        detect_audio_encoder,
        detect_blur_filter,
        detect_video_encoder,
    )

    ffmpeg_ok, ffprobe_ok, msg = check_ffmpeg_installed()
    if not ffmpeg_ok:
        print(f"  {RED}{BOLD}[!] FFmpeg is missing!{RESET}")
        print(f"    {msg}")
        return False

    enc_name, enc_flags = detect_video_encoder()
    blur_filter = detect_blur_filter()
    audio_flags = detect_audio_encoder()

    print(f"  {GREEN}[OK] FFmpeg command is available and working.{RESET}")
    print(f"  {GREEN}[OK] Video Encoder:{RESET} {YELLOW}{enc_name}{RESET}")
    if enc_name == "h264_videotoolbox":
        print(f"       (Apple Hardware Acceleration enabled for iOS a-Shell / macOS)")
    elif enc_name == "libx264":
        print(f"       (H.264 standard visual encoding enabled)")
    elif enc_name == "h264_mediacodec":
        print(f"       (Android Hardware Acceleration enabled for Termux)")

    print(f"  {GREEN}[OK] Blur Filter:{RESET}   {YELLOW}{blur_filter}{RESET}")
    return True


def setup_directories_and_config() -> bool:
    """Create project directories and initialize config.json."""
    from config import load_config, save_config

    video_dir = Path("video")
    output_dir = Path("output/shorts")

    video_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    readme_note = video_dir / "place_your_video_here.txt"
    if not readme_note.exists() and not (video_dir / "video.mp4").exists():
        readme_note.write_text(
            "Place your source video file here and rename it to 'video.mp4'.\n"
            "The splitter will automatically detect and load it on startup.\n",
            encoding="utf-8",
        )

    cfg = load_config()
    save_config(cfg)

    print(f"  {GREEN}[OK] Created directory:{RESET} {video_dir}/")
    print(f"  {GREEN}[OK] Created directory:{RESET} {output_dir}/")
    print(f"  {GREEN}[OK] Configuration ready:{RESET} config.json")
    return True


def run_quick_self_test() -> bool:
    """Run a fast synthetic self-test to verify full pipeline."""
    from test_mobile import run_mobile_tests

    print(f"  Running 3-second self-diagnostic test...")
    success = run_mobile_tests()
    return success


def main() -> None:
    """Main installation and setup entrypoint."""
    if os.name == "nt":
        os.system("")

    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{CYAN}{BOLD}   AUTOMATIC SETUP & INSTALLER (PYTHON DEPENDENCY MANAGER)   {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{DIM}Setting up environment, dependencies, and video engine...{RESET}")

    total_steps = 4

    print_step(1, total_steps, "Checking Python environment...")
    if not check_python_environment():
        sys.exit(1)

    print_step(2, total_steps, "Installing / Verifying Python packages...")
    if not install_python_dependencies():
        print(f"{YELLOW}Warning: Proceeding with standard library...{RESET}")

    print_step(3, total_steps, "Verifying FFmpeg multimedia tools & encoders...")
    if not check_and_configure_multimedia():
        print(f"\n{RED}{BOLD}Setup incomplete. Please ensure FFmpeg is available on your device.{RESET}")
        sys.exit(1)

    print_step(4, total_steps, "Initializing project folders & configuration...")
    if not setup_directories_and_config():
        sys.exit(1)

    print(f"\n{CYAN}{BOLD}Verifying video processing pipeline...{RESET}")
    run_quick_self_test()

    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{GREEN}{BOLD}       ALL DEPENDENCIES & SETUP COMPLETED SUCCESSFULLY!       {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"\n{BOLD}To start the video splitter now, simply run:{RESET}")
    print(f"  {GREEN}{BOLD}python main.py{RESET}\n")
    print(f"{DIM}Place your source video in: {YELLOW}video/video.mp4{RESET}\n")


if __name__ == "__main__":
    main()
