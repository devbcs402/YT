#!/usr/bin/env python3
"""
Universal Video Downloader - Terminal Edition
Author: Senior Python Engineering
Environment: Windows / Cross-platform

Features:
- Automatic highest-quality video & audio download (up to 4K UHD)
- Separate stream merging via FFmpeg
- ffprobe stream verification (guarantees audio stream exists)
- Safe unique filename generation avoiding overwrites
- Real-time progress bar (percent, speed, ETA, size)
"""

import os
import sys
import time
from pathlib import Path

# Local modular imports
import config as config_mgr
import downloader


# ANSI Colors for Windows Terminal and modern shells
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"
    BG_BLUE = "\033[44m"


def enable_windows_ansi():
    """Enable ANSI escape sequences and UTF-8 output on Windows console."""
    if os.name == "nt":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


class TerminalProgressBar:
    """Live interactive console progress bar with speed, ETA, and percent."""
    def __init__(self):
        self.last_update = 0

    def hook(self, d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            percent = 0.0
            if total > 0:
                percent = (downloaded / total) * 100.0

            speed_val = d.get("speed")
            speed_str = f"{downloader.format_bytes(speed_val)}/s" if speed_val else "Calculating..."

            eta_val = d.get("eta")
            if eta_val is not None:
                mins, secs = divmod(int(eta_val), 60)
                eta_str = f"{mins:02d}:{secs:02d}"
            else:
                eta_str = "--:--"

            bar_len = 30
            filled = int(bar_len * percent / 100.0) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)

            # Throttle console refresh rate to ~10 times per second for smooth rendering
            now = time.time()
            if now - self.last_update >= 0.08 or percent >= 100.0:
                self.last_update = now
                sys.stdout.write(
                    f"\r{Style.CYAN}[DOWNLOADING]{Style.RESET} "
                    f"|{Style.GREEN}{bar}{Style.RESET}| "
                    f"{Style.BOLD}{percent:5.1f}%{Style.RESET} "
                    f"[{downloader.format_bytes(downloaded)} / {downloader.format_bytes(total)}] "
                    f"Speed: {Style.YELLOW}{speed_str}{Style.RESET} "
                    f"ETA: {Style.WHITE}{eta_str}{Style.RESET}  "
                )
                sys.stdout.flush()

        elif status == "finished":
            sys.stdout.write(
                f"\r{Style.CYAN}[DOWNLOADING]{Style.RESET} Stream transfer finished. "
                f"{Style.MAGENTA}[Merging Video & Audio via FFmpeg...]{Style.RESET}                \n"
            )
            sys.stdout.flush()


def show_banner(config, ffmpeg_info):
    """Display modern terminal banner with system status."""
    os.system("cls" if os.name == "nt" else "clear")
    download_dir = config.get("download_dir", config_mgr.DEFAULT_DOWNLOAD_DIR)
    ffmpeg_status = (
        f"{Style.GREEN}Available ({ffmpeg_info.get('version') or 'Installed'}){Style.RESET}"
        if ffmpeg_info.get("ffmpeg_available")
        else f"{Style.RED}NOT FOUND (Required for audio merging){Style.RESET}"
    )

    print(f"{Style.BOLD}{Style.CYAN}╔══════════════════════════════════════════════════════════════════╗{Style.RESET}")
    print(f"{Style.BOLD}{Style.CYAN}║         UNIVERSAL VIDEO DOWNLOADER - TERMINAL EDITION            ║{Style.RESET}")
    print(f"{Style.BOLD}{Style.CYAN}║              Automatic Highest-Quality Audio & Video             ║{Style.RESET}")
    print(f"{Style.BOLD}{Style.CYAN}╚══════════════════════════════════════════════════════════════════╝{Style.RESET}")
    print(f"  {Style.DIM}Download Folder:{Style.RESET}   {Style.BOLD}{download_dir}{Style.RESET}")
    print(f"  {Style.DIM}FFmpeg Engine:{Style.RESET}     {ffmpeg_status}")
    print(f"{Style.CYAN}────────────────────────────────────────────────────────────────────{Style.RESET}")


