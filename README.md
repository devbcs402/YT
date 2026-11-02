# StreamVault — Universal Personal Media Downloader & Transcoder

A high-performance personal video downloader and media processing application for Windows. StreamVault offers two workflows:

1. **Python Terminal Downloader (`main.py`)**: A fast, standalone CLI utility with automatic highest-quality video & audio selection (up to 4K UHD), lossless FFmpeg stream merging, `ffprobe` stream integrity verification (preventing missing sound), and safe collision-free file naming.
2. **Full-Stack Web Application (MERN Stack)**: A modern dark-themed web interface built with React 18, Vite, Tailwind CSS, Lucide icons, Node.js Express, and MongoDB.

---

## Table of Contents

- [1. System Prerequisites](#1-system-prerequisites)
- [2. Quick Start Guide](#2-quick-start-guide)
  - [Mode A: Python Terminal Downloader](#mode-a-python-terminal-downloader-recommended)
  - [Mode B: Full-Stack Web Application](#mode-b-full-stack-web-application)
- [3. Python Terminal Downloader (`main.py`)](#3-python-terminal-downloader-mainpy)
  - [Interactive Menu Options](#interactive-menu-options)
  - [Command-Line Flags](#command-line-flags)
  - [Configuration (`config.json`)](#configuration-configjson)
  - [Audio Fix & Merging Strategy](#audio-fix--merging-strategy)
- [4. Full-Stack Web Application (MERN)](#4-full-stack-web-application-mern)
  - [Architecture](#architecture)
  - [API Endpoints](#api-endpoints)
- [5. Testing & Verification](#5-testing--verification)
  - [Running Automated Test Suites](#running-automated-test-suites)
  - [How to Verify Audio in Downloaded Files](#how-to-verify-audio-in-downloaded-files)
- [6. Troubleshooting & Common Issues](#6-troubleshooting--common-issues)
- [7. Security & Compliance](#7-security--compliance)

---

## 1. System Prerequisites

Ensure you have the following installed on your Windows computer:

| Tool | Minimum Version | Installation Command (PowerShell) |
|---|---|---|
| **Python** | 3.10+ (Recommended: 3.12) | `winget install Python.Python.3.12` |
| **Node.js** | 18+ or 20+ | `winget install OpenJS.NodeJS.LTS` |
| **FFmpeg & ffprobe** | Full Build 7.0+ / 9.0+ | `winget install Gyan.FFmpeg` |
| **yt-dlp** | 2026.10+ | `python -m pip install yt-dlp` |

> [!IMPORTANT]
> **FFmpeg is required** to merge separate high-definition video (1080p, 2K, 4K) and audio tracks into a single playable file. If you install FFmpeg via `winget`, close and restart your PowerShell terminal so your system reloads the updated `PATH`.

---

## 2. Quick Start Guide

### Mode A: Python Terminal Downloader (Recommended)

The terminal downloader runs directly in your console with zero web dependencies.

```powershell
# 1. Open PowerShell and navigate to the project directory:
cd "d:\YASH KACHA\YT"

# 2. Install Python requirements:
python -m pip install -r requirements.txt

# 3. Check that dependencies (Python, yt-dlp, FFmpeg, ffprobe) are ready:
python main.py --check-deps

# 4. Launch the interactive menu:
python main.py

# (Alternatively, you can double-click "run_cli.bat" in Windows File Explorer)
```

---

### Mode B: Full-Stack Web Application

The MERN web app runs an Express backend server and a Vite React frontend in your browser.

#### One-Click Launcher:
Double-click [`start_web.bat`](file:///d:/YASH%20KACHA/YT/start_web.bat) or run in PowerShell:
```powershell
.\start_web.bat
```

#### Manual Startup (Two Terminals):

**Terminal 1 — Backend API Server:**
```powershell
cd "d:\YASH KACHA\YT\server"
npm install
npm start
# Server listens on: http://localhost:5000
```

**Terminal 2 — Frontend Development Client:**
```powershell
cd "d:\YASH KACHA\YT\client"
npm install
npm run dev
# Frontend runs on: http://localhost:5173
```

Open your web browser to: **[http://localhost:5173](http://localhost:5173)**

---

## 3. Python Terminal Downloader (`main.py`)

### Interactive Menu Options

When you run `python main.py`, the following interactive menu is displayed:

```
╔══════════════════════════════════════════════════════════════════╗
║         UNIVERSAL VIDEO DOWNLOADER - TERMINAL EDITION            ║
║              Automatic Highest-Quality Audio & Video             ║
╚══════════════════════════════════════════════════════════════════╝
  Download Folder:   D:\VideoDownloads
  FFmpeg Engine:     Available (ffmpeg version 9.0.2-full_build)
────────────────────────────────────────────────────────────────────
Menu Options:
  [1] Download video from URL
  [2] Choose download folder
  [3] Check dependencies
  [4] Exit
```

1. **Option 1: Download video from URL**
   - Prompts for a media URL.
   - Inspects the format ladder and displays genuine available resolutions (e.g. 2160p 4K, 1440p 2K, 1080p, 720p).
   - Automatically downloads the best video stream and best audio stream.
   - Displays real-time progress: percentage `[████████░░]`, download speed (e.g. `12.5 MiB/s`), ETA, and file size.
   - Merges streams using FFmpeg without lossy re-encoding.
   - Runs `ffprobe` stream verification to guarantee audio is present.
   - Displays full confirmation details (file path, size, codecs, elapsed time).
2. **Option 2: Choose download folder**
   - Displays current folder (default: `D:\VideoDownloads`).
   - Allows typing or pasting any custom local path.
   - Automatically creates the directory if missing and persists it to `config.json`.
3. **Option 3: Check dependencies**
   - Validates Python version, `yt-dlp` library version, `ffmpeg.exe` binary path, and `ffprobe.exe` binary path.
   - Displays clear instructions if any tool is missing.
4. **Option 4: Exit**
   - Cleanly closes the application.

---

### Command-Line Flags

You can bypass the interactive menu and run commands directly:

```powershell
# Direct highest-quality download:
python main.py "https://example.com/video.mp4"

# Dependency inspection:
python main.py --check-deps

# Help and usage:
python main.py --help
```

---

### Configuration (`config.json`)

User preferences are persisted in [`config.json`](file:///d:/YASH%20KACHA/YT/config.json) in the project root:

```json
{
  "download_dir": "D:\\VideoDownloads",
  "quality_mode": "best",
  "container_preference": "mp4",
  "auto_download": true
}
```

- `download_dir`: Destination directory where completed media files are saved.
- `quality_mode`: Default quality level (`best` selects the highest available resolution, up to 4K UHD).
- `container_preference`: Preferred output container (`mp4`). If codecs require MKV to preserve quality and audio sync, it safely falls back to MKV.
- `auto_download`: Automatically initiates highest-quality download after metadata inspection.

---

### Audio Fix & Merging Strategy

> [!NOTE]
> **Why downloaded videos previously had no sound:**
> 1. High-definition web videos (1080p+, 4K) are served as separate video-only and audio-only streams.
> 2. If FFmpeg was missing or failing, the video track was saved alone, creating a silent file.
> 3. Forcing `.mp4` on streams with Opus or VP9 codecs caused standard MP4 muxers to drop or corrupt audio.

**How StreamVault fixes this:**
- **Selector**: Uses `"format": "bestvideo*+bestaudio/best"`.
- **Safe Fallback**: If FFmpeg is missing, it falls back to combined progressive streams (`"best[acodec!=none]/best"`) so a video-only format is **never** downloaded when audio exists.
- **Dynamic Container**: Uses `"merge_output_format": "mp4/mkv"`. It uses MP4 when codecs are compatible (H.264 + AAC), and safely uses MKV when best quality requires Opus or VP9, avoiding any audio loss.
- **Automated Verification**: Uses `ffprobe` to verify that an audio stream exists in the final file before reporting success.

---

## 4. Full-Stack Web Application (MERN)

### Architecture

```
[ React 18 + Vite + Tailwind CSS ]  (Port 5173)
               │
               ▼ (Axios REST / Server-Sent Events SSE)
[ Node.js + Express API ]           (Port 5000)
    ├── Security Guard (SSRF protection & rate limiting)
    ├── MongoDB History Store (In-Memory Fallback if offline)
    └── Storage Manager & HTTP Streaming Pipeline
               │
               ▼ (stdio JSON pipeline)
[ Python 3.12 Media Worker ]
    ├── yt-dlp (Stream extraction & format ladder inspection)
    └── FFmpeg 9.0.2 (Muxing, VP9 WebM, 192k MP3 audio extraction)
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check, system uptime, and DB status |
| `POST` | `/api/video/analyze` | SSRF-safe URL validation & yt-dlp format inspection |
| `GET` | `/api/video/samples` | Pre-verified sample test video URLs |
| `POST` | `/api/downloads` | Initiates media processing / download task |
| `GET` | `/api/downloads/:id` | Polls task progress, speed, ETA, and status |
| `GET` | `/api/downloads/:id/progress` | Live Server-Sent Events (SSE) progress stream |
| `GET` | `/api/downloads/:id/stream` | Streams completed media to the browser |
| `DELETE` | `/api/downloads/:id` | Cancels active task and unlinks partial files |
| `GET` | `/api/downloads/history` | Retrieves recent download history |
| `DELETE` | `/api/downloads/history` | Clears all download records |

---

## 5. Testing & Verification

### Running Automated Test Suites

StreamVault includes comprehensive automated test suites for both Python and JavaScript:

#### 1. Python Downloader & Audio Verification Tests (10 Tests)
Runs 10 offline unit tests with mocked network calls covering FFmpeg detection, separate stream merging, combined formats, missing audio detection, merge errors, and stream verification:
```powershell
cd "d:\YASH KACHA\YT"
python -m unittest test_downloader.py -v
```
*(Expected result: `Ran 10 tests in 0.035s — OK`)*

#### 2. Backend Server Tests (12 Tests)
Tests SSRF filtering, URL validation, health endpoints, and download management:
```powershell
cd "d:\YASH KACHA\YT\server"
npm test
```
*(Expected result: `12 passed, 12 total`)*

#### 3. Frontend Client Tests (5 Tests)
Tests UI formatters and helper utilities:
```powershell
cd "d:\YASH KACHA\YT\client"
npm test
```
*(Expected result: `5 passed, 5 total`)*

---

### How to Verify Audio in Downloaded Files

#### Method 1: Automated Verification via `ffprobe` (Recommended)
Run `ffprobe` in PowerShell to inspect the streams of any downloaded file:
```powershell
ffprobe -v error -show_entries stream=index,codec_type,codec_name -of json "D:\VideoDownloads\your_video.mp4"
```

**Output for a video with verified audio:**
```json
{
    "streams": [
        {
            "index": 0,
            "codec_name": "h264",
            "codec_type": "video"
        },
        {
            "index": 1,
            "codec_name": "aac",
            "codec_type": "audio"
        }
    ]
}
```
If `"codec_type": "audio"` is present, the audio track is active and healthy.

#### Method 2: Media Player Verification
1. Open the downloaded file in **VLC Media Player**.
2. Press <kbd>Ctrl</kbd> + <kbd>J</kbd> (or go to **Tools** > **Codec Information**).
3. Confirm that both **Stream 0 (Video)** and **Stream 1 (Audio)** are listed.
4. Play the media to verify clear audio output.

---

## 6. Troubleshooting & Common Issues

### Issue 1: "FFmpeg is missing or not recognized"
- **Symptom**: `python main.py --check-deps` shows `FFmpeg Engine: NOT FOUND ON PATH`.
- **Solution**: Install FFmpeg via Windows WinGet:
  ```powershell
  winget install Gyan.FFmpeg
  ```
  Close and reopen PowerShell so the updated `PATH` takes effect.

### Issue 2: "Duplicate file names"
- **Behavior**: If `video.mp4` already exists in `D:\VideoDownloads`, StreamVault automatically saves the new file as `video (1).mp4`, `video (2).mp4`, etc., preventing accidental overwriting.

### Issue 3: "Failed - Unknown server error" in Web Browser
- **Symptom**: Browser shows download failure when saving from the web UI.
- **Solution**: Already resolved in `storageService.js` by sanitizing Unicode characters (such as fullwidth bars `｜`) and enforcing RFC 5987 / RFC 6266 compliant `Content-Disposition` headers.

### Issue 4: "MongoDB connection refused"
- **Behavior**: MongoDB is completely optional. If MongoDB is not running locally, the server automatically switches to its built-in in-memory fallback store without interrupting downloads.

---

## 7. Security & Compliance

- **Zero Shell Injection**: All subprocess calls use array argument tokens with `shell=False`.
- **SSRF Immunity**: Web backend pre-resolves DNS and blocks loopback, link-local, private LAN IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata services (`169.254.169.254`).
- **Filesystem Safety**: Filenames are sanitized for Windows to strip invalid characters (`<>:"/\|?*`), directory traversal sequences (`..`), and control characters.
- **Respect for Access Controls**: StreamVault does not bypass DRM (Widevine, FairPlay), paywalls, or unauthorized access controls. When a video is protected or restricted, it reports the exact reason clearly.

---

## 8. License

MIT License. Designed for personal local media backup, public-domain content, and authorized media processing.
