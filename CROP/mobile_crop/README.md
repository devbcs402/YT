# Mobile YouTube Shorts Automatic Video Splitter

A standalone, lightweight edition of the YouTube Shorts Video Splitter tailored specifically for mobile terminal environments like **iOS a-Shell** and **Android Termux**, as well as desktop systems.

---

## Why this Mobile Edition?

1. **Zero External Python Dependencies**: Built 100% on Python standard library (`pathlib`, `json`, `subprocess`, `dataclasses`, `shutil`). You don't need to install any pip packages.
2. **a-Shell & iOS Native Support**:
   - Seamlessly detects and works with `ffmpeg` and `ffprobe` built directly into a-Shell.
   - Handles iOS sandboxed document paths.
3. **One-Time Self-Test Script (`test_mobile.py`)**:
   - Generates a synthetic test video and verifies FFmpeg encoding, probing, vertical 9:16 blurred background crop, center crop, and audio sync right on your mobile phone in seconds.
4. **Mobile Battery & Speed Optimizations**:
   - Option to select **720×1280** or **1080×1920** for 2x faster encoding on mobile processors.
   - Stream copy option for instant splitting without re-encoding.

---

## Folder Structure

```text
mobile_crop/
├── install.py           # Automatic setup & dependency installer (like npm install)
├── setup.py             # Alias for install.py
├── install.sh           # 1-click installer for mobile a-Shell / Termux / Linux
├── install.bat          # 1-click installer for Windows
├── main.py              # Mobile interactive terminal menu & CLI runner
├── video_processor.py   # Mobile-optimized FFmpeg engine & validation
├── config.py            # Settings manager (auto-creates config.json)
├── config.json          # Persistent settings (remembers your last format choice)
├── test_mobile.py       # One-time self-diagnostic and verification test
├── requirements.txt     # Dependency definition file
├── README.md            # Mobile setup and usage guide
├── video/
│   └── video.mp4        # Place your input video file here
└── output/
    └── shorts/          # Generated 60-second YouTube Shorts clips
```

---

## Quick Start (Just like `npm install`)

When you first open or copy the project, run:

```bash
python install.py
```
*(or `python setup.py`)*

This single command automatically:
1. Detects your phone or computer environment.
2. Automatically downloads and installs any needed Python packages.
3. Auto-detects and configures hardware acceleration (`h264_videotoolbox` on iPhone, `libx264` on PC).
4. Creates necessary `video/` and `output/shorts/` folders.
5. Runs a 3-second self-test to verify that cutting and 9:16 vertical cropping work.
6. Gives you the green light to start!

---

## How to Run on iPhone / iPad (a-Shell)

### Step 1: Install a-Shell
Download **a-Shell** (free) from the App Store on your iPhone or iPad.

### Step 2: Copy this `mobile_crop` Folder into a-Shell
1. Open the iOS **Files** app.
2. Go to **On My iPhone** (or **On My iPad**) -> **a-Shell**.
3. Copy or move this `mobile_crop` folder inside.
4. Put your video file into `mobile_crop/video/video.mp4`.

### Step 3: Open a-Shell and Navigate
In the a-Shell app, run:

```bash
cd mobile_crop
```

### Step 4: Run the One-Time Test Code
Verify that FFmpeg and Python on your device are working:

```bash
python test_mobile.py
```

You should see:
```text
---> [TEST] 1. Checking FFmpeg & ffprobe availability...
  [PASS] FFmpeg and ffprobe are functioning correctly.
...
   >>> ALL 7/7 DIAGNOSTIC TESTS PASSED SUCCESSFULLY! <<<
```

### Step 5: Run the Splitter
```bash
python main.py
```

> **Important iOS Tip**: iOS suspends apps when the screen locks or when switching to another app. In a-Shell, type `keepScreenOn` in the terminal to keep the screen active while processing your video.

---

## How to Run on Android (Termux)

1. Open Termux and install Python and FFmpeg:
   ```bash
   pkg update
   pkg install python ffmpeg
   ```
2. Navigate to your folder and run the test:
   ```bash
   python test_mobile.py
   ```
3. Run the application:
   ```bash
   python main.py
   ```

---

## How to Run on Desktop (Windows, macOS, Linux)

It works identically on your computer:

```bash
cd mobile_crop
python test_mobile.py
python main.py
```

---

## Terminal Menu Options

```text
=================================================================
    YOUTUBE SHORTS VIDEO SPLITTER (MOBILE & DESKTOP)   
=================================================================
[Source Video]:    video/video.mp4 [Found (10:00, 1920x1080)]
[Output Folder]:   output/shorts/
[Format Mode]:     Mode B: Vertical Shorts 9:16 (Blurred BG, 1080x1920)
-----------------------------------------------------------------
  1. Split video into 60-second clips
  2. Select video format & resolution (9:16 Shorts / Original)
  3. Show source video information
  4. Open output folder
  5. Run self-test / diagnostics
  6. Exit
-----------------------------------------------------------------
Enter choice [1-6]:
```

### Formats Available:
- **Mode A (Original)**: Keeps original video resolution and aspect ratio.
- **Mode B (Vertical Shorts - Blurred Background) [Recommended]**: Centers full horizontal video on 9:16 vertical canvas with a blurred background filling the top and bottom. No content is cropped or lost!
- **Mode B (Vertical Shorts - Center Crop)**: Direct center crop filling the 9:16 vertical frame.

### Resolution Options:
- **1080×1920**: Full HD Shorts (crisp, standard YouTube Shorts resolution).
- **720×1280**: HD Shorts (encodes twice as fast, ideal for older phones or saving battery).

---

## Command Line Automation

You can also run tasks directly without the menu:

```bash
# Run one-time diagnostics
python main.py --test

# Show video metadata
python main.py --info

# Split automatically using saved settings
python main.py --split

# Override format mode
python main.py --split --format original
python main.py --split --format vertical_blur
python main.py --split --format vertical_crop
```