def handle_download_action(config):
    """Option 1: Download video from URL."""
    url = input(f"\n{Style.BOLD}Paste video URL to download: {Style.RESET}").strip()
    if not url:
        print(f"{Style.YELLOW}No URL provided. Returning to menu...{Style.RESET}")
        time.sleep(1)
        return

    print(f"\n{Style.CYAN}--> Analyzing video streams and metadata...{Style.RESET}")
    ffmpeg_info = downloader.check_ffmpeg_installed()

    try:
        info = downloader.inspect_video(url, ffmpeg_info)
    except Exception as e:
        print(f"\n{Style.RED}[ERROR] Could not inspect video:{Style.RESET} {e}")
        input(f"\n{Style.DIM}Press Enter to return to menu...{Style.RESET}")
        return

    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    duration = info.get("duration")
    dur_str = f"{int(duration // 60)}m {int(duration % 60)}s" if duration else "Unknown"
    formats = info.get("formats", [])
    has_audio = downloader.source_has_audio(info)

    print(f"\n{Style.BOLD}======================================================================{Style.RESET}")
    print(f"{Style.GREEN}{Style.BOLD}Video Details:{Style.RESET}")
    print(f"  • {Style.BOLD}Title:{Style.RESET}     {title}")
    print(f"  • {Style.BOLD}Uploader:{Style.RESET}  {uploader}")
    print(f"  • {Style.BOLD}Duration:{Style.RESET}  {dur_str}")
    print(f"  • {Style.BOLD}Audio:{Style.RESET}     {'Available (will be merged)' if has_audio else 'No audio track in source'}")
    print(f"{Style.BOLD}======================================================================{Style.RESET}")

    # Inspect unique resolutions
    video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("height")]
    video_formats.sort(key=lambda x: (x.get("height") or 0, x.get("fps") or 0), reverse=True)
    seen = set()
    res_list = []
    for f in video_formats:
        h = f.get("height")
        fps = f.get("fps")
        label = f"{h}p" + (f"{int(fps)}" if fps and fps > 30 else "")
        if label not in seen:
            seen.add(label)
            res_list.append(label)

    if res_list:
        print(f"  Available Qualities: {Style.BOLD}{', '.join(res_list[:6])}{Style.RESET}")
        max_h = video_formats[0].get("height", 0)
        if max_h >= 2160:
            print(f"  {Style.BG_BLUE}{Style.WHITE} 4K UHD Available {Style.RESET} (Will automatically download highest quality)")
        elif max_h >= 1080:
            print(f"  {Style.GREEN} 1080p Full HD Available {Style.RESET}")
    print(f"{Style.BOLD}======================================================================{Style.RESET}\n")

    confirm = input(f"{Style.BOLD}Proceed with download? [Y/n]: {Style.RESET}").strip().lower()
    if confirm not in ("", "y", "yes"):
        print(f"{Style.YELLOW}Download cancelled.{Style.RESET}")
        time.sleep(1)
        return

    progress = TerminalProgressBar()
    try:
        result = downloader.download_video(url, config, progress_hook=progress.hook)
        print(f"\n{Style.GREEN}{Style.BOLD}======================================================================{Style.RESET}")
        print(f"{Style.GREEN}{Style.BOLD}✓ SUCCESS! Video & Audio Download Complete & Verified{Style.RESET}")
        print(f"{Style.BOLD}======================================================================{Style.RESET}")
        print(f"  • {Style.BOLD}Saved File:{Style.RESET}     {result['file_path']}")
        print(f"  • {Style.BOLD}File Size:{Style.RESET}      {downloader.format_bytes(result['file_size'])} ({result['file_size']:,} bytes)")
        print(f"  • {Style.BOLD}Container:{Style.RESET}      {result['container']}")
        print(f"  • {Style.BOLD}Video Stream:{Style.RESET}   {result['video_codec'] or 'Verified'}")
        
        # Audio stream verification output
        if result.get("source_had_audio"):
            if result.get("has_audio"):
                print(f"  • {Style.BOLD}Audio Stream:{Style.RESET}   {Style.GREEN}✓ Verified ({result.get('audio_codec') or 'Active'}){Style.RESET}")
            else:
                print(f"  • {Style.BOLD}Audio Stream:{Style.RESET}   {Style.RED}✗ Missing (Stream check failed){Style.RESET}")
        else:
            print(f"  • {Style.BOLD}Audio Stream:{Style.RESET}   {Style.DIM}Source video has no audio track{Style.RESET}")

        print(f"  • {Style.BOLD}Time Elapsed:{Style.RESET}   {result['elapsed']:.1f} seconds")
        print(f"{Style.BOLD}======================================================================{Style.RESET}\n")

    except downloader.DownloadVerificationError as dve:
        print(f"\n{Style.RED}{Style.BOLD}[VERIFICATION ERROR]{Style.RESET} {dve}")
        print(f"{Style.YELLOW}The downloaded file failed integrity checks.{Style.RESET}")
    except Exception as e:
        print(f"\n{Style.RED}[ERROR] Download failed:{Style.RESET} {e}")

    input(f"\n{Style.DIM}Press Enter to return to main menu...{Style.RESET}")


def handle_choose_folder_action(config):
    """Option 2: Choose download folder."""
    current_dir = config.get("download_dir", config_mgr.DEFAULT_DOWNLOAD_DIR)
    print(f"\n{Style.BOLD}=== Choose Download Folder ==={Style.RESET}")
    print(f"Current download folder: {Style.CYAN}{current_dir}{Style.RESET}\n")

    new_dir = input(f"Enter new folder path (or press Enter to keep current): ").strip()
    if not new_dir:
        print(f"{Style.YELLOW}No change made.{Style.RESET}")
        time.sleep(1)
        return

    updated_dir = config_mgr.set_download_dir(new_dir)
    config["download_dir"] = updated_dir
    print(f"{Style.GREEN}✓ Download folder updated to: {updated_dir}{Style.RESET}")
    time.sleep(1.5)


