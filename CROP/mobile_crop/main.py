"""
Mobile YouTube Shorts Video Splitter.
Interactive terminal application designed for mobile environments (iOS a-Shell, Android Termux)
as well as standard desktop environments (Windows, macOS, Linux).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import MobileAppConfig, load_config, save_config
from video_processor import (
    MobileVideoProcessor,
    VideoInfo,
    check_ffmpeg_installed,
    find_candidate_videos,
    format_duration,
    format_timestamp,
)

# Clean ANSI styling
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner(config: MobileAppConfig, video_info: Optional[VideoInfo] = None) -> None:
    """Display terminal header banner."""
    mode_labels = {
        "original": "Mode A: Preserve Original Dimensions",
        "vertical_blur": f"Mode B: Vertical Shorts 9:16 (Blurred BG, {config.output_resolution})",
        "vertical_crop": f"Mode B: Vertical Shorts 9:16 (Center Crop, {config.output_resolution})",
    }
    format_desc = mode_labels.get(config.video_format, config.video_format)

    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{CYAN}{BOLD}    YOUTUBE SHORTS VIDEO SPLITTER (MOBILE & DESKTOP)   {RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}")

    input_path = Path(config.input_video)
    if video_info:
        dur_str = format_timestamp(video_info.duration)
        status_str = f"{GREEN}Found{RESET} ({dur_str}, {video_info.resolution_str})"
    elif input_path.exists():
        status_str = f"{GREEN}Found{RESET}"
    else:
        status_str = f"{RED}Not Found (Place in {input_path}){RESET}"

    print(f"{BOLD}[Source Video]:{RESET}    {input_path} [{status_str}]")
    print(f"{BOLD}[Output Folder]:{RESET}   {config.output_dir}/")
    print(f"{BOLD}[Format Mode]:{RESET}     {YELLOW}{format_desc}{RESET}")
    print(f"{CYAN}{'-' * 65}{RESET}")


def show_missing_video_dialog(expected_path: Path) -> Optional[Path]:
    """Display instructions when video is not found and search for nearby videos."""
    print(f"\n{RED}{BOLD}[!] SOURCE VIDEO NOT FOUND{RESET}")
    print(f"Expected file at: {BOLD}{expected_path.resolve()}{RESET}\n")
    print("How to place your video on mobile (iOS a-Shell):")
    print("  1. Open the iOS 'Files' app.")
    print("  2. Go to 'On My iPhone' -> 'a-Shell'.")
    print(f"  3. Copy your video into the '{expected_path.parent}' folder named '{expected_path.name}'.\n")

    candidates = find_candidate_videos()
    if candidates:
        print(f"{CYAN}Nearby video files found:{RESET}")
        for idx, cand in enumerate(candidates, 1):
            print(f"  [{idx}] {cand}")
        print("\nEnter number to use one of these videos, or press Enter to skip:")
        choice = input(" > ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            selected = candidates[int(choice) - 1]
            print(f"{GREEN}Using: {selected}{RESET}")
            return selected

    input(f"{DIM}Press Enter to return to menu...{RESET}")
    return None


def handle_split_video(
    config: MobileAppConfig, processor: MobileVideoProcessor, interactive: bool = True
) -> None:
    """Execute video split into 60-second clips."""
    input_path = Path(config.input_video)

    if not input_path.exists():
        if interactive:
            alt_path = show_missing_video_dialog(input_path)
            if alt_path:
                input_path = alt_path
            else:
                return
        else:
            print(f"[ERROR] Video not found: {input_path}")
            return

    print(f"\n{CYAN}Analyzing source video...{RESET}")
    try:
        info = processor.probe_video(input_path)
    except Exception as exc:
        print(f"{RED}[ERROR] Probing failed:{RESET} {exc}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to menu...{RESET}")
        return

    clips = processor.calculate_clips(info.duration, config.clip_duration)
    if not clips:
        print(f"{RED}[ERROR] Video duration is too short ({info.duration}s).{RESET}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to menu...{RESET}")
        return

    total_clips = len(clips)
    print(f"\n{GREEN}{BOLD}Video Details:{RESET}")
    print(f"  Duration:    {format_duration(info.duration)}")
    print(f"  Resolution:  {info.resolution_str} ({info.aspect_ratio})")
    print(f"  Audio:       {'Yes (' + (info.audio_codec or '') + ')' if info.has_audio else 'No audio track'}")
    print(f"  Clips:       {BOLD}{total_clips}{RESET} clip(s) of ~{config.clip_duration}s each\n")

    print(f"{CYAN}Clip Breakdown:{RESET}")
    preview_count = min(5, total_clips)
    for i in range(preview_count):
        c = clips[i]
        rem = f" (Remainder: {c.duration:.1f}s)" if c.duration < config.clip_duration else ""
        print(f"  Part {c.index:02d}: {c.formatted_range}{rem} -> {c.filename}")
    if total_clips > preview_count:
        final_c = clips[-1]
        rem = f" (Remainder: {final_c.duration:.1f}s)" if final_c.duration < config.clip_duration else ""
        print(f"  ... [{total_clips - preview_count - 1} intermediate clips] ...")
        print(f"  Part {final_c.index:02d}: {final_c.formatted_range}{rem} -> {final_c.filename}")

    # Output directory conflict check
    target_dir = Path(config.output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    conflicts = [c for c in clips if (target_dir / c.filename).exists()]

    if conflicts and interactive:
        print(f"\n{YELLOW}{BOLD}[WARNING] {len(conflicts)} clip(s) already exist in '{target_dir}'.{RESET}")
        print("  [1] Overwrite existing clips")
        print("  [2] Create a new folder (e.g. output/shorts_timestamp/)")
        print("  [3] Cancel")
        choice = input("Select option [1-3]: ").strip()
        if choice == "2":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_dir = Path(f"output/shorts_{ts}")
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"{GREEN}New output folder: {target_dir}{RESET}")
        elif choice == "1":
            print(f"{YELLOW}Overwriting existing files...{RESET}")
        else:
            print("Cancelled.")
            input(f"\n{DIM}Press Enter to return to menu...{RESET}")
            return

    if interactive:
        print(f"\n{BOLD}Ready to process {total_clips} clips using {YELLOW}{config.video_format}{RESET}.")
        print(f"{DIM}(Mobile tip: In a-Shell, run 'keepScreenOn' so iOS does not suspend processing){RESET}")
        confirm = input("Start processing? [Y/n]: ").strip().lower()
        if confirm not in ("", "y", "yes"):
            print("Aborted.")
            return

    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{CYAN}{BOLD}Encoding {total_clips} clips... (Press Ctrl+C to cancel){RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}\n")

    start_time = time.time()
    successful = 0
    failed = 0

    try:
        for idx, clip in enumerate(clips, 1):
            out_file = target_dir / clip.filename
            prefix = f"[{idx:02d}/{total_clips:02d}] {clip.formatted_range} -> {clip.filename}"

            def update_status(msg: str) -> None:
                sys.stdout.write(f"\r  {prefix} | Status: {YELLOW}{msg:<15}{RESET}")
                sys.stdout.flush()

            ok, msg = processor.render_clip(
                input_path=input_path,
                clip=clip,
                output_path=out_file,
                format_mode=config.video_format,
                has_audio=info.has_audio,
                resolution=config.output_resolution,
                stream_copy_original=config.stream_copy_original,
                crf=config.crf,
                preset=config.preset,
                on_status=update_status,
            )

            if ok:
                successful += 1
                sys.stdout.write(f"\r  {prefix} | Status: {GREEN}{BOLD}Done (Success){RESET}\n")
            else:
                failed += 1
                sys.stdout.write(f"\r  {prefix} | Status: {RED}{BOLD}FAILED{RESET} ({msg})\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}{BOLD}[INTERRUPTED] Processing stopped by user.{RESET}")
        print(f"Completed clips: {successful}/{total_clips}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to menu...{RESET}")
        return

    elapsed = time.time() - start_time
    print(f"\n{CYAN}{BOLD}{'=' * 65}{RESET}")
    print(f"{GREEN}{BOLD} Splitting Completed! {RESET}")
    print(f"  Clips Created:    {BOLD}{successful}{RESET} of {total_clips}")
    if failed > 0:
        print(f"  Clips Failed:     {RED}{BOLD}{failed}{RESET}")
    print(f"  Total Time:       {elapsed:.1f} seconds")
    print(f"  Destination:      {BOLD}{target_dir.resolve()}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 65}{RESET}\n")

    if interactive:
        open_now = input("Open output directory now? [Y/n]: ").strip().lower()
        if open_now in ("", "y", "yes"):
            open_output_folder(target_dir)
        input(f"\n{DIM}Press Enter to return to menu...{RESET}")


def handle_select_format(config: MobileAppConfig) -> None:
    """Format and resolution selection menu."""
    while True:
        print(f"\n{CYAN}{BOLD}--- SELECT VIDEO FORMAT & RESOLUTION ---{RESET}\n")
        m1_mark = f"{GREEN}[CURRENT]{RESET}" if config.video_format == "original" else ""
        m2_mark = f"{GREEN}[CURRENT]{RESET}" if config.video_format == "vertical_blur" else ""
        m3_mark = f"{GREEN}[CURRENT]{RESET}" if config.video_format == "vertical_crop" else ""

        print(f"  [1] Mode A: Preserve original format {m1_mark}")
        print("      - Keeps original dimensions & aspect ratio.")
        print()
        print(f"  [2] Mode B: Vertical Shorts (9:16) - Blurred Background {m2_mark} {BOLD}[Recommended]{RESET}")
        print("      - Full video centered; blurred background fills top/bottom.")
        print("      - Zero content lost or cropped.")
        print()
        print(f"  [3] Mode B: Vertical Shorts (9:16) - Center Crop {m3_mark}")
        print("      - 9:16 vertical canvas, fills screen by cropping sides.")
        print()
        print(f"  [4] Change Resolution (Current: {YELLOW}{config.output_resolution}{RESET})")
        print("      - Switch between 1080x1920 (Full HD) and 720x1280 (Faster on mobile/battery).")
        print()
        print("  [5] Back to main menu")

        choice = input("\nSelect option [1-5]: ").strip()
        if choice == "1":
            config.video_format = "original"
            save_config(config)
            print(f"{GREEN}Format set to: Mode A (Original). Saved in config.json.{RESET}")
            break
        elif choice == "2":
            config.video_format = "vertical_blur"
            save_config(config)
            print(f"{GREEN}Format set to: Mode B (Vertical Blurred Background). Saved.{RESET}")
            break
        elif choice == "3":
            config.video_format = "vertical_crop"
            save_config(config)
            print(f"{GREEN}Format set to: Mode B (Vertical Center Crop). Saved.{RESET}")
            break
        elif choice == "4":
            print("\nSelect Resolution:")
            print("  [1] 1080x1920 (Full HD Shorts - crispest quality)")
            print("  [2] 720x1280  (HD Shorts - 2x faster encoding on mobile)")
            r_choice = input("Choice [1-2]: ").strip()
            if r_choice == "2":
                config.output_resolution = "720x1280"
            else:
                config.output_resolution = "1080x1920"
            save_config(config)
            print(f"{GREEN}Output resolution set to {config.output_resolution}. Saved.{RESET}")
            time.sleep(0.5)
        elif choice == "5":
            break
        else:
            print(f"{RED}Invalid choice.{RESET}")


def handle_show_info(
    config: MobileAppConfig, processor: MobileVideoProcessor, interactive: bool = True
) -> None:
    """Show detailed metadata of source video."""
    input_path = Path(config.input_video)
    if not input_path.exists():
        if interactive:
            alt_path = show_missing_video_dialog(input_path)
            if alt_path:
                input_path = alt_path
            else:
                return
        else:
            print(f"[ERROR] Video file not found: {input_path}")
            return

    print(f"\n{CYAN}Inspecting: {input_path}...{RESET}\n")
    try:
        info = processor.probe_video(input_path)
    except Exception as exc:
        print(f"{RED}[ERROR] Probing failed:{RESET} {exc}")
        if interactive:
            input(f"\n{DIM}Press Enter to return to menu...{RESET}")
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
    print(f" {BOLD}Resolution:{RESET}        {info.resolution_str} ({info.aspect_ratio})")
    print(f" {BOLD}Frame Rate:{RESET}        {info.fps:.2f} fps")
    print(f" {BOLD}Video Codec:{RESET}       {info.video_codec}")
    if info.bitrate:
        print(f" {BOLD}Bitrate:{RESET}           {info.bitrate // 1000} kbps")
    if info.has_audio:
        print(f" {BOLD}Audio Codec:{RESET}       {info.audio_codec} ({info.audio_channels} ch, {info.audio_sample_rate} Hz)")
    else:
        print(f" {BOLD}Audio:{RESET}             {YELLOW}No audio track present{RESET}")
    print(f"{CYAN}{'-' * 60}{RESET}")
    print(f" {BOLD}YouTube Shorts Split Estimate:{RESET}")
    print(f"   Total Clips:       {BOLD}{total_clips}{RESET} clips of {config.clip_duration}s each")
    if clips and clips[-1].duration < config.clip_duration:
        print(f"   Final Remainder:   {clips[-1].formatted_range} ({clips[-1].duration:.1f}s)")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}\n")

    if interactive:
        input(f"{DIM}Press Enter to return to menu...{RESET}")


def open_output_folder(dir_path: Path) -> None:
    """Open folder in system file manager."""
    dir_path.mkdir(parents=True, exist_ok=True)
    resolved = str(dir_path.resolve())
    print(f"Output folder: {resolved}")
    try:
        if os.name == "nt":
            os.startfile(resolved)
        elif sys.platform == "darwin":
            # macOS or iOS
            subprocess.run(["open", resolved], check=False)
        else:
            subprocess.run(["xdg-open", resolved], check=False)
    except Exception as exc:
        print(f"{YELLOW}(Browse to '{resolved}' in your file manager){RESET}")


def main_menu() -> None:
    """Main interactive terminal loop."""
    if os.name == "nt":
        os.system("")

    ffmpeg_ok, ffprobe_ok, status_msg = check_ffmpeg_installed()
    if not (ffmpeg_ok and ffprobe_ok):
        print(f"{RED}{BOLD}{status_msg}{RESET}")
        sys.exit(1)

    config = load_config()
    processor = MobileVideoProcessor()

    while True:
        input_path = Path(config.input_video)
        cached_info = None
        if input_path.exists():
            try:
                cached_info = processor.probe_video(input_path)
            except Exception:
                pass

        print_banner(config, cached_info)
        print("  1. Split video into 60-second clips")
        print("  2. Select video format & resolution (9:16 Shorts / Original)")
        print("  3. Show source video information")
        print("  4. Open output folder")
        print("  5. Run self-test / diagnostics")
        print("  6. Exit")
        print(f"{CYAN}{'-' * 65}{RESET}")

        choice = input("Enter choice [1-6]: ").strip()

        if choice == "1":
            handle_split_video(config, processor)
        elif choice == "2":
            handle_select_format(config)
        elif choice == "3":
            handle_show_info(config, processor)
        elif choice == "4":
            open_output_folder(Path(config.output_dir))
            time.sleep(0.5)
        elif choice == "5":
            # Run one-time self test directly from menu
            from test_mobile import run_mobile_tests

            run_mobile_tests()
            input(f"\n{DIM}Press Enter to return to menu...{RESET}")
        elif choice in ("6", "q", "exit", "quit"):
            print(f"\n{GREEN}Thank you for using YouTube Shorts Splitter. Bye!{RESET}\n")
            sys.exit(0)
        else:
            print(f"{RED}Invalid option '{choice}'. Please enter 1-6.{RESET}")
            time.sleep(1)


def parse_arguments() -> argparse.Namespace:
    """CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Mobile YouTube Shorts Video Splitter",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split video directly without interactive menu",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Print source video info and exit",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-diagnostic test suite and exit",
    )
    parser.add_argument(
        "--format",
        choices=["original", "vertical_blur", "vertical_crop"],
        help="Override video format mode",
    )
    parser.add_argument(
        "--resolution",
        choices=["1080x1920", "720x1280"],
        help="Override output resolution",
    )
    parser.add_argument("--input", type=str, help="Override input video path")
    parser.add_argument("--output", type=str, help="Override output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    if args.test:
        from test_mobile import run_mobile_tests

        run_mobile_tests()
        sys.exit(0)

    if args.split or args.info:
        ffmpeg_ok, ffprobe_ok, status_msg = check_ffmpeg_installed()
        if not (ffmpeg_ok and ffprobe_ok):
            print(f"{RED}{BOLD}{status_msg}{RESET}")
            sys.exit(1)

        cfg = load_config()
        if args.format:
            cfg.video_format = args.format
        if args.resolution:
            cfg.output_resolution = args.resolution
        if args.input:
            cfg.input_video = args.input
        if args.output:
            cfg.output_dir = args.output

        proc = MobileVideoProcessor()
        if args.info:
            handle_show_info(cfg, proc, interactive=False)
        elif args.split:
            handle_split_video(cfg, proc, interactive=False)
    else:
        try:
            main_menu()
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Process exited.{RESET}\n")
            sys.exit(0)

