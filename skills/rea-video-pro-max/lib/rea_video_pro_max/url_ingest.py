"""Bounded, opt-in URL acquisition for public video platform pages.

URL acquisition is deliberately separate from the local analysis kernel.  The
downloader is an optional dependency and never receives credentials, bypasses
DRM, or follows arbitrary local-network targets.
"""
from __future__ import annotations

import datetime as _datetime
import hashlib
import ipaddress
import json
import shutil
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlparse

SUPPORTED_HOSTS = (
    "youtube.com", "youtu.be", "youtube-nocookie.com",
    "facebook.com", "fb.watch", "tiktok.com",
)
DEFAULT_MAX_BYTES = 1 * 1024 * 1024 * 1024
DEFAULT_MAX_SECONDS = 900
DEFAULT_TIMEOUT_SECONDS = 900
VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}


def _host_allowed(host: str) -> bool:
    host = host.lower().rstrip(".")
    return any(host == suffix or host.endswith("." + suffix) for suffix in SUPPORTED_HOSTS)


def validate_url(url: str) -> str:
    """Validate a public YouTube/Facebook/TikTok page URL.

    The platform allowlist prevents the optional downloader from becoming a
    general-purpose SSRF primitive.  Login-only, private, DRM and playlist
    URLs are rejected by policy or by the upstream extractor.
    """
    if not isinstance(url, str) or len(url) > 4096:
        raise ValueError("URL must be a string of at most 4096 characters")
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only http:// and https:// video URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not accepted")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or not _host_allowed(host):
        raise ValueError("URL host is outside the supported public video platforms")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (address.is_private or address.is_loopback or address.is_link_local
                                or address.is_reserved or address.is_multicast or address.is_unspecified):
        raise ValueError("Private or local-network video hosts are not accepted")
    if parsed.fragment:
        # Fragments are client-side state and can change the requested item.
        parsed = parsed._replace(fragment="")
    return parsed.geturl()


def _public_dns(host: str) -> None:
    """Reject platform hostnames that resolve to local/reserved addresses."""
    try:
        results = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as error:
        raise ValueError(f"Could not resolve public video host: {host}") from error
    if not results:
        raise ValueError(f"Could not resolve public video host: {host}")
    for result in results:
        address = result[4][0].split("%", 1)[0]
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as error:
            raise ValueError("Video host returned an invalid network address") from error
        if parsed.is_private or parsed.is_loopback or parsed.is_link_local or parsed.is_reserved \
                or parsed.is_multicast or parsed.is_unspecified:
            raise ValueError("Video host resolves to a private or reserved network")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _empty_or_new(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise ValueError("URL output must be a new directory")
        if any(path.iterdir()):
            raise ValueError("URL output directory must be empty; use a fresh directory")
    path.mkdir(parents=True, exist_ok=True)


def fetch_url(url: str, out_dir: str | Path, *, max_bytes: int = DEFAULT_MAX_BYTES,
              max_seconds: float = DEFAULT_MAX_SECONDS,
              timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Download one public platform video and return a provenance manifest."""
    url = validate_url(url)
    _public_dns(urlparse(url).hostname or "")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= 8 * 1024**3:
        raise ValueError("max_bytes must be an integer in 1..8589934592")
    if isinstance(max_seconds, bool) or not isinstance(max_seconds, (int, float)) or not 1 <= max_seconds <= 900:
        raise ValueError("max_seconds must be in 1..900")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 10 <= timeout_seconds <= 3600:
        raise ValueError("timeout_seconds must be an integer in 10..3600")
    target = Path(out_dir).expanduser().resolve()
    _empty_or_new(target)
    try:
        import yt_dlp
    except ImportError as error:
        raise RuntimeError("URL ingestion requires the optional dependency: pip install 'rea-video-pro-max[url]'") from error

    progress = {"bytes": 0}

    def hook(status):
        progress["bytes"] = max(progress["bytes"], int(status.get("downloaded_bytes") or 0))
        if progress["bytes"] > max_bytes:
            raise yt_dlp.utils.DownloadError("download exceeds the configured byte limit")

    def match_filter(info, *, incomplete):
        duration = info.get("duration")
        if duration is not None and duration > max_seconds:
            return f"video duration exceeds {max_seconds:g} seconds"
        if info.get("is_live"):
            return "live streams are not accepted"
        return None

    with tempfile.TemporaryDirectory(prefix=".rvpm-url-") as temporary:
        staging = Path(temporary)
        options = {
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
            "merge_output_format": "mp4",
            "outtmpl": str(staging / "%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
            "socket_timeout": timeout_seconds,
            "progress_hooks": [hook],
            "match_filter": match_filter,
            "max_filesize": max_bytes,
            "overwrites": False,
        }
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=True)
        except Exception as error:
            # Keep platform/private/DRM failures actionable without exposing a
            # potentially enormous extractor traceback to the calling agent.
            raise RuntimeError(f"Public video download failed: {error}") from error
        if info.get("entries"):
            entries = [entry for entry in info["entries"] if entry]
            if len(entries) != 1:
                raise ValueError("Playlists and multi-video URLs are not accepted")
            info = entries[0]
        candidates = [p for p in staging.iterdir() if p.is_file() and not p.name.endswith((".part", ".ytdl"))
                     and p.suffix.lower() in VIDEO_SUFFIXES]
        if not candidates:
            raise RuntimeError("Downloader produced no supported video file")
        source = max(candidates, key=lambda p: p.stat().st_size)
        size = source.stat().st_size
        if not 1 <= size <= max_bytes:
            raise ValueError("Downloaded video is empty or exceeds the configured byte limit")
        duration = info.get("duration")
        if duration is not None and duration > max_seconds:
            raise ValueError(f"Downloaded video exceeds {max_seconds:g} seconds")
        final = target / ("reference" + source.suffix.lower())
        shutil.move(str(source), final)

    manifest = {
        "schema_version": 1,
        "kind": "rea-video-url-source",
        "requested_url": url,
        "resolved_url": info.get("webpage_url") or info.get("original_url") or url,
        "extractor": info.get("extractor_key") or info.get("extractor"),
        "video_id": info.get("id"),
        "title": info.get("title"),
        "downloaded_path": final.name,
        "bytes": size,
        "sha256": _sha256(final),
        "duration_seconds": duration,
        "width": info.get("width"),
        "height": info.get("height"),
        "extension": final.suffix.lower().lstrip("."),
        "downloader": {"name": "yt-dlp", "version": getattr(yt_dlp, "__version__", "unknown")},
        "policy": {"noplaylist": True, "max_bytes": max_bytes, "max_seconds": max_seconds,
                   "credentials": "not supplied", "drm_or_private_bypass": False},
        "fetched_at": _datetime.datetime.now(_datetime.timezone.utc).isoformat(),
    }
    (target / "url-source.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest
