# YouTube Shorts Automatic Video Splitter

A senior-grade, reliable Python command-line application that automatically analyzes and splits long videos into high-quality, 60-second short clips optimized for YouTube Shorts, Instagram Reels, and TikTok.

---

## Key Features

- **Automated Source Video Detection**: Automatically detects and loads your source video from `video/video.mp4`. No need to enter the video path on every run.
- **Smart 60-Second Segmenting**: Automatically calculates clip boundaries, producing exact 60-second segments without overlapping or skipping frames.
- **Zero Content Loss**: If the remaining duration at the end is shorter than 60 seconds (e.g. 21.2 seconds), it is preserved as a final clip.
- **Format Flexibility (Dual Modes)**:
  - **Mode A (Original Format)**: Keeps original resolution, frame rate, and aspect ratio without cropping.
  - **Mode B (Vertical Shorts - 9:16, 1080×1920)**:
    - *Blurred Background (Recommended)*: Fits the full video centered in the frame with a dynamic blurred matching background filling the top and bottom. No content is cropped or lost!
    - *Center Crop*: Fills the full 1080×1920 canvas by cropping the center subject.
- **Audio & Video Stream Preservation**: Preserves original video clarity and audio synchronization. Gracefully supports videos without audio tracks.
- **Collision-Safe Output**: Saves numbered clips (`short_01.mp4`, `short_02.mp4`, etc.) to `output/shorts/`. Never overwrites existing clips without user confirmation.
- **Interactive Terminal UI**: Clean menu with real-time status updates (encoding, verification, success/failure).
- **Persistent Preferences**: Remembers your chosen format mode in `config.json`.
- **Command-Line & Automation Ready**: Supports CLI flags (`--split`, `--info`, `--format`) for automated batch workflows.

---

## Project Structure

```text
CROP/
├── install.py           # Automatic setup & dependency installer (like npm install)
├── setup.py             # Alias for install.py
├── install.bat          # 1-click Windows installer
├── install.sh           # 1-click Unix/mobile installer
├── main.py              # CLI entry point, interactive menu & progress reporting
├── video_processor.py   # FFmpeg engine, stream analysis, clipping & validation
├── config.py            # Configuration loader, validator & serializer
├── config.json          # Persistent user settings (format mode, CRF, resolution)
├── requirements.txt     # Python dependencies (colorama, pytest)
├── test_splitter.py     # Comprehensive unit and integration test suite
├── README.md            # Complete project documentation and guide
├── .gitignore           # Git ignore rules for virtualenvs, caches, and outputs
├── video/
│   └── video.mp4        # Source video file (automatically detected)
└── output/
    └── shorts/          # Generated 60-second YouTube Shorts clips
```

---

## ⚡ 1-Step Setup (Just like `npm install`)

When you first clone or download this project, simply run:

```bash
python install.py
```
*(or double-click `install.bat` on Windows)*

It will automatically check your Python environment, install all libraries from `requirements.txt`, verify FFmpeg, create the folders, and get everything ready.

---

## Prerequisites

- **Python 3.10+** (Tested with Python 3.12+)
- **FFmpeg & ffprobe** (Version 5.0+ or 9.0+)

---

## FFmpeg Installation on Windows

If FFmpeg is not already installed on your system, follow one of these easy methods:

### Option 1: Using Windows Package Manager (Winget - Recommended)

Open Windows PowerShell (Run as Administrator or regular user) and execute:

```powershell
winget install Gyan.FFmpeg
```

Restart your PowerShell window after installation completes.

### Option 2: Using Chocolatey

```powershell
choco install ffmpeg
```

### Option 3: Manual Installation

1. Download the latest release build (`ffmpeg-release-essentials.zip`) from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the archive to `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your System `PATH` environment variable:
   - Search for **Environment Variables** in the Windows Start menu.
   - Under **System Variables**, select **Path** and click **Edit**.
   - Click **New** and add `C:\ffmpeg\bin`.
   - Click **OK** to save.
4. Restart your PowerShell terminal.

### Verification

Verify that FFmpeg and ffprobe are recognized:

```powershell
ffmpeg -version
ffprobe -version
```

---

## Quick Start (Windows PowerShell)

Follow these exact commands to set up the virtual environment and run the application:

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# (If PowerShell blocks script execution, run this once:
#  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

# 3. Install dependencies
python -m pip install -r requirements.txt

# 4. Launch the application
python main.py
```

---

## Input Video Placement

Place your video file in the `video/` directory named `video.mp4`:

```text
video/video.mp4
```

> **Smart Detection**: If `video/video.mp4` is not found, the application will display a helpful error message and search for candidate video files in common project locations (such as `videos/` or other video formats), allowing you to select them with one keystroke.

---

## Terminal Menu Options

When you launch `python main.py`, you will see:

