"""
Automated Test Suite for Universal Video Downloader
Tests:
- FFmpeg available and missing
- Successful download with separate video and audio streams
- Download of a source with combined video and audio
- Missing audio in the final output (detects and flags error)
- Merge failure handling
- Invalid URL and network failure handling
- Stream verification of output files via ffprobe
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import config as config_mgr
import downloader


class TestDownloader(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            "download_dir": self.test_dir,
            "quality_mode": "best",
            "container_preference": "mp4",
            "auto_download": True
        }

    def tearDown(self):
        # Cleanup temp directory
        try:
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(self.test_dir)
        except Exception:
            pass

    # 1. FFmpeg available
    @patch("downloader.shutil.which")
    @patch("downloader.subprocess.run")
    def test_ffmpeg_available(self, mock_subproc, mock_which):
        mock_which.side_effect = lambda cmd: f"C:\\fake_path\\{cmd}.exe"
        mock_subproc.return_value = MagicMock(
            returncode=0,
            stdout="ffmpeg version 9.0.2-test-build Copyright (c)"
        )

        res = downloader.check_ffmpeg_installed()
        self.assertTrue(res["ffmpeg_available"])
        self.assertTrue(res["ffprobe_available"])
        self.assertIn("9.0.2", res["version"])

    # 2. FFmpeg missing
    @patch("downloader.shutil.which", return_value=None)
    @patch("os.path.isfile", return_value=False)
    def test_ffmpeg_missing(self, mock_isfile, mock_which):
        res = downloader.check_ffmpeg_installed()
        self.assertFalse(res["ffmpeg_available"])
        self.assertFalse(res["ffprobe_available"])

        instructions = downloader.get_ffmpeg_install_instructions()
        self.assertIn("winget install Gyan.FFmpeg", instructions)
        self.assertIn("FFMPEG INSTALLATION REQUIRED", instructions)

    # 3. Successful download with separate video and audio streams
    @patch("downloader.check_ffmpeg_installed")
    @patch("downloader.inspect_video")
    @patch("downloader.verify_file_streams")
    @patch("downloader.yt_dlp.YoutubeDL")
    def test_download_separate_video_and_audio(self, mock_ydl_cls, mock_verify, mock_inspect, mock_ffmpeg):
        mock_ffmpeg.return_value = {
            "ffmpeg_available": True,
            "ffprobe_available": True,
            "ffmpeg_dir": "C:\\fake\\bin",
            "ffprobe_path": "C:\\fake\\bin\\ffprobe.exe",
            "version": "ffmpeg 9.0"
        }

        # Mock metadata with separate video and audio tracks
        mock_inspect.return_value = {
            "title": "Blender 4K Demo",
            "acodec": "opus",
            "formats": [
                {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080},
                {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "abr": 128}
            ]
        }

        # Mock yt_dlp download to write the dummy file during download execution
        def fake_download(urls):
            dummy_file = os.path.join(self.test_dir, "Blender 4K Demo.mp4")
            with open(dummy_file, "wb") as f:
                f.write(b"\x00" * 4096)
            return 0

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.download.side_effect = fake_download
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        mock_verify.return_value = {
            "exists": True,
            "file_size": 4096,
            "has_video": True,
            "has_audio": True,
            "video_codec": "h264",
            "audio_codec": "aac",
            "verified": True,
            "error": None
        }

        result = downloader.download_video("https://example.com/separate", self.config)
        self.assertTrue(result["success"])
        self.assertTrue(result["has_video"])
        self.assertTrue(result["has_audio"])
        self.assertEqual(result["audio_codec"], "aac")
        self.assertEqual(result["video_codec"], "h264")

    # 4. Download of a source with combined video and audio
    @patch("downloader.check_ffmpeg_installed")
    @patch("downloader.inspect_video")
    @patch("downloader.verify_file_streams")
    @patch("downloader.yt_dlp.YoutubeDL")
    def test_download_combined_video_audio(self, mock_ydl_cls, mock_verify, mock_inspect, mock_ffmpeg):
        mock_ffmpeg.return_value = {
            "ffmpeg_available": True,
            "ffprobe_available": True,
            "ffmpeg_dir": "C:\\fake\\bin",
            "ffprobe_path": "C:\\fake\\bin\\ffprobe.exe",
            "version": "ffmpeg 9.0"
        }

        # Combined format (format 18 / 22)
        mock_inspect.return_value = {
            "title": "Combined Nature Video",
            "formats": [
                {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a", "height": 360}
            ]
        }

        def fake_download(urls):
            dummy_file = os.path.join(self.test_dir, "Combined Nature Video.mp4")
            with open(dummy_file, "wb") as f:
                f.write(b"\x00" * 2048)
            return 0

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.download.side_effect = fake_download
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        mock_verify.return_value = {
            "exists": True,
            "file_size": 2048,
            "has_video": True,
            "has_audio": True,
            "video_codec": "h264",
            "audio_codec": "aac",
            "verified": True,
            "error": None
        }

        result = downloader.download_video("https://example.com/combined", self.config)
        self.assertTrue(result["success"])
        self.assertTrue(result["has_audio"])
        self.assertTrue(result["has_video"])

    # 5. Missing audio in the final output -> MUST trigger DownloadVerificationError
    @patch("downloader.check_ffmpeg_installed")
    @patch("downloader.inspect_video")
    @patch("downloader.verify_file_streams")
    @patch("downloader.yt_dlp.YoutubeDL")
    def test_missing_audio_in_final_output(self, mock_ydl_cls, mock_verify, mock_inspect, mock_ffmpeg):
        mock_ffmpeg.return_value = {
            "ffmpeg_available": True,
            "ffprobe_available": True,
            "ffmpeg_dir": "C:\\fake\\bin",
            "ffprobe_path": "C:\\fake\\bin\\ffprobe.exe",
            "version": "ffmpeg 9.0"
        }

        # Source HAS audio
        mock_inspect.return_value = {
            "title": "Bugged Video No Sound",
            "formats": [
                {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080},
                {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "abr": 128}
            ]
        }

        def fake_download(urls):
            dummy_file = os.path.join(self.test_dir, "Bugged Video No Sound.mp4")
            with open(dummy_file, "wb") as f:
                f.write(b"\x00" * 2048)
            return 0

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.download.side_effect = fake_download
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        # Output file is missing audio! has_audio = False
        mock_verify.return_value = {
            "exists": True,
            "file_size": 2048,
            "has_video": True,
            "has_audio": False,  # Missing audio!
            "video_codec": "h264",
            "audio_codec": None,
            "verified": True,
            "error": None
        }

        with self.assertRaises(downloader.DownloadVerificationError) as ctx:
            downloader.download_video("https://example.com/buggy", self.config)

        self.assertIn("Missing Audio Stream Error", str(ctx.exception))

    # 6. Merge failure
    @patch("downloader.check_ffmpeg_installed")
    @patch("downloader.inspect_video")
    @patch("downloader.yt_dlp.YoutubeDL")
    def test_merge_failure(self, mock_ydl_cls, mock_inspect, mock_ffmpeg):
        mock_ffmpeg.return_value = {
            "ffmpeg_available": True,
            "ffprobe_available": True,
            "ffmpeg_dir": "C:\\fake\\bin",
            "version": "ffmpeg 9.0"
        }

        mock_inspect.return_value = {
            "title": "Merge Crash Clip",
            "formats": [
                {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a"}
            ]
        }

        mock_ydl_instance = MagicMock()
        # Non-zero exit code
        mock_ydl_instance.download.return_value = 1
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        with self.assertRaises(RuntimeError) as ctx:
            downloader.download_video("https://example.com/fail", self.config)

        self.assertIn("failed with exit code 1", str(ctx.exception))

    # 7. Invalid URL and network failure
    @patch("downloader.check_ffmpeg_installed")
    @patch("downloader.inspect_video")
    def test_invalid_url_and_network_failure(self, mock_inspect, mock_ffmpeg):
        mock_ffmpeg.return_value = {"ffmpeg_available": True}
        mock_inspect.side_effect = RuntimeError("Could not resolve host / 404 Not Found")

        with self.assertRaises(RuntimeError) as ctx:
            downloader.download_video("https://invalid-nonexistent-domain.xyz/video", self.config)

        self.assertIn("Failed to retrieve video information", str(ctx.exception))

    # 8. Successful verification of the output file via ffprobe
    @patch("downloader.subprocess.run")
    def test_successful_verification_of_output_file(self, mock_subproc):
        # Create real temp file
        sample_path = os.path.join(self.test_dir, "sample.mp4")
        with open(sample_path, "wb") as f:
            f.write(b"\x00" * 1024)

        # Mock ffprobe JSON output
        probe_json = {
            "streams": [
                {"index": 0, "codec_name": "h264", "codec_type": "video"},
                {"index": 1, "codec_name": "aac", "codec_type": "audio"}
            ]
        }
        mock_subproc.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(probe_json)
        )

        res = downloader.verify_file_streams(sample_path, ffprobe_path="C:\\fake\\ffprobe.exe")
        self.assertTrue(res["exists"])
        self.assertEqual(res["file_size"], 1024)
        self.assertTrue(res["has_video"])
        self.assertTrue(res["has_audio"])
        self.assertEqual(res["video_codec"], "h264")
        self.assertEqual(res["audio_codec"], "aac")
        self.assertTrue(res["verified"])

    # 9. Verification of 0-byte file
    def test_verification_empty_file(self):
        empty_path = os.path.join(self.test_dir, "empty.mp4")
        with open(empty_path, "wb") as f:
            pass  # 0 bytes

        res = downloader.verify_file_streams(empty_path)
        self.assertTrue(res["exists"])
        self.assertEqual(res["file_size"], 0)
        self.assertFalse(res["verified"])
        self.assertIn("empty", res["error"])

    # 10. Filename sanitization
    def test_sanitize_filename(self):
        dirty = 'My Video: Episode 1 / "Special" <4K>? *Cool* | Test'
        cleaned = downloader.sanitize_filename(dirty)
        self.assertNotIn(":", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertNotIn('"', cleaned)
        self.assertNotIn("<", cleaned)
        self.assertNotIn(">", cleaned)
        self.assertNotIn("?", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("|", cleaned)


if __name__ == "__main__":
    unittest.main()
