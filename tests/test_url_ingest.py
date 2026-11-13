"""URL-ingestion policy and provenance tests without external network access."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from rea_video_pro_max.url_ingest import fetch_url, validate_url


@pytest.mark.parametrize("url", [
    "file:///private/reference.mp4",
    "https://example.com/video.mp4",
    "https://user:secret@youtube.com/watch?v=abc",
    "http://127.0.0.1/video",
])
def test_url_policy_rejects_non_platform_or_local_targets(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_url_policy_normalizes_fragment():
    assert validate_url("https://www.youtube.com/shorts/abc#t=4") == "https://www.youtube.com/shorts/abc"


def test_fetch_records_hash_and_policy(monkeypatch, tmp_path):
    class DownloadError(Exception):
        pass

    class YoutubeDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download=True):
            path = Path(self.options["outtmpl"].replace("%(id)s", "fixture").replace("%(ext)s", "mp4"))
            path.write_bytes(b"owned URL fixture")
            for hook in self.options["progress_hooks"]:
                hook({"downloaded_bytes": path.stat().st_size})
            return {
                "id": "fixture", "title": "Owned URL fixture", "extractor_key": "Youtube",
                "webpage_url": url, "duration": 2.0, "width": 640, "height": 360,
            }

    fake = types.SimpleNamespace(YoutubeDL=YoutubeDL, version="test", utils=types.SimpleNamespace(DownloadError=DownloadError))
    monkeypatch.setitem(sys.modules, "yt_dlp", fake)
    monkeypatch.setattr("rea_video_pro_max.url_ingest._public_dns", lambda host: None)
    manifest = fetch_url("https://youtu.be/fixture", tmp_path / "source", max_bytes=1024, max_seconds=10, timeout_seconds=10)
    media = tmp_path / "source" / manifest["downloaded_path"]
    assert media.read_bytes() == b"owned URL fixture"
    assert manifest["sha256"]
    assert manifest["bytes"] == media.stat().st_size
    assert manifest["policy"]["noplaylist"] is True
    assert (tmp_path / "source" / "url-source.json").is_file()


def test_fetch_requires_fresh_output(monkeypatch, tmp_path):
    monkeypatch.setattr("rea_video_pro_max.url_ingest._public_dns", lambda host: None)
    target = tmp_path / "source"
    target.mkdir()
    (target / "existing.txt").write_text("keep")
    with pytest.raises(ValueError, match="empty"):
        fetch_url("https://youtu.be/fixture", target)


def test_youtube_retries_public_progressive_format(monkeypatch, tmp_path):
    class DownloadError(Exception):
        pass

    class YoutubeDL:
        attempts = []

        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download=True):
            self.attempts.append(self.options["format"])
            if len(self.attempts) == 1:
                raise DownloadError("HTTP Error 403")
            path = Path(self.options["outtmpl"].replace("%(id)s", "fallback").replace("%(ext)s", "mp4"))
            path.write_bytes(b"progressive fixture")
            return {"id": "fallback", "title": "Fallback", "duration": 1.0,
                    "extractor_key": "Youtube", "webpage_url": url, "format_id": "18"}

    fake = types.SimpleNamespace(YoutubeDL=YoutubeDL, __version__="test",
                                 utils=types.SimpleNamespace(DownloadError=DownloadError))
    monkeypatch.setitem(sys.modules, "yt_dlp", fake)
    monkeypatch.setattr("rea_video_pro_max.url_ingest._public_dns", lambda host: None)
    manifest = fetch_url("https://youtu.be/fallback", tmp_path / "source", max_bytes=1024,
                         max_seconds=10, timeout_seconds=10)
    assert YoutubeDL.attempts == ["bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b", "18"]
    assert manifest["downloader"]["strategy"] == "youtube-progressive-fallback"