```text
=================================================================
       YOUTUBE SHORTS AUTOMATIC VIDEO SPLITTER       
=================================================================
[Source Video]:    video\video.mp4 [Found (25:21, 1920x1080)]
[Output Folder]:   output/shorts/
[Format Mode]:     Mode B: Vertical Shorts 9:16 (Blurred Background)
-----------------------------------------------------------------
  1. Split video into 60-second clips
  2. Select video format (original or vertical Shorts)
  3. Show source video information
  4. Open output folder
  5. Exit
-----------------------------------------------------------------
Enter your choice [1-5]:
```

### Option 1: Split video into 60-second clips
- Reads `video/video.mp4` automatically.
- Detects the exact duration and displays a clear breakdown plan (e.g., `Part 01: 00:00–01:00`, `Part 02: 01:00–02:00`, etc.).
- Verifies output conflicts before processing.
- Renders each clip with live encoding and verification status.
- Displays summary with the total number of clips created and offers to open the folder in Windows Explorer.

### Option 2: Select video format
Choose between:
1. **Mode A — Preserve original format**:
   - Keeps original dimensions and aspect ratio.
   - Splits without cropping.
2. **Mode B — Vertical Shorts (9:16) with Blurred Background [Recommended]**:
   - 1080×1920 canvas.
   - Centers full original video without cropping any content.
   - Creates a blurred matching background to fill top and bottom bars.
3. **Mode B — Vertical Shorts (9:16) with Center Crop**:
   - 1080×1920 canvas.
   - Crops the sides to fill the full vertical frame.

Your selection is saved immediately to `config.json` and remembered across sessions.

### Option 3: Show source video information
Displays a detailed breakdown of:
- Resolution, aspect ratio, frame rate (fps)
- Video codec, bitrate, and file size
- Audio presence, audio codec, channels, and sample rate
- Exact number of YouTube Shorts clips that will be generated

### Option 4: Open output folder
Opens `output/shorts/` directly in Windows File Explorer.

### Option 5: Exit
Exits the application cleanly.

---

## Output Naming & Collision Protection

Every generated clip is saved to:

```text
output/shorts/
├── short_01.mp4
├── short_02.mp4
├── short_03.mp4
...
```

If clips already exist in `output/shorts/`, the application will prompt you:
1. **Overwrite existing clips**
2. **Save to a new folder** (e.g. `output/shorts_20261029_1850/`)
3. **Cancel**

---

## Automated CLI Usage (Scripting)

The application also supports automated command-line execution without the interactive menu:

```powershell
# Show source video information
python main.py --info

# Split using default configuration
python main.py --split

# Override format mode from command line
python main.py --split --format original
python main.py --split --format vertical_blur
python main.py --split --format vertical_crop

# Specify custom input or output paths
python main.py --split --input "path/to/my_video.mp4" --output "output/my_shorts"
```

---

## Configuration (`config.json`)

The application settings can be configured via `config.json`:

```json
{
    "input_video": "video/video.mp4",
    "output_dir": "output/shorts",
    "clip_duration": 60,
    "video_format": "vertical_blur",
    "output_resolution": "1080x1920",
    "video_codec": "libx264",
    "audio_codec": "aac",
    "crf": 18,
    "preset": "fast",
    "stream_copy_original": false
}
```

- `clip_duration`: Default clip length in seconds (default: `60`).
- `crf`: Visual quality (lower is higher quality, `18` is visually lossless).
- `preset`: FFmpeg encoding speed (`ultrafast`, `veryfast`, `fast`, `medium`).
- `stream_copy_original`: Set to `true` if you wish to use ultra-fast stream copy for original format cuts when keyframes align.

---

## Testing

A comprehensive automated test suite is included in `test_splitter.py`:

```powershell
# Run with Python unittest
python -m unittest test_splitter.py

# Or run with pytest
pytest -v
```

### Covered Test Cases
- 10-minute video duration calculation (exact 10 clips, 00:00–10:00)
- 10-minute-30-second duration calculation (11 clips: 10 × 60s, 1 × 30s remainder)
- Sub-60-second video handling (1 single clip)
- Long video handling (25m+ video calculations)
- Audio and video stream verification with ffprobe
- Filenames and paths with spaces
- Vertical blurred background filter construction
- Vertical center crop filter construction
- Corrupted file rejection and graceful interruption handling

---

## Troubleshooting

### 1. `Execution_Policies` error in PowerShell
If you see `File ... cannot be loaded because running scripts is disabled on this system`, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then re-run `.\.venv\Scripts\Activate.ps1`.

### 2. FFmpeg not recognized
Verify that running `ffmpeg -version` works in your PowerShell terminal. If not, follow the [FFmpeg Installation Guide](#ffmpeg-installation-on-windows) above and ensure the terminal is restarted after modifying the PATH.

### 3. Video has no audio
The splitter detects audio presence automatically. If your input video has no audio track, output clips are encoded cleanly without failing or producing corrupt audio tracks.

