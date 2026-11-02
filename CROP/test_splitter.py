"""
Comprehensive unit and integration test suite for YouTube Shorts Video Splitter.
Tests clip duration calculations, config management, video probing,
stream verification, and FFmpeg command generation.
"""

from __future__ import annotations

import json
import math
import shutil
import unittest
from pathlib import Path

from config import AppConfig, load_config, save_config
from video_processor import (
    ClipSegment,
    VideoProcessor,
    format_duration,
    format_file_size,
    format_timestamp,
)


class TestClipCalculations(unittest.TestCase):
    """Test clip segment calculation logic under various durations."""

    def setUp(self) -> None:
        self.processor = VideoProcessor()

    def test_ten_minute_video(self) -> None:
        """A 10-minute video (600s) should yield exactly 10 clips of 60s each."""
        duration = 600.0
        clips = self.processor.calculate_clips(duration, 60.0)

        self.assertEqual(len(clips), 10)

        expected_ranges = [
            ("00:00", "01:00"),
            ("01:00", "02:00"),
            ("02:00", "03:00"),
            ("03:00", "04:00"),
            ("04:00", "05:00"),
            ("05:00", "06:00"),
            ("06:00", "07:00"),
            ("07:00", "08:00"),
            ("08:00", "09:00"),
            ("09:00", "10:00"),
        ]

        for i, clip in enumerate(clips):
            self.assertEqual(clip.index, i + 1)
            self.assertEqual(clip.duration, 60.0)
            self.assertEqual(clip.formatted_start, expected_ranges[i][0])
            self.assertEqual(clip.formatted_end, expected_ranges[i][1])
            self.assertEqual(clip.filename, f"short_{i + 1:02d}.mp4")

        # Verify no gaps and no overlaps
        for i in range(1, len(clips)):
            self.assertAlmostEqual(clips[i].start_time, clips[i - 1].end_time, places=2)

    def test_ten_minute_thirty_second_video(self) -> None:
        """A 10m 30s video (630s) should yield 11 clips: 10 x 60s and 1 x 30s."""
        duration = 630.0
        clips = self.processor.calculate_clips(duration, 60.0)

        self.assertEqual(len(clips), 11)

        # First 10 clips are 60s
        for i in range(10):
            self.assertEqual(clips[i].duration, 60.0)

        # Final clip should be 30s
        final_clip = clips[-1]
        self.assertEqual(final_clip.index, 11)
        self.assertEqual(final_clip.start_time, 600.0)
        self.assertEqual(final_clip.duration, 30.0)
        self.assertEqual(final_clip.end_time, 630.0)
        self.assertEqual(final_clip.formatted_start, "10:00")
        self.assertEqual(final_clip.formatted_end, "10:30")
        self.assertEqual(final_clip.filename, "short_11.mp4")

    def test_short_video_less_than_sixty_seconds(self) -> None:
        """A video of 45 seconds should yield exactly 1 clip of 45 seconds."""
        duration = 45.0
        clips = self.processor.calculate_clips(duration, 60.0)

        self.assertEqual(len(clips), 1)
        clip = clips[0]
        self.assertEqual(clip.index, 1)
        self.assertEqual(clip.start_time, 0.0)
        self.assertEqual(clip.duration, 45.0)
        self.assertEqual(clip.end_time, 45.0)
        self.assertEqual(clip.formatted_start, "00:00")
        self.assertEqual(clip.formatted_end, "00:45")
        self.assertEqual(clip.filename, "short_01.mp4")

    def test_exact_sixty_seconds_video(self) -> None:
        """A video of exactly 60.0s should yield 1 clip of 60.0s."""
        duration = 60.0
        clips = self.processor.calculate_clips(duration, 60.0)

        self.assertEqual(len(clips), 1)
        self.assertEqual(clips[0].duration, 60.0)
        self.assertEqual(clips[0].formatted_range, "00:00 - 01:00")

    def test_long_video_twenty_five_minutes(self) -> None:
        """A 25m 21.22s video (1521.22s) should yield 26 clips without loss."""
        duration = 1521.22
        clips = self.processor.calculate_clips(duration, 60.0)

        expected_count = math.ceil(duration / 60.0)
        self.assertEqual(len(clips), expected_count)
        self.assertEqual(len(clips), 26)

        # Check total summed duration
        total_covered = sum(c.duration for c in clips)
        self.assertAlmostEqual(total_covered, duration, places=2)

        # Check final clip
        self.assertAlmostEqual(clips[-1].duration, 21.22, places=2)
        self.assertEqual(clips[-1].filename, "short_26.mp4")

    def test_zero_or_negative_duration(self) -> None:
        """Zero or negative duration should return an empty list."""
        self.assertEqual(self.processor.calculate_clips(0.0), [])
        self.assertEqual(self.processor.calculate_clips(-10.0), [])