def handle_check_dependencies_action(interactive=True):
    """Option 3: Check dependencies."""
    print(f"\n{Style.BOLD}=== Dependency Check ==={Style.RESET}\n")

    # 1. Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"1. Python Runtime:  {Style.GREEN}✓ Python {py_ver}{Style.RESET}")

    # 2. yt-dlp
    try:
        import yt_dlp
        yt_ver = getattr(yt_dlp, "__version__", None)
        if not yt_ver:
            try:
                import yt_dlp.version
                yt_ver = yt_dlp.version.__version__
            except Exception:
                yt_ver = "Installed"
        print(f"2. yt-dlp Library:  {Style.GREEN}✓ Version {yt_ver}{Style.RESET}")
    except ImportError:
        print(f"2. yt-dlp Library:  {Style.RED}✗ NOT INSTALLED. Run: pip install yt-dlp{Style.RESET}")

    # 3. FFmpeg & ffprobe
    dep = downloader.check_ffmpeg_installed()
    if dep["ffmpeg_available"]:
        print(f"3. FFmpeg Engine:   {Style.GREEN}✓ Available{Style.RESET}")
        print(f"   Binary Path:     {dep['ffmpeg_path']}")
        if dep["version"]:
            print(f"   Version Info:    {dep['version']}")
    else:
        print(f"3. FFmpeg Engine:   {Style.RED}✗ NOT FOUND ON PATH{Style.RESET}")

    if dep["ffprobe_available"]:
        print(f"4. ffprobe Tool:    {Style.GREEN}✓ Available{Style.RESET}")
        print(f"   Binary Path:     {dep['ffprobe_path']}")
    else:
        print(f"4. ffprobe Tool:    {Style.YELLOW}⚠ Missing (Audio stream verification will be limited){Style.RESET}")

    if not dep["ffmpeg_available"]:
        print(downloader.get_ffmpeg_install_instructions())
    else:
        print(f"\n{Style.GREEN}{Style.BOLD}✓ All core dependencies for highest-quality video + audio are ready!{Style.RESET}\n")

    if interactive:
        input(f"\n{Style.DIM}Press Enter to return to main menu...{Style.RESET}")


def interactive_menu():
    """Main terminal loop presenting the 4 required options."""
    enable_windows_ansi()

    while True:
        config = config_mgr.load_config()
        ffmpeg_info = downloader.check_ffmpeg_installed()
        show_banner(config, ffmpeg_info)

        print(f"{Style.BOLD}Menu Options:{Style.RESET}")
        print(f"  {Style.GREEN}[1]{Style.RESET} {Style.BOLD}Download video from URL{Style.RESET}")
        print(f"  {Style.CYAN}[2]{Style.RESET} Choose download folder")
        print(f"  {Style.YELLOW}[3]{Style.RESET} Check dependencies")
        print(f"  {Style.RED}[4]{Style.RESET} Exit")

        choice = input(f"\n{Style.BOLD}Select an option [1-4]: {Style.RESET}").strip()

        if choice == "1":
            handle_download_action(config)
        elif choice == "2":
            handle_choose_folder_action(config)
        elif choice == "3":
            handle_check_dependencies_action()
        elif choice in ("4", "exit", "quit", "q"):
            print(f"\n{Style.CYAN}Exiting Universal Video Downloader. Goodbye!{Style.RESET}\n")
            sys.exit(0)
        else:
            print(f"{Style.YELLOW}Invalid selection. Please choose 1, 2, 3, or 4.{Style.RESET}")
            time.sleep(1)


def main():
    """CLI entrypoint: supports command-line arguments or interactive menu."""
    enable_windows_ansi()
    config = config_mgr.load_config()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("--help", "-h"):
            print("Usage:")
            print("  python main.py                  (Launch interactive terminal menu)")
            print("  python main.py <URL>            (Direct highest-quality download)")
            print("  python main.py --check-deps     (Inspect system dependencies)")
            sys.exit(0)
        elif arg == "--check-deps":
            handle_check_dependencies_action(interactive=False)
            sys.exit(0)
        elif not arg.startswith("-"):
            # Direct URL passed via CLI
            url = arg
            progress = TerminalProgressBar()
            try:
                result = downloader.download_video(url, config, progress_hook=progress.hook)
                print(f"\n[SUCCESS] Downloaded to: {result['file_path']}")
                print(f"Audio stream verified: {result['has_audio']}")
                sys.exit(0)
            except Exception as e:
                print(f"\n[ERROR] Download failed: {e}", file=sys.stderr)
                sys.exit(1)

    try:
        interactive_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Style.CYAN}Session aborted by user. Goodbye!{Style.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
