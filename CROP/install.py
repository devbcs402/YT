"""
Automatic Project Setup & Dependency Installer for YouTube Shorts Splitter.
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

    if v.major < 3 or (v.major == 3 and v.minor < 8):
        print(f"  {RED}[ERROR] Python 3.8 or newer is required.{RESET}")
        return False

    return True


def install_python_dependencies() -> bool:
    """Install required Python packages automatically, just like npm install."""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print(f"  {YELLOW}No requirements.txt found. Skipping pip install.{RESET}")
        return True

    print(f"  Installing required packages from requirements.txt...")
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
            print(f"  {GREEN}[OK] All Python libraries installed successfully.{RESET}")
            return True
        else:
            err_msg = proc.stderr.strip() or proc.stdout.strip()
            print(f"  {RED}[ERROR] Failed to install packages via pip:{RESET}\n{err_msg}")
            return False
    except Exception as exc:
        print(f"  {YELLOW}[NOTE] Pip execution note: {exc}{RESET}")
        return True


def check_and_configure_multimedia() -> bool:
    """Verify FFmpeg and detect native hardware acceleration."""
    from video_processor import check_ffmpeg_installed

    ffmpeg_ok, ffprobe_ok, msg = check_ffmpeg_installed()
    if not ffmpeg_ok:
        print(f"  {RED}{BOLD}[!] FFmpeg is missing!{RESET}")
        print(f"    {msg}")
        return False

    print(f"  {GREEN}[OK] FFmpeg command is available and working.{RESET}")
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

    print_step(2, total_steps, "Installing required Python packages (requirements.txt)...")
    if not install_python_dependencies():
        print(f"{YELLOW}Warning: Proceeding with existing packages...{RESET}")

    print_step(3, total_steps, "Verifying FFmpeg multimedia tools...")
    if not check_and_configure_multimedia():
        print(f"\n{RED}{BOLD}Setup incomplete. Please ensure FFmpeg is installed.{RESET}")
        sys.exit(1)

    print_step(4, total_steps, "Initializing project folders & configuration...")
    if not setup_directories_and_config():
        sys.exit(1)

    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{GREEN}{BOLD}       ALL DEPENDENCIES & SETUP COMPLETED SUCCESSFULLY!       {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"\n{BOLD}To start the video splitter, run:{RESET}")
    print(f"  {GREEN}{BOLD}python main.py{RESET}\n")
    print(f"{DIM}Place your source video in: {YELLOW}video/video.mp4{RESET}\n")


if __name__ == "__main__":
    main()
