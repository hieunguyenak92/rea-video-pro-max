"""Shared boundary validation, identity, time math and capability inventory."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

from . import __version__

MAX_JSON = 16 * 1024 * 1024
KINDS = {"rea-video-analysis", "rea-video-style-template", "rea-video-project", "rea-video-content"}


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _finite(value: Any, depth: int = 0) -> None:
    if depth > 64:
        raise ValueError("JSON exceeds nesting limit")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite JSON number")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _finite(child, depth + 1)


def read_json(path: str | Path, *, limit: int = MAX_JSON) -> dict:
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("JSON exceeds byte limit")
    try:
        value = json.loads(data.decode("utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError(f"Invalid JSON constant: {x}")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"Invalid UTF-8 JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("Artifact must be a JSON object")
    _finite(value)
    return value


def write_json(path: str | Path, value: dict) -> Path:
    _finite(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".rvpm-", delete=False) as output:
            temporary = Path(output.name)
            output.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def bounded_number(value: Any, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if not low <= value <= high:
        raise ValueError(f"{name} outside [{low}, {high}]")
    return float(value)


def validate(value: dict, expected: str | None = None) -> dict:
    _finite(value)
    if not isinstance(value, dict):
        raise ValueError("Artifact must be an object")
    kind = value.get("kind")
    if kind not in KINDS or value.get("schema_version") != 1:
        raise ValueError("Unknown artifact kind or schema_version; expected version 1")
    if expected and kind != expected:
        raise ValueError(f"Expected {expected}, got {kind}")
    nested = {"rea-video-style-template": ("reference", "style", "rhythm", "motion"),
              "rea-video-project": ("render", "style", "font", "provenance")}.get(kind, ())
    for name in nested:
        if not isinstance(value.get(name), dict):
            raise ValueError(f"{kind} requires object {name}")
    if kind == "rea-video-project":
        for name in ("scenes", "captions", "assets"):
            if not isinstance(value.get(name), list) or any(not isinstance(x, dict) for x in value[name]):
                raise ValueError(f"Project {name} must be a list of objects")
    if kind == "rea-video-analysis":
        source = value.get("source", {})
        if not isinstance(source, dict):
            raise ValueError("Analysis source must be an object")
        bounded_number(source.get("duration"), "source.duration", 0, 86400)
        if not isinstance(value.get("shots"), list):
            raise ValueError("Analysis needs shots")
        last = 0.0
        for shot in value["shots"]:
            if not isinstance(shot, dict):
                raise ValueError("Shot must be an object")
            start = bounded_number(shot.get("start"), "shot.start", 0, source["duration"] + .1)
            end = bounded_number(shot.get("end"), "shot.end", start, source["duration"] + .1)
            if start + 1e-6 < last or end <= start:
                raise ValueError("Shot intervals must be ordered and non-overlapping")
            last = end
        for key in ("captions", "motion", "claims", "unknowns", "evidence"):
            if key in value and (not isinstance(value[key], list) or any(not isinstance(x, dict) for x in value[key])):
                raise ValueError(f"Analysis {key} must be a list of objects")
        if not isinstance(value.get("style", {}), dict):
            raise ValueError("Analysis style must be an object")
        for cue in value.get("captions", []):
            if not isinstance(cue.get("text"), str):
                raise ValueError("Caption text must be a string")
            start = bounded_number(cue.get("start"), "caption.start", 0, source["duration"]+.1)
            end = bounded_number(cue.get("end"), "caption.end", start, source["duration"]+.1)
            if source["duration"] > 0 and end <= start:
                raise ValueError("Caption end must follow start")
            box = cue.get("bbox")
            if box is not None:
                if not isinstance(box, list) or len(box) != 4:
                    raise ValueError("Caption bbox must be normalized xywh")
                for n in box:
                    bounded_number(n, "caption.bbox", 0, 1)
        if not isinstance(source.get("path"), str) or not isinstance(source.get("sha256"), str):
            raise ValueError("Source requires path and sha256 strings")
        for key in ("width", "height"):
            bounded_number(source.get(key), f"source.{key}", 1, 16000000)
    if kind == "rea-video-content":
        scenes = value.get("scenes")
        if not isinstance(scenes, list) or not 1 <= len(scenes) <= 256:
            raise ValueError("Content requires 1–256 scenes")
        for scene in scenes:
            if not isinstance(scene, dict) or not isinstance(scene.get("text", ""), str):
                raise ValueError("Each scene needs text")
            if len(scene.get("text", "")) > 8000:
                raise ValueError("Scene text exceeds limit")
            if "duration" in scene:
                bounded_number(scene["duration"], "scene.duration", .1, 120)
        for key, default, low, high in [("width", 640, 64, 3840), ("height", 360, 64, 3840),
                                        ("fps", 30, 1, 60)]:
            n = bounded_number(value.get(key, default), key, low, high)
            if not n.is_integer():
                raise ValueError(f"{key} must be integer")
    return value


def time_value(seconds: float, rate: int = 1_000_000) -> dict:
    fraction = Fraction(str(seconds)).limit_denominator(rate)
    return {"value": fraction.numerator, "rate": fraction.denominator}


def confined(workspace: str | Path, path: str | Path, *, must_exist: bool = False) -> Path:
    root = Path(workspace).resolve(strict=True)
    path = Path(path)
    resolved = (root / path if not path.is_absolute() else path).resolve(strict=must_exist)
    if not resolved.is_relative_to(root):
        raise ValueError("Path is outside the explicit workspace")
    return resolved


def tool(command: list[str], timeout: int = 10) -> dict:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {"available": result.returncode == 0, "exit_code": result.returncode,
                "output": (result.stdout + result.stderr)[-24000:]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": False, "reason": str(error)}


def doctor() -> dict:
    versions = {}
    for package in ["Pillow", "numpy", "av", "mcp", "opentimelineio", "faster-whisper", "ctranslate2", "yt-dlp"]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    ffmpeg = tool(["ffmpeg", "-version"])
    filters = tool(["ffmpeg", "-hide_banner", "-filters"])
    encoders = tool(["ffmpeg", "-hide_banner", "-encoders"])
    tesseract = tool(["tesseract", "--list-langs"])
    font_dir = Path(__file__).resolve().parents[2] / "assets/fonts"
    if not font_dir.is_dir():
        font_dir = Path(__file__).resolve().parent / "resources/fonts"
    fonts = [{"name": x.name, "sha256": sha256(x)} for x in sorted(font_dir.glob("*.ttf"))]
    return {"schema_version": 1, "kind": "rea-video-capabilities", "version": __version__,
            "platform": platform.platform(), "python": platform.python_version(), "packages": versions,
            "ffmpeg": {**ffmpeg, "path": shutil.which("ffmpeg"),
                       "libx264": "libx264 " in encoders.get("output", ""),
                       "filters": {n: any(line.split()[1:2] == [n] for line in
                                          filters.get("output", "").splitlines())
                                   for n in ["ass", "subtitles", "drawtext", "ssim", "libvmaf"]}},
            "ffprobe": tool(["ffprobe", "-version"]), "tesseract": tesseract, "fonts": fonts,
            "network": "No content upload or model download in the native pipeline; URL ingestion is explicit and optional.",
            "limitations": ["Tesseract language availability is not certified OCR accuracy.",
                            "Native renderer: 2D graphics/captions; complex scripts need a verified shaper.",
                            "Metadata/analysis does not identify the original editing project uniquely."]}
