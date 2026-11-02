"""
Main entry point for the YouTube Shorts Video Splitter.
Presents an interactive terminal menu with real-time progress, configuration management,
and automatic splitting into 60-second YouTube Shorts clips.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import AppConfig, load_config, save_config
from video_processor import (
    VideoInfo,
    VideoProcessor,
    check_ffmpeg_installed,
    format_duration,
    format_file_size,
    format_timestamp,
    get_available_source_candidates,
)

# ANSI terminal colors for clean, professional output
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def clear_screen() -> None:
    """Clear terminal screen gracefully."""
    # os.system("cls" if os.name == "nt" else "clear")
    # For a smoother experience in IDE terminals, just print empty line or do clean separator
    pass


def print_banner(config: AppConfig, video_info: Optional[VideoInfo] = None) -> None:
    """Display modern header banner with status."""
    mode_labels = {
        "original": "Mode A: Original Format (Preserve aspect ratio)",
        "vertical_blur": "Mode B: Vertical Shorts 9:16 (Blurred Background)",
        "vertical_crop": "Mode B: Vertical Shorts 9:16 (Center Crop)",
    }
    format_desc = mode_labels.get(config.video_format, config.video_format)

    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{CYAN}{BOLD}       YOUTUBE SHORTS AUTOMATIC VIDEO SPLITTER       {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")

    # Video status
    input_path = Path(config.input_video)
    if video_info:
        dur_str = format_timestamp(video_info.duration)
        status_str = f"{GREEN}Found{RESET} ({dur_str}, {video_info.resolution_str})"
    elif input_path.exists():
        status_str = f"{GREEN}Found{RESET}"
    else:
        status_str = f"{RED}Not Found (Expected at {input_path}){RESET}"

    print(f"{BOLD}[Source Video]:{RESET}    {input_path} [{status_str}]")
    print(f"{BOLD}[Output Folder]:{RESET}   {config.output_dir}/")
    print(f"{BOLD}[Format Mode]:{RESET}     {YELLOW}{format_desc}{RESET}")
    print(f"{CYAN}{'-' * 65}{RESET}")


def show_missing_video_error(expected_path: Path) -> Optional[Path]:
    """
    Display a helpful, unambiguous error message when the video file is missing.
    Also searches for candidate video files in common folders and offers to use them.
    """
    print(f"\n{RED}{BOLD}{'!' * 65}{RESET}")
    print(f"{RED}{BOLD} [ERROR] SOURCE VIDEO NOT FOUND!{RESET}")
    print(f"{RED}{BOLD}{'!' * 65}{RESET}")
    print(f" Expected video location: {BOLD}{expected_path.resolve()}{RESET}")
    print(" Please place your source video file at that exact location:")
    print(f"   --> {YELLOW}{expected_path}{RESET}")

    # Check for candidates
    candidates = get_available_source_candidates()
    if candidates:
        print(f"\n{CYAN}We found the following video file(s) in your project:{RESET}")
        for idx, cand in enumerate(candidates, 1):
            print(f"  [{idx}] {cand}")
        print("\nWould you like to use one of these files? Enter number or press Enter to skip:")
        choice = input(" > ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            selected = candidates[int(choice) - 1]
            print(f"{GREEN}Selected: {selected}{RESET}")
            return selected

    input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
    return None


def handle_split_video(config: AppConfig, processor: VideoProcessor, interactive: bool = True) -> None:
    """Option 1: Split video into 60-second clips."""
    input_path = Path(config.input_video)

    # 1. Check video existence
    if not input_path.exists():
        if interactive:
            alt_path = show_missing_video_error(input_path)
            if alt_path:
                input_path = alt_path
            else:
                return
        else:
            print(f"[ERROR] Source video not found at: {input_path}")
            return

    # 2. Probe video
    print(f"\n{CYAN}Analyzing source video...{RESET}")
    try:
        info = processor.probe_video(input_path)
    except Exception as exc:
        print(f"{RED}[ERROR] Failed to read video:{RESET} {exc}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
        return

    # 3. Calculate clips
    clips = processor.calculate_clips(info.duration, config.clip_duration)
    if not clips:
        print(f"{RED}[ERROR] Source video duration is too short or invalid ({info.duration}s).{RESET}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
        return

    total_clips = len(clips)
    print(f"\n{GREEN}{BOLD}Source Video Detected:{RESET}")
    print(f"  Duration:    {format_duration(info.duration)}")
    print(f"  Resolution:  {info.resolution_str} ({info.aspect_ratio})")
    print(f"  Audio:       {'Yes (' + (info.audio_codec or '') + ')' if info.has_audio else 'No audio stream'}")
    print(f"  Total Clips: {BOLD}{total_clips}{RESET} clip(s) of ~{config.clip_duration}s each\n")

    print(f"{CYAN}Clip Breakdown Plan:{RESET}")
    max_preview = 6
    for i, clip in enumerate(clips):
        if i < max_preview or i == total_clips - 1:
            note = f" (Final remainder: {clip.duration:.1f}s)" if clip.duration < config.clip_duration else ""
            print(f"  Part {clip.index:02d}: {clip.formatted_range}{note} -> {clip.filename}")
        elif i == max_preview:
            print(f"  ... [{total_clips - max_preview - 1} clips hidden for brevity] ...")

    # 4. Handle output folder conflict
    target_dir = Path(config.output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    existing_conflicts = [c for c in clips if (target_dir / c.filename).exists()]
    if existing_conflicts and interactive:
        print(f"\n{YELLOW}{BOLD}[WARNING] {len(existing_conflicts)} clip(s) already exist in '{target_dir}'.{RESET}")
        print("Please choose how to proceed:")
        print("  [1] Overwrite existing clips")
        print("  [2] Create a new folder (e.g., output/shorts_timestamp/)")
        print("  [3] Cancel and return to menu")
        choice = input(" Select option [1-3]: ").strip()

        if choice == "2":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_dir = Path(f"output/shorts_{ts}")
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"{GREEN}New output directory created: {target_dir}{RESET}")
        elif choice == "1":
            print(f"{YELLOW}Proceeding to overwrite existing files...{RESET}")
        else:
            print("Cancelled by user.")
            input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
            return

    # 5. Confirmation
    if interactive:
        print(f"\n{BOLD}Ready to split into {total_clips} clips using format: {YELLOW}{config.video_format}{RESET}.")
        confirm = input("Start processing? [Y/n]: ").strip().lower()
        if confirm not in ("", "y", "yes"):
            print("Aborted.")
            return

    # 6. Process clips with real-time feedback
    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{CYAN}{BOLD}Starting video split: {total_clips} clips total...{RESET}")
    print(f"{DIM}(Press Ctrl+C at any time to safely stop processing){RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}\n")

    start_time = time.time()
    successful_clips = 0
    failed_clips = 0

    try:
        for idx, clip in enumerate(clips, 1):
            out_file = target_dir / clip.filename
            prefix = f"[{idx:02d}/{total_clips:02d}] {clip.formatted_range} -> {clip.filename}"

            def update_status(status_text: str) -> None:
                sys.stdout.write(f"\r  {prefix} | Status: {YELLOW}{status_text:<15}{RESET}")
                sys.stdout.flush()

            update_status("Encoding...")
            ok, msg = processor.render_clip(
                input_path=input_path,
                clip=clip,
                output_path=out_file,
                format_mode=config.video_format,
                has_audio=info.has_audio,
                stream_copy_original=config.stream_copy_original,
                crf=config.crf,
                preset=config.preset,
                on_status=update_status,
            )

            if ok:
                successful_clips += 1
                sys.stdout.write(f"\r  {prefix} | Status: {GREEN}{BOLD}Done (Success){RESET}\n")
            else:
                failed_clips += 1
                sys.stdout.write(f"\r  {prefix} | Status: {RED}{BOLD}FAILED{RESET} ({msg})\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}{BOLD}[INTERRUPTED] Process was interrupted by user.{RESET}")
        print(f"Completed clips: {successful_clips}/{total_clips}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
        return

    elapsed = time.time() - start_time
    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{GREEN}{BOLD} Splitting Complete! {RESET}")
    print(f"  Clips Created:     {BOLD}{successful_clips}{RESET} of {total_clips}")
    if failed_clips > 0:
        print(f"  Clips Failed:      {RED}{BOLD}{failed_clips}{RESET}")
    print(f"  Total Time Taken:  {elapsed:.1f} seconds")
    print(f"  Saved in Folder:   {BOLD}{target_dir.resolve()}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}\n")

    if interactive:
        open_now = input("Open output folder in Windows Explorer now? [Y/n]: ").strip().lower()
        if open_now in ("", "y", "yes"):
            open_directory(target_dir)

        input(f"\n{DIM}Press Enter to return to main menu...{RESET}")


def handle_select_format(config: AppConfig) -> None:
    """Option 2: Select video format (original or vertical Shorts)."""
    while True:
        print(f"\n{CYAN}{BOLD}--- SELECT VIDEO FORMAT ---{RESET}")
        print("Choose the output format for your YouTube Shorts clips:\n")

        m1_mark = f"{GREEN}[CURRENT]{RESET}" if config.video_format == "original" else ""
        m2_mark = f"{GREEN}[CURRENT]{RESET}" if config.video_format == "vertical_blur" else ""
        m3_mark = f"{GREEN}[CURRENT]{RESET}" if config.video_format == "vertical_crop" else ""

        print(f"  [1] Mode A: Preserve original format {m1_mark}")
        print("      - Keeps original dimensions, aspect ratio and frame rate.")
        print("      - Splits without cropping.")
        print()
        print(f"  [2] Mode B: Vertical Shorts (9:16) - Blurred Background {m2_mark} {BOLD}[Recommended]{RESET}")
        print("      - 1080x1920 vertical canvas.")
        print("      - Full video fitted in center, blurred copy fills top/bottom background.")
        print("      - Never cuts off any part of the original video.")
        print()
        print(f"  [3] Mode B: Vertical Shorts (9:16) - Center Crop {m3_mark}")
        print("      - 1080x1920 vertical canvas.")
        print("      - Fills full screen by center-cropping the video.")
        print()
        print("  [4] Back to main menu")

        choice = input("\nSelect an option [1-4]: ").strip()
        if choice == "1":
            config.video_format = "original"
            save_config(config)
            print(f"\n{GREEN}Video format set to: Mode A (Preserve original format). Saved in config.json.{RESET}")
            break
        elif choice == "2":
            config.video_format = "vertical_blur"
            save_config(config)
            print(f"\n{GREEN}Video format set to: Mode B (Vertical Shorts - Blurred Background). Saved in config.json.{RESET}")
            break
        elif choice == "3":
            config.video_format = "vertical_crop"
            save_config(config)
            print(f"\n{GREEN}Video format set to: Mode B (Vertical Shorts - Center Crop). Saved in config.json.{RESET}")
            break
        elif choice == "4":
            break
        else:
            print(f"{RED}Invalid selection. Please enter 1, 2, 3, or 4.{RESET}")

    time.sleep(0.5)


def handle_show_info(config: AppConfig, processor: VideoProcessor, interactive: bool = True) -> None:
    """Option 3: Show detailed source video information."""
    input_path = Path(config.input_video)
    if not input_path.exists():
        if interactive:
            alt_path = show_missing_video_error(input_path)
            if alt_path:
                input_path = alt_path
            else:
                return
        else:
            print(f"[ERROR] Video file not found: {input_path}")
            return

    print(f"\n{CYAN}Inspecting video file: {input_path}...{RESET}\n")
    try:
        info = processor.probe_video(input_path)
    except Exception as exc:
        print(f"{RED}[ERROR] Failed to read video information:{RESET} {exc}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
        return

    clips = processor.calculate_clips(info.duration, config.clip_duration)
    total_clips = len(clips)

    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{CYAN}{BOLD}              SOURCE VIDEO INFORMATION              {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f" {BOLD}File Name:{RESET}         {info.filename}")
    print(f" {BOLD}Full Path:{RESET}         {info.path.resolve()}")
    print(f" {BOLD}File Size:{RESET}         {info.formatted_size}")
    print(f" {BOLD}Duration:{RESET}          {info.formatted_duration}")
    print(f" {BOLD}Resolution:{RESET}        {info.resolution_str} (Aspect Ratio: {info.aspect_ratio})")
    print(f" {BOLD}Frame Rate:{RESET}        {info.fps:.2f} fps")
    print(f" {BOLD}Video Codec:{RESET}       {info.video_codec}")
    if info.bitrate:
        print(f" {BOLD}Bitrate:{RESET}           {info.bitrate // 1000} kbps")
    if info.has_audio:
        print(f" {BOLD}Audio Codec:{RESET}       {info.audio_codec} ({info.audio_channels} channels, {info.audio_sample_rate} Hz)")
    else:
        print(f" {BOLD}Audio:{RESET}             {YELLOW}No audio track present{RESET}")
    print(f"{CYAN}{'-' * 60}{RESET}")
    print(f" {BOLD}YouTube Shorts Split Estimate:{RESET}")
    print(f"   Splits into:       {BOLD}{total_clips}{RESET} clips of {config.clip_duration}s each")
    if clips and clips[-1].duration < config.clip_duration:
        print(f"   Final Clip:        {clips[-1].formatted_range} ({clips[-1].duration:.1f}s remainder)")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}\n")

    if interactive:
        input(f"{DIM}Press Enter to return to main menu...{RESET}")


def open_directory(dir_path: Path) -> None:
    """Option 4: Open output folder in file explorer."""
    dir_path.mkdir(parents=True, exist_ok=True)
    resolved = str(dir_path.resolve())
    print(f"Opening folder: {resolved}")
    try:
        if os.name == "nt":
            os.startfile(resolved)
        else:
            subprocess.run(["xdg-open", resolved], check=False)
    except Exception as exc:
        print(f"{YELLOW}Could not open folder automatically: {exc}{RESET}")
        print(f"Folder location: {resolved}")


def main_menu() -> None:
    """Run interactive terminal menu."""
    # Ensure Windows console supports ANSI colors
    if os.name == "nt":
        os.system("")

    # Verify FFmpeg & ffprobe
    ffmpeg_ok, ffprobe_ok, guide_or_msg = check_ffmpeg_installed()
    if not (ffmpeg_ok and ffprobe_ok):
        print(f"{RED}{BOLD}{guide_or_msg}{RESET}")
        sys.exit(1)

    config = load_config()
    processor = VideoProcessor()

    while True:
        # Check source video status for header
        input_path = Path(config.input_video)
        cached_info = None
        if input_path.exists():
            try:
                cached_info = processor.probe_video(input_path)
            except Exception:
                pass

        print_banner(config, cached_info)
        print("  1. Split video into 60-second clips")
        print("  2. Select video format (original or vertical Shorts)")
        print("  3. Show source video information")
        print("  4. Open output folder")
        print("  5. Exit")
        print(f"{CYAN}{'-' * 65}{RESET}")

        choice = input("Enter your choice [1-5]: ").strip()

        if choice == "1":
            handle_split_video(config, processor)
        elif choice == "2":
            handle_select_format(config)
        elif choice == "3":
            handle_show_info(config, processor)
        elif choice == "4":
            open_directory(Path(config.output_dir))
            time.sleep(0.5)
        elif choice == "5" or choice.lower() in ("q", "exit", "quit"):
            print(f"\n{GREEN}Thank you for using YouTube Shorts Video Splitter. Goodbye!{RESET}\n")
            sys.exit(0)
        else:
            print(f"{RED}Invalid choice '{choice}'. Please enter a number from 1 to 5.{RESET}")
            time.sleep(1)


def parse_arguments() -> argparse.Namespace:
    """CLI argument parser for scripted/automated usage."""
    parser = argparse.ArgumentParser(
        description="Automatic YouTube Shorts Video Splitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Directly split video into 60s clips without interactive menu",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Print source video information and exit",
    )
    parser.add_argument(
        "--format",
        choices=["original", "vertical_blur", "vertical_crop"],
        help="Override video format mode",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Override input video path",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Override output directory",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    if args.split or args.info:
        # Non-interactive CLI mode
        ffmpeg_ok, ffprobe_ok, guide_or_msg = check_ffmpeg_installed()
        if not (ffmpeg_ok and ffprobe_ok):
            print(f"{RED}{BOLD}{guide_or_msg}{RESET}")
            sys.exit(1)

        cfg = load_config()
        if args.format:
            cfg.video_format = args.format
        if args.input:
            cfg.input_video = args.input
        if args.output:
            cfg.output_dir = args.output

        proc = VideoProcessor()
        if args.info:
            handle_show_info(cfg, proc, interactive=False)
        elif args.split:
            handle_split_video(cfg, proc, interactive=False)
    else:
        # Default: Interactive menu
        try:
            main_menu()
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Process exited by user.{RESET}\n")
            sys.exit(0)
