"""
Core Downloader & Verification Engine
Universal Video Downloader
Handles yt-dlp format selection, FFmpeg merging, stream verification via ffprobe,
and safe unique filename handling.
"""

import os
import sys
import re
import json
import shutil
import subprocess
import time
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class DownloadVerificationError(Exception):
    """Raised when downloaded file fails verification (e.g. missing audio stream)."""
    pass


class DependencyMissingError(Exception):
    """Raised when a required external dependency like FFmpeg is missing."""
    pass


def check_ffmpeg_installed(custom_path=None):
    """
    Check whether FFmpeg and ffprobe are available.
    Checks system PATH first, then optional custom_path, and known Windows locations.
    Returns a dict with availability, binary paths, and version information.
    """
    ffmpeg_cmd = shutil.which("ffmpeg")
    ffprobe_cmd = shutil.which("ffprobe")
    ffmpeg_dir = None

    # Check custom_path if provided
    if custom_path and os.path.isdir(custom_path):
        candidate_ffmpeg = os.path.join(custom_path, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        candidate_ffprobe = os.path.join(custom_path, "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.isfile(candidate_ffmpeg):
            ffmpeg_cmd = candidate_ffmpeg
            ffmpeg_dir = custom_path
        if os.path.isfile(candidate_ffprobe):
            ffprobe_cmd = candidate_ffprobe

    # If not found in PATH, check known Windows WinGet & local paths
    if not ffmpeg_cmd and os.name == "nt":
        search_dirs = [
            r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin",
            r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-N-127043-g5a54fcf75e-win64-gpl\bin",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "bin"),
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "ffmpeg", "bin"),
        ]
        for d in search_dirs:
            candidate_ffmpeg = os.path.join(d, "ffmpeg.exe")
            candidate_ffprobe = os.path.join(d, "ffprobe.exe")
            if os.path.isfile(candidate_ffmpeg):
                ffmpeg_cmd = candidate_ffmpeg
                ffmpeg_dir = d
                if os.path.isfile(candidate_ffprobe):
                    ffprobe_cmd = candidate_ffprobe
                break

    if ffmpeg_cmd and not ffmpeg_dir:
        ffmpeg_dir = os.path.dirname(os.path.abspath(ffmpeg_cmd))

    version_str = None
    if ffmpeg_cmd:
        try:
            res = subprocess.run(
                [ffmpeg_cmd, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                shell=False
            )
            if res.returncode == 0:
                first_line = res.stdout.splitlines()[0] if res.stdout else ""
                version_str = first_line.strip()
        except Exception:
            pass

    return {
        "ffmpeg_available": bool(ffmpeg_cmd),
        "ffprobe_available": bool(ffprobe_cmd),
        "ffmpeg_path": ffmpeg_cmd,
        "ffprobe_path": ffprobe_cmd,
        "ffmpeg_dir": ffmpeg_dir,
        "version": version_str
    }


def get_ffmpeg_install_instructions():
    """Return human-readable instructions for installing FFmpeg on Windows."""
    return (
        "\n"
        "======================================================================\n"
        "                     FFMPEG INSTALLATION REQUIRED                     \n"
        "======================================================================\n"
        "FFmpeg is required to merge high-definition video and audio streams.\n"
        "Without FFmpeg, downloaded 1080p, 2K, or 4K videos may have NO sound.\n\n"
        "How to install FFmpeg on Windows:\n"
        "1. Open Windows PowerShell as Administrator and run:\n"
        "     winget install Gyan.FFmpeg\n\n"
        "2. Alternatively, download FFmpeg from:\n"
        "     https://www.gyan.dev/ffmpeg/builds/\n"
        "   Extract the zip and add its 'bin' directory to your Windows PATH.\n\n"
        "3. Restart your PowerShell or Command Prompt after installing.\n"
        "======================================================================\n"
    )


def sanitize_filename(filename, fallback="video_download"):
    """
    Produce a safe Windows filesystem filename from any Unicode string.
    Removes invalid characters: < > : " / \\ | ? * and control characters.
    """
    if not filename:
        return fallback

    # Remove illegal characters for Windows
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', str(filename))
    # Collapse multiple whitespace characters into a single space
    clean = re.sub(r'\s+', ' ', clean).strip('. ')

    if not clean:
        clean = fallback

    # Limit filename length to 150 characters to prevent path length errors
    if len(clean) > 150:
        clean = clean[:150].strip('. ')

    return clean


def get_unique_base_name(target_dir, base_title, preferred_ext="mp4"):
    """
    Determine a unique base name in target_dir so that base.ext or base (n).ext
    never overwrites an existing file.
    """
    candidate_base = base_title
    extensions_to_check = [preferred_ext, "mp4", "mkv", "webm"]

    def file_exists_with_base(name):
        for ext in extensions_to_check:
            if os.path.exists(os.path.join(target_dir, f"{name}.{ext}")):
                return True
        return False

    if not file_exists_with_base(candidate_base):
        return candidate_base

    i = 1
    while True:
        candidate_base = f"{base_title} ({i})"
        if not file_exists_with_base(candidate_base):
            return candidate_base
        i += 1


def format_bytes(bytes_num):
    """Format bytes to human-readable string (KiB, MiB, GiB)."""
    if bytes_num is None or bytes_num == 0:
        return "N/A"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    val = float(bytes_num)
    unit_idx = 0
    while val >= 1024.0 and unit_idx < len(units) - 1:
        val /= 1024.0
        unit_idx += 1
    return f"{val:.2f} {units[unit_idx]}"


def source_has_audio(info):
    """
    Determine whether the source media provides an audio stream.
    Inspects available formats in the yt-dlp metadata info dictionary.
    """
    if not info:
        return False

    # Check top-level acodec
    top_acodec = info.get("acodec")
    if top_acodec and top_acodec != "none":
        return True

    formats = info.get("formats", [])
    if not formats:
        # If no formats list, check direct stream characteristics
        return top_acodec != "none" if top_acodec else True

    for f in formats:
        acodec = f.get("acodec")
        vcodec = f.get("vcodec")
        # An audio format has acodec != 'none' or is audio-only (vcodec == 'none' and acodec != 'none')
        if acodec and acodec != "none":
            return True

    return False


def verify_file_streams(file_path, ffprobe_path=None):
    """
    Use ffprobe to verify whether the final downloaded file contains
    a video stream and an audio stream.
    Returns a dictionary of stream verification details.
    """
    if not os.path.isfile(file_path):
        return {
            "exists": False,
            "file_size": 0,
            "has_video": False,
            "has_audio": False,
            "video_codec": None,
            "audio_codec": None,
            "streams": [],
            "verified": False,
            "error": f"File does not exist: {file_path}"
        }

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return {
            "exists": True,
            "file_size": 0,
            "has_video": False,
            "has_audio": False,
            "video_codec": None,
            "audio_codec": None,
            "streams": [],
            "verified": False,
            "error": "File is empty (0 bytes)"
        }

    # Locate ffprobe
    probe_bin = ffprobe_path or shutil.which("ffprobe")
    if not probe_bin:
        # Check standard winget paths on Windows
        dep_info = check_ffmpeg_installed()
        probe_bin = dep_info.get("ffprobe_path")

    if not probe_bin:
        # ffprobe is not available, we can only verify basic file existence & non-zero size
        return {
            "exists": True,
            "file_size": file_size,
            "has_video": True,
            "has_audio": None,  # Unable to verify without ffprobe
            "video_codec": None,
            "audio_codec": None,
            "streams": [],
            "verified": False,
            "error": "ffprobe is not available to verify stream contents."
        }

    try:
        cmd = [
            probe_bin,
            "-v", "error",
            "-show_entries", "stream=index,codec_type,codec_name",
            "-of", "json",
            file_path
        ]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            shell=False
        )

        if proc.returncode != 0:
            return {
                "exists": True,
                "file_size": file_size,
                "has_video": False,
                "has_audio": False,
                "video_codec": None,
                "audio_codec": None,
                "streams": [],
                "verified": False,
                "error": f"ffprobe analysis failed: {proc.stderr.strip()}"
            }

        data = json.loads(proc.stdout)
        streams = data.get("streams", [])

        has_video = False
        has_audio = False
        video_codec = None
        audio_codec = None

        for s in streams:
            ctype = s.get("codec_type")
            cname = s.get("codec_name")
            if ctype == "video" and not has_video:
                has_video = True
                video_codec = cname
            elif ctype == "audio" and not has_audio:
                has_audio = True
                audio_codec = cname

        return {
            "exists": True,
            "file_size": file_size,
            "has_video": has_video,
            "has_audio": has_audio,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "streams": streams,
            "verified": True,
            "error": None
        }

    except Exception as e:
        return {
            "exists": True,
            "file_size": file_size,
            "has_video": False,
            "has_audio": False,
            "video_codec": None,
            "audio_codec": None,
            "streams": [],
            "verified": False,
            "error": f"Exception during stream verification: {e}"
        }


def build_yt_dlp_options(config, output_template, ffmpeg_info, has_audio, progress_hook=None):
    """
    Construct yt-dlp options dictionary to ensure:
    - Both best video and best audio are downloaded.
    - Separate streams are merged using FFmpeg.
    - Fallback to pre-merged formats if separate streams cannot be merged.
    - Container compatibility without stripping audio.
    """
    container_pref = config.get("container_preference", "mp4").lower()
    ffmpeg_available = ffmpeg_info.get("ffmpeg_available", False)
    ffmpeg_dir = ffmpeg_info.get("ffmpeg_dir")

    # Format selection strategy:
    # If the source provides audio:
    #   When FFmpeg is available: 'bestvideo*+bestaudio/best'
    #   When FFmpeg is missing: fallback to formats that already contain audio 'best[acodec!=none]/best'
    #   so the user NEVER receives a video-only format when audio is available!
    if has_audio:
        if ffmpeg_available:
            format_str = "bestvideo*+bestaudio/best"
        else:
            format_str = "best[acodec!=none]/best"
    else:
        format_str = "bestvideo/best"

    # Merge container:
    # 'mp4/mkv' prefers MP4, but if audio codec (e.g. Opus) or video codec (e.g. VP9)
    # is incompatible with MP4, yt-dlp automatically uses MKV, preventing quality loss
    # and ensuring audio is not stripped or rejected!
    if container_pref == "mp4":
        merge_format = "mp4/mkv"
    else:
        merge_format = container_pref

    ydl_opts = {
        "format": format_str,
        "outtmpl": output_template,
        "merge_output_format": merge_format,
        "quiet": True,
        "no_warnings": True,
        "overwrites": False,
        "socket_timeout": 30,
    }

    # Use native Windows curl when available to bypass Python's OpenSSL
    # [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] bug on large files
    curl_bin = shutil.which("curl")
    if curl_bin:
        ydl_opts["external_downloader"] = "curl"
        ydl_opts["external_downloader_args"] = {
            "curl": ["--retry", "10", "--retry-delay", "1", "--retry-connrefused"]
        }
    else:
        # Fallback Python HTTP downloader resilience settings
        ydl_opts["http_chunk_size"] = 10485760  # 10 MiB chunks
        ydl_opts["retries"] = 50
        ydl_opts["fragment_retries"] = 50
        ydl_opts["buffersize"] = 1048576
        ydl_opts["retry_sleep_functions"] = {"http": lambda n: 1}

    if ffmpeg_dir:
        ydl_opts["ffmpeg_location"] = ffmpeg_dir

    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    return ydl_opts


def inspect_video(url, ffmpeg_info=None):
    """
    Extract video metadata and inspect genuine available resolutions and audio tracks.
    Returns info dict or raises an exception.
    """
    if yt_dlp is None:
        raise ImportError("yt-dlp is not installed. Please run: pip install yt-dlp")

    dep_info = ffmpeg_info or check_ffmpeg_installed()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if dep_info.get("ffmpeg_dir"):
        ydl_opts["ffmpeg_location"] = dep_info["ffmpeg_dir"]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def download_video(url, config, progress_hook=None):
    """
    Download a video in the highest available quality with verified audio.
    Full workflow:
    1. Checks FFmpeg availability.
    2. Extracts metadata and checks if the source media contains audio.
    3. Handles missing FFmpeg cleanly without creating silent videos.
    4. Downloads best video and best audio and merges them with FFmpeg.
    5. Verifies the downloaded file exists and is not empty.
    6. Uses ffprobe to verify that the video contains an audio stream.
    7. Raises DownloadVerificationError if audio is missing when source had audio.
    """
    if yt_dlp is None:
        raise ImportError("yt-dlp is not installed. Please run: pip install yt-dlp")

    download_dir = config.get("download_dir", r"D:\VideoDownloads")
    os.makedirs(download_dir, exist_ok=True)

    # Step 1: Check FFmpeg availability
    ffmpeg_info = check_ffmpeg_installed()

    # Step 2: Extract metadata and inspect streams
    try:
        info = inspect_video(url, ffmpeg_info)
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve video information: {e}")

    if not info:
        raise RuntimeError("No video metadata returned by extractor.")

    has_source_audio = source_has_audio(info)
    raw_title = info.get("title") or "video_download"
    safe_title = sanitize_filename(raw_title)
    unique_base = get_unique_base_name(
        download_dir,
        safe_title,
        preferred_ext=config.get("container_preference", "mp4")
    )

    # Check if FFmpeg is required:
    # If source provides separate video & audio streams and has audio, FFmpeg is needed to merge them.
    formats = info.get("formats", [])
    has_separate_streams = any(
        f.get("vcodec") != "none" and f.get("acodec") == "none" for f in formats
    )
    if has_source_audio and has_separate_streams and not ffmpeg_info["ffmpeg_available"]:
        print(get_ffmpeg_install_instructions())
        print(
            "[WARNING] FFmpeg is missing! The downloader will attempt to use a combined "
            "progressive format with audio, but resolutions may be limited to 720p/360p."
        )

    # Step 3: Build yt-dlp options
    output_template = os.path.join(download_dir, f"{unique_base}.%(ext)s")
    ydl_opts = build_yt_dlp_options(
        config=config,
        output_template=output_template,
        ffmpeg_info=ffmpeg_info,
        has_audio=has_source_audio,
        progress_hook=progress_hook
    )

    # Step 4: Execute download
    start_time = time.time()
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            exit_code = ydl.download([url])
            if exit_code != 0:
                raise RuntimeError(f"yt-dlp download failed with exit code {exit_code}")
    except yt_dlp.utils.DownloadError as de:
        raise RuntimeError(f"Download rejected by media source or network: {de}")
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")

    elapsed = time.time() - start_time

    # Step 5: Locate the completed media file on disk
    matched_files = []
    try:
        for f in os.listdir(download_dir):
            if f.startswith(unique_base):
                full_path = os.path.join(download_dir, f)
                if (
                    os.path.isfile(full_path)
                    and not f.endswith(".part")
                    and not f.endswith(".ytdl")
                ):
                    matched_files.append(full_path)
    except Exception as e:
        raise RuntimeError(f"Failed to scan download directory '{download_dir}': {e}")

    if not matched_files:
        raise FileNotFoundError(f"Target media file not found in '{download_dir}'.")

    # Pick the largest file (the completed merged media file)
    final_file = max(matched_files, key=os.path.getsize)
    file_size = os.path.getsize(final_file)

    if file_size == 0:
        raise DownloadVerificationError("Downloaded media file is empty (0 bytes).")

    # Step 6: Verify streams using ffprobe
    stream_check = verify_file_streams(final_file, ffmpeg_info.get("ffprobe_path"))

    # If the source provided audio, verify that the final file actually contains an audio stream!
    if has_source_audio:
        if stream_check["verified"] and not stream_check["has_audio"]:
            raise DownloadVerificationError(
                f"Missing Audio Stream Error: The downloaded file '{os.path.basename(final_file)}' "
                f"contains a video stream ({stream_check.get('video_codec') or 'unknown'}) "
                "but has NO audio stream, even though the source provided audio.\n"
                "Root cause: FFmpeg was unable to merge the audio stream or the container rejected the codec."
            )

    return {
        "success": True,
        "file_path": final_file,
        "file_name": os.path.basename(final_file),
        "file_size": file_size,
        "title": raw_title,
        "has_video": stream_check.get("has_video", True),
        "has_audio": stream_check.get("has_audio"),
        "video_codec": stream_check.get("video_codec"),
        "audio_codec": stream_check.get("audio_codec"),
        "container": Path(final_file).suffix.lstrip(".").upper(),
        "elapsed": elapsed,
        "verified": stream_check.get("verified", False),
        "source_had_audio": has_source_audio
    }