class TestFormattingHelpers(unittest.TestCase):
    """Test timestamp, duration, and file size formatting."""

    def test_format_timestamp(self) -> None:
        self.assertEqual(format_timestamp(0), "00:00")
        self.assertEqual(format_timestamp(59), "00:59")
        self.assertEqual(format_timestamp(60), "01:00")
        self.assertEqual(format_timestamp(125), "02:05")
        self.assertEqual(format_timestamp(3600), "01:00:00")
        self.assertEqual(format_timestamp(3665), "01:01:05")

    def test_format_file_size(self) -> None:
        self.assertEqual(format_file_size(500 * 1024), "500.0 KB")
        self.assertEqual(format_file_size(50 * 1024 * 1024), "50.00 MB")
        self.assertEqual(format_file_size(2 * 1024 * 1024 * 1024), "2.00 GB")

    def test_format_duration(self) -> None:
        self.assertIn("10m 0s", format_duration(600))
        self.assertIn("1h 1m 5s", format_duration(3665))


class TestConfiguration(unittest.TestCase):
    """Test config load, save, and fallback logic."""

    def setUp(self) -> None:
        self.test_cfg_path = Path("test_config.json")
        if self.test_cfg_path.exists():
            self.test_cfg_path.unlink()

    def tearDown(self) -> None:
        if self.test_cfg_path.exists():
            self.test_cfg_path.unlink()

    def test_default_config_creation(self) -> None:
        config = load_config(self.test_cfg_path)
        self.assertTrue(self.test_cfg_path.exists())
        self.assertEqual(config.input_video, "video/video.mp4")
        self.assertEqual(config.clip_duration, 60)
        self.assertEqual(config.video_format, "vertical_blur")

    def test_save_and_reload_config(self) -> None:
        config = load_config(self.test_cfg_path)
        config.video_format = "original"
        config.crf = 20
        save_config(config, self.test_cfg_path)

        reloaded = load_config(self.test_cfg_path)
        self.assertEqual(reloaded.video_format, "original")
        self.assertEqual(reloaded.crf, 20)

    def test_corrupted_config_fallback(self) -> None:
        with open(self.test_cfg_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON DATA ---")
        fallback = load_config(self.test_cfg_path)
        self.assertEqual(fallback.clip_duration, 60)


class TestFFmpegCommands(unittest.TestCase):
    """Test FFmpeg command argument construction."""

    def setUp(self) -> None:
        self.processor = VideoProcessor()
        self.clip = ClipSegment(
            index=1,
            start_time=60.0,
            duration=60.0,
            end_time=120.0,
            filename="short_01.mp4",
        )
        self.in_path = Path("video/video.mp4")
        self.out_path = Path("output/shorts/short_01.mp4")

    def test_original_format_args(self) -> None:
        args = self.processor.build_ffmpeg_args(
            input_path=self.in_path,
            clip=self.clip,
            output_path=self.out_path,
            format_mode="original",
            has_audio=True,
        )
        self.assertEqual(args[0], "ffmpeg")
        self.assertIn("-ss", args)
        self.assertIn("60.000", args)
        self.assertIn("-t", args)
        self.assertIn("libx264", args)
        self.assertIn("aac", args)
        self.assertIn("+faststart", args)

    def test_vertical_blur_filter_args(self) -> None:
        args = self.processor.build_ffmpeg_args(
            input_path=self.in_path,
            clip=self.clip,
            output_path=self.out_path,
            format_mode="vertical_blur",
            has_audio=True,
        )
        self.assertIn("-filter_complex", args)
        self.assertIn("-map", args)
        self.assertIn("[v]", args)
        self.assertIn("boxblur=20:5", "".join(args))

    def test_vertical_crop_filter_args(self) -> None:
        args = self.processor.build_ffmpeg_args(
            input_path=self.in_path,
            clip=self.clip,
            output_path=self.out_path,
            format_mode="vertical_crop",
            has_audio=False,
        )
        self.assertIn("-vf", args)
        self.assertIn("crop=1080:1920", "".join(args))
        self.assertIn("-an", args)  # No audio in source -> -an flag


class TestVideoProbingAndRendering(unittest.TestCase):
    """Integration test: Probe actual video file and render a small test clip."""

    def setUp(self) -> None:
        self.processor = VideoProcessor()
        self.video_path = Path("video/video.mp4")
        self.test_output_dir = Path("output_test")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir, ignore_errors=True)

    def test_probe_real_video(self) -> None:
        """Test probing real video file."""
        if not self.video_path.exists():
            self.skipTest(f"Video file {self.video_path} does not exist.")

        info = self.processor.probe_video(self.video_path)
        self.assertEqual(info.width, 1920)
        self.assertEqual(info.height, 1080)
        self.assertGreater(info.duration, 1500.0)
        self.assertTrue(info.has_audio)
        self.assertGreater(info.fps, 20.0)

    def test_probe_nonexistent_file(self) -> None:
        """Non-existent file must raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.processor.probe_video(Path("video/does_not_exist.mp4"))

    def test_render_sample_clip(self) -> None:
        """Render a small 3-second clip to verify end-to-end splitting & stream verification."""
        if not self.video_path.exists():
            self.skipTest(f"Video file {self.video_path} does not exist.")

        sample_clip = ClipSegment(
            index=1,
            start_time=0.0,
            duration=3.0,
            end_time=3.0,
            filename="test_short_01.mp4",
        )
        out_file = self.test_output_dir / sample_clip.filename

        success, msg = self.processor.render_clip(
            input_path=self.video_path,
            clip=sample_clip,
            output_path=out_file,
            format_mode="vertical_blur",
            has_audio=True,
            crf=22,
            preset="ultrafast",
        )

        self.assertTrue(success, f"Render failed: {msg}")
        self.assertTrue(out_file.exists())
        self.assertGreater(out_file.stat().st_size, 10000)

        # Verify probe of output clip
        info = self.processor.probe_video(out_file)
        self.assertEqual(info.width, 1080)
        self.assertEqual(info.height, 1920)
        self.assertTrue(info.has_audio)
        self.assertAlmostEqual(info.duration, 3.0, delta=1.0)

    def test_render_with_spaces_in_path(self) -> None:
        """Verify that file and folder names containing spaces are handled correctly without shell quoting issues."""
        if not self.video_path.exists():
            self.skipTest(f"Video file {self.video_path} does not exist.")

        folder_with_spaces = self.test_output_dir / "folder with spaces"
        folder_with_spaces.mkdir(parents=True, exist_ok=True)
        out_file = folder_with_spaces / "short clip with spaces.mp4"

        sample_clip = ClipSegment(
            index=1,
            start_time=1.0,
            duration=2.0,
            end_time=3.0,
            filename="short clip with spaces.mp4",
        )

        success, msg = self.processor.render_clip(
            input_path=self.video_path,
            clip=sample_clip,
            output_path=out_file,
            format_mode="original",
            has_audio=True,
            crf=22,
            preset="ultrafast",
        )

        self.assertTrue(success, f"Render with spaces failed: {msg}")
        self.assertTrue(out_file.exists())
        info = self.processor.probe_video(out_file)
        self.assertEqual(info.width, 1920)
        self.assertEqual(info.height, 1080)

    def test_render_center_crop_mode(self) -> None:
        """Verify vertical center crop rendering mode."""
        if not self.video_path.exists():
            self.skipTest(f"Video file {self.video_path} does not exist.")

        out_file = self.test_output_dir / "test_crop_01.mp4"
        sample_clip = ClipSegment(
            index=1,
            start_time=2.0,
            duration=2.0,
            end_time=4.0,
            filename="test_crop_01.mp4",
        )

        success, msg = self.processor.render_clip(
            input_path=self.video_path,
            clip=sample_clip,
            output_path=out_file,
            format_mode="vertical_crop",
            has_audio=True,
            crf=22,
            preset="ultrafast",
        )

        self.assertTrue(success, f"Render crop failed: {msg}")
        self.assertTrue(out_file.exists())
        info = self.processor.probe_video(out_file)
        self.assertEqual(info.width, 1080)
        self.assertEqual(info.height, 1920)

    def test_verify_clip_fails_on_empty_or_corrupt_file(self) -> None:
        """verify_clip must reject empty or zero-byte files."""
        corrupt_file = self.test_output_dir / "corrupt.mp4"
        corrupt_file.write_bytes(b"")  # 0 bytes

        valid, msg = self.processor.verify_clip(corrupt_file, expected_duration=10.0, should_have_audio=True)
        self.assertFalse(valid)
        self.assertIn("suspiciously small", msg)


if __name__ == "__main__":
    unittest.main()
