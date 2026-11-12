"""Portable, seekable 2D renderer for content-bound projects.

Pillow supplies typography/graphics, PyAV decodes explicitly bound footage, and
FFmpeg encodes/muxes. No browser, libass or reference-media fallback is required.
"""

from __future__ import annotations

import json
import math
import os
import select
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import av
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, features

from .core import read_json, validate

from .template import MAX_DURATION, MAX_FRAMES, MAX_PIXELS, SUPPORTED_TRANSITIONS, VARIANT_FIELDS, _check_glyphs, _color, _digest, _number, _validated_style, _write

VIDEO_DEMUXERS = "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,avi"
AUDIO_DEMUXERS = VIDEO_DEMUXERS + ",wav,mp3,flac,ogg,aac,aiff,au"


def _local(root, value):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("project asset path is invalid")
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError("portable project assets must use relative paths")
    candidate = (root / candidate).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError("project asset escapes project or is missing")
    return candidate


def _load_project(project_path):
    path = Path(project_path).resolve()
    if path.is_dir():
        path /= "project.json"
    if not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("project JSON missing or exceeds 16 MiB")
    project = validate(read_json(path), "rea-video-project")
    if not isinstance(project, dict):
        raise ValueError("project must be an object")
    if project.get("kind") != "rea-video-project" or project.get("schema_version") != 1:
        raise ValueError("expected schema_version 1 rea-video-project")
    root = path.parent
    settings = project.get("render", {})
    raw_width = _number(settings.get("width"), "width", 64, 3840)
    raw_height = _number(settings.get("height"), "height", 64, 3840)
    if not raw_width.is_integer() or not raw_height.is_integer():
        raise ValueError("render dimensions must be integers")
    width, height = int(raw_width), int(raw_height)
    fps = _number(settings.get("fps"), "fps", 1, 60)
    duration = _number(settings.get("duration"), "duration", 0.1, MAX_DURATION)
    if width % 2 or height % 2 or width * height > MAX_PIXELS:
        raise ValueError("invalid even render dimensions/pixel budget")
    count = math.ceil(duration * fps)
    if count > MAX_FRAMES or settings.get("frame_count") != count:
        raise ValueError("project frame count is inconsistent or exceeds budget")
    assets = project.get("assets")
    if not isinstance(assets, list) or not 1 <= len(assets) <= 258:
        raise ValueError("project requires a bounded asset manifest")
    manifest = {}
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("role") not in {"font", "media", "audio"}:
            raise ValueError("invalid asset record or role")
        source = _local(root, asset.get("path"))
        if source.stat().st_size > 1024 * 1024 * 1024 or source.stat().st_size != asset.get("bytes") or _digest(source) != asset.get("sha256"):
            raise ValueError(f"project asset changed: {asset.get('path')}")
        if asset["path"] in manifest and asset != manifest[asset["path"]]:
            raise ValueError("conflicting project asset records")
        manifest[asset["path"]] = asset
    def bound(record, role):
        if not isinstance(record, dict) or record.get("role") != role or record != manifest.get(record.get("path")):
            raise ValueError("bound asset differs from hashed project manifest")
        return _local(root, record["path"])
    font_path = bound(project.get("font"), "font")
    if project.get("audio"):
        bound(project["audio"], "audio")
        _number(project["audio"].get("offset", 0), "audio offset", -MAX_DURATION, MAX_DURATION)
    reference_hash = project.get("reference", {}).get("sha256")
    reused = bool(reference_hash and any(a["sha256"] == reference_hash for a in assets))
    if reused and not project.get("provenance", {}).get("reference_reuse_authorized", False):
        raise ValueError("reference media reuse is not authorized by this project")
    if project.get("provenance", {}).get("content") != "explicit-new-content-bindings":
        raise ValueError("project lacks explicit content provenance")
    scenes = project.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 256:
        raise ValueError("project requires 1..256 scenes")
    previous_end = 0.0
    ids = set()
    caption_texts = []
    project["style"] = _validated_style(project.get("style", {}))
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict) or not isinstance(scene.get("id"), str) or scene["id"] in ids:
            raise ValueError("scene records require unique string IDs")
        ids.add(scene["id"])
        start = _number(scene.get("start"), "scene start", 0, duration)
        end = _number(scene.get("end"), "scene end", start, duration + 1e-6)
        length = _number(scene.get("duration"), "scene duration", 0.1, 120)
        if abs(end - start - length) > 1e-6:
            raise ValueError("scene interval differs from its duration")
        transition = scene.get("transition", {})
        overlap = _number(transition.get("duration", 0), "transition duration", 0, min(2, length / 4))
        if transition.get("family", "cut") not in SUPPORTED_TRANSITIONS:
            raise ValueError("unsupported scene transition")
        if transition.get("family", "cut") == "cut" and overlap:
            raise ValueError("cut transitions cannot declare overlap")
        expected_start = previous_end - overlap if index else 0
        if abs(start - expected_start) > 1e-6:
            raise ValueError("scene coverage has an undeclared gap or overlap")
        previous_end = end
        if scene.get("asset"):
            bound(scene["asset"], "media")
            if scene["asset"].get("type") not in {"image", "video"}:
                raise ValueError("unsupported scene media type")
        _number(scene.get("asset_start", 0), "asset start", 0, MAX_DURATION)
        _color(scene.get("background"), [17, 24, 39])
        _color(scene.get("accent"), [255, 222, 89])
        if not isinstance(scene.get("accent_explicit", True), bool):
            raise ValueError("accent_explicit must be boolean")
        cues = scene.get("captions", [])
        if not isinstance(cues, list) or len(cues) > 10000:
            raise ValueError("invalid caption list")
        previous_cue = 0.0
        for cue in cues:
            if not isinstance(cue, dict) or not isinstance(cue.get("text"), str):
                raise ValueError("caption records require text")
            cstart = _number(cue.get("start"), "caption start", 0, length)
            cend = _number(cue.get("end"), "caption end", cstart, length + 1e-6)
            if cstart < previous_cue - 1e-6 or cend <= cstart:
                raise ValueError("caption intervals must be ordered, non-overlapping and nonempty")
            previous_cue = cend
            override = cue.get("style", {})
            if not isinstance(override, dict) or override.keys() - VARIANT_FIELDS:
                raise ValueError("unsupported caption style override")
            if override:
                merged_style = _validated_style({**project["style"], **override})
                cue["style"] = {key: merged_style[key] for key in override}
            words = cue.get("words")
            if not isinstance(words, list) or not 1 <= len(words) <= 12:
                raise ValueError("caption group requires 1..12 word records")
            previous_word = cstart
            for word in words:
                if not isinstance(word, dict) or not isinstance(word.get("text"), str) or not word["text"] or len(word["text"]) > 100000:
                    raise ValueError("invalid caption word")
                start_word = _number(word.get("start"), "word start", cstart, cend)
                end_word = _number(word.get("end"), "word end", start_word, cend)
                if start_word < previous_word - 1e-6 or end_word <= start_word:
                    raise ValueError("word intervals must be ordered, non-overlapping and nonempty")
                previous_word = end_word
                if "highlight" in word:
                    _color(word["highlight"], [255, 255, 255])
            if " ".join(word["text"] for word in words) != cue["text"]:
                raise ValueError("caption text differs from word content")
            caption_texts.append(cue["text"])
    if abs(previous_end - duration) > 1e-6:
        raise ValueError("scene coverage does not reach the project end")
    if sum(len(text) for text in caption_texts) > 100000:
        raise ValueError("caption content exceeds 100,000 characters")
    _check_glyphs(font_path, " ".join(caption_texts))
    project["style"] = _validated_style(project.get("style", {}))
    return project, root, path


class _Footage:
    """Forward-only bounded video decoder; frame time is PTS, never frame/fps."""

    def __init__(self, path):
        try:
            self.container = av.open(str(path), options={"protocol_whitelist": "file,pipe", "format_whitelist": VIDEO_DEMUXERS})
        except av.error.FFmpegError as exc:
            raise ValueError("bound footage is unreadable or uses an unsupported media demuxer") from exc
        candidates = [s for s in self.container.streams.video if not (int(s.disposition) & 0x400)]
        if not candidates:
            self.container.close()
            raise ValueError("bound footage has no non-attached video stream")
        self.stream = max(candidates, key=lambda s: s.width * s.height)
        sar = self.stream.sample_aspect_ratio
        if sar is not None and float(sar) not in (0.0, 1.0):
            self.container.close()
            raise ValueError("anamorphic footage must be prepared as square-pixel media first")
        if self.stream.width * self.stream.height > 16384 * 8192:
            self.container.close()
            raise ValueError("bound footage exceeds decoded source pixel budget")
        self.stream.thread_type = "SLICE"
        self.stream.codec_context.thread_count = 1
        self.frames = self.container.decode(self.stream)
        self.current = None
        self.pending = None
        self.origin = None
        self.decoded = 0
        self.last_request = -math.inf
        self.eof = False

    def _next(self):
        try:
            frame = next(self.frames)
        except StopIteration:
            self.eof = True
            return None
        self.decoded += 1
        if self.decoded > 500000:
            raise ValueError("bound footage exceeds 500,000-frame decode budget")
        if frame.pts is None or frame.time_base is None:
            raise ValueError("bound footage frame has no presentation timestamp")
        if any("DISPLAYMATRIX" in str(side.type) for side in frame.side_data):
            raise ValueError("display-matrix footage must be prepared as upright square-pixel media first")
        if frame.width * frame.height > 16384 * 8192:
            raise ValueError("bound footage frame exceeds decoded source pixel budget")
        stamp = float(frame.pts * frame.time_base)
        if self.origin is None:
            self.origin = stamp
        return stamp - self.origin, frame

    def at(self, seconds):
        if seconds + 1e-8 < self.last_request:
            raise ValueError("native footage decoder only supports monotonic scene playback")
        self.last_request = seconds
        if self.pending is None and not self.eof:
            self.pending = self._next()
        while self.pending is not None and (self.current is None or self.pending[0] <= seconds + 1e-8):
            self.current = self.pending
            self.pending = self._next() if not self.eof else None
        if self.current is None:
            raise ValueError("bound footage decoded no video frames")
        return self.current[1].to_image().convert("RGB")

    def close(self):
        self.container.close()


def _cover(image, width, height, scale=1.0, pan_x=0.0, pan_y=0.0):
    if image.width * image.height > 16384 * 8192:
        raise ValueError("image source exceeds decoded pixel budget")
    factor = max(width / image.width, height / image.height) * scale
    crop_width, crop_height = width / factor, height / factor
    left = max(0, min(image.width - crop_width, (image.width - crop_width) * (0.5 + pan_x)))
    top = max(0, min(image.height - crop_height, (image.height - crop_height) * (0.5 + pan_y)))
    # Resample only the source crop. Resizing an extreme panorama before cropping
    # would allocate a huge intermediate despite a small requested canvas.
    return image.resize((width, height), Image.Resampling.LANCZOS, box=(left, top, left + crop_width, top + crop_height))


def _ease(progress):
    progress = min(1.0, max(0.0, progress))
    return progress * progress * (3 - 2 * progress)


def _wrap(words, font, width):
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = []
    line = []
    for index, word in enumerate(words):
        candidate = [*line, (index, word)]
        if line and draw.textlength(" ".join(w for _, w in candidate), font=font) > width:
            lines.append(line)
            line = [(index, word)]
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def _caption(image, scene, local_time, style, font_path):
    cue = next((cue for cue in scene.get("captions", []) if cue["start"] <= local_time < cue["end"]), None)
    if cue is None:
        return image
    style = {**style, **cue.get("style", {})}
    width, height = image.size
    size = max(12, round(_number(style.get("font_size_ratio", 0.055), "font size ratio", 0.01, 0.2) * height))
    max_width = round(width * _number(style.get("max_width_ratio", 0.88), "caption max width", 0.2, 0.98))
    words = [word["text"] for word in cue["words"]]
    # Fit new text, including longer words and groups, rather than clipping it.
    while True:
        font = ImageFont.truetype(str(font_path), size)
        lines = _wrap(words, font, max_width)
        measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        widest = max(measure.textlength(" ".join(w for _, w in line), font=font) for line in lines)
        if size <= 10 or (widest <= max_width and len(lines) * size * 1.2 <= height * 0.45):
            break
        size -= 1
    if widest > max_width + 1:
        raise ValueError("caption contains an unbreakable word that cannot fit the canvas")
    stroke_width = max(0, round(height * _number(style.get("stroke_width_ratio", 0.003), "stroke ratio", 0, 0.025)))
    padding = max(5, round(size * 0.24)) + stroke_width
    line_height = round(size * _number(style.get("line_height", 1.2), "line height", 1, 2))
    block_width = min(width, math.ceil(widest) + padding * 2)
    block_height = line_height * len(lines) + padding * 2
    block = Image.new("RGBA", (block_width, block_height))
    plate = _color(style.get("box_color"), [0, 0, 0, 0])
    if len(plate) == 3:
        plate.append(220)
    draw = ImageDraw.Draw(block)
    draw.rounded_rectangle((0, 0, block_width - 1, block_height - 1), radius=max(2, size // 5), fill=tuple(plate))
    active_word = next((i for i, word in enumerate(cue["words"]) if word["start"] <= local_time < word["end"]), None)
    fill = tuple(_color(style.get("fill"), [255, 255, 255]))
    outline = tuple(_color(style.get("stroke"), [0, 0, 0]))
    highlight = scene.get("accent", style.get("highlight")) if scene.get("accent_explicit", True) else style.get("highlight")
    if active_word is not None and not scene.get("accent_explicit", True):
        highlight = cue["words"][active_word].get("highlight", highlight)
    highlight = tuple(_color(highlight, [255, 222, 89]))
    shadow_color = _color(style.get("shadow"), [0, 0, 0, 140])
    if len(shadow_color) == 3:
        shadow_color.append(140)
    shadow = Image.new("RGBA", block.size)
    shadow_draw = ImageDraw.Draw(shadow)
    space = draw.textlength(" ", font=font)
    for row, line in enumerate(lines):
        line_width = draw.textlength(" ".join(word for _, word in line), font=font)
        x = (block_width - line_width) / 2
        y = padding + row * line_height
        for index, word in line:
            shadow_draw.text((x + max(1, size // 14), y + max(1, size // 14)), word, font=font, fill=tuple(shadow_color), stroke_width=stroke_width, stroke_fill=tuple(shadow_color), anchor="lt")
            draw.text((x, y), word, font=font, fill=highlight if index == active_word else fill, stroke_width=stroke_width, stroke_fill=outline, anchor="lt")
            x += draw.textlength(word, font=font) + space
    # Put the shadow behind text and plate, not over the visible glyphs.
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(0.5, size / 24)))
    shadow.alpha_composite(block)
    block = shadow
    elapsed = local_time - cue["start"]
    entry_duration = min(style.get("entry_duration", 0.18), max(0.01, (cue["end"] - cue["start"]) / 3))
    progress = min(1.0, max(0.0, elapsed / max(entry_duration, 0.001)))
    entry = style.get("entry", "fade")
    alpha = 1.0
    offset = 0.0
    if entry == "fade":
        alpha = _ease(progress)
    elif entry == "slide":
        alpha = min(1.0, progress * 2)
        offset = size * 0.7 * (1 - _ease(progress))
    elif entry == "pop":
        scale = 0.80 + 0.20 * _ease(min(1, progress * 1.6)) + 0.10 * math.sin(math.pi * progress)
        block = block.resize((max(1, round(block.width * scale)), max(1, round(block.height * scale))), Image.Resampling.LANCZOS)
    if alpha < 1:
        block.putalpha(block.getchannel("A").point(lambda value: round(value * alpha)))
    anchor = style.get("anchor", "bottom")
    anchor_y = style.get("anchor_y", {"top": 0.18, "center": 0.5, "bottom": 0.82}.get(anchor, 0.82))
    center_x = _number(style.get("anchor_x", 0.5), "anchor x", 0.05, 0.95) * width
    center_y = _number(anchor_y, "anchor y", 0.05, 0.95) * height
    x = max(0, min(width - block.width, round(center_x - block.width / 2)))
    y = max(0, min(height - block.height, round(center_y - block.height / 2 + offset)))
    output = image.convert("RGBA")
    output.alpha_composite(block, (x, y))
    return output.convert("RGB")


def _visual(scene, local_time, project, root, readers):
    settings = project["render"]
    width, height = settings["width"], settings["height"]
    record = scene.get("asset")
    if record:
        path = _local(root, record["path"])
        if record.get("type") == "video":
            key = scene["id"]
            if key not in readers:
                readers[key] = _Footage(path)
            frame = readers[key].at(scene.get("asset_start", 0) + max(0, local_time))
        elif record.get("type") == "image":
            key = scene["id"]
            if key not in readers:
                with Image.open(path) as opened:
                    readers[key] = ImageOps.exif_transpose(opened).convert("RGB")
            frame = readers[key]
        else:
            raise ValueError("bound scene asset has unsupported type")
        motion = scene.get("motion", project.get("motion", {}))
        family = motion.get("family", "static")
        if family not in {"static", "panzoom"}:
            raise ValueError(f"unsupported background motion: {family}")
        progress = max(0, min(1, local_time / max(0.001, scene["duration"])))
        easing = motion.get("easing", "ease-in-out")
        if easing not in {"linear", "ease-in-out", "constant"}:
            raise ValueError("unsupported native motion easing")
        progress = _ease(progress) if easing == "ease-in-out" else 0 if easing == "constant" else progress
        amplitude = _number(motion.get("panzoom", 0), "panzoom", -.25, .25) if family == "panzoom" else 0
        ratio = _number(motion.get("scale_ratio", 1+amplitude), "scale ratio", .8, 1.25) if family == "panzoom" else 1
        start_zoom, end_zoom = max(1, 1/ratio), max(1, ratio)
        frame = _cover(frame, width, height, start_zoom + (end_zoom-start_zoom)*progress)
    else:
        frame = Image.new("RGB", (width, height), tuple(_color(scene.get("background"), [17, 24, 39])[:3]))
    return _caption(frame, scene, local_time, project.get("style", {}), _local(root, project["font"]["path"]))


def _frame_at(project, root, seconds, readers):
    scenes = project["scenes"]
    index = max(i for i, scene in enumerate(scenes) if scene["start"] <= seconds + 1e-9)
    scene = scenes[index]
    local = seconds - scene["start"]
    visible = _visual(scene, local, project, root, readers)
    active_ids = {scene["id"]}
    transition = scene.get("transition", {})
    duration = transition.get("duration", 0)
    if index and duration > 0 and local < duration:
        previous = scenes[index - 1]
        active_ids.add(previous["id"])
        outgoing = _visual(previous, seconds - previous["start"], project, root, readers)
        phase = min(1.0, max(0.0, local / duration))
        family = transition.get("family", "cut")
        if family == "dissolve":
            visible = Image.blend(outgoing, visible, phase)
        elif family == "fade":
            black = Image.new("RGB", visible.size)
            visible = Image.blend(outgoing, black, phase * 2) if phase < 0.5 else Image.blend(black, visible, (phase - 0.5) * 2)
        elif family == "wipe":
            split = round(visible.width * phase)
            outgoing.paste(visible.crop((0, 0, split, visible.height)), (0, 0))
            visible = outgoing
    for scene_id in list(readers):
        if scene_id not in active_ids:
            reader = readers.pop(scene_id)
            if isinstance(reader, _Footage):
                reader.close()
    return visible


def _pipe_frame(process, payload, deadline):
    remaining = memoryview(payload)
    descriptor = process.stdin.fileno()
    while remaining:
        if time.monotonic() > deadline:
            raise RuntimeError("render deadline exceeded")
        if process.poll() is not None:
            raise RuntimeError("FFmpeg encoder stopped before the frame stream ended")
        _, ready, _ = select.select([], [descriptor], [], min(0.25, max(0.001, deadline - time.monotonic())))
        if ready:
            try:
                written = os.write(descriptor, remaining)
                remaining = remaining[written:]
            except BlockingIOError:
                continue


def render(project_path: Path | str, output: Path | str | None = None, *, timeout_seconds: float = 3600) -> dict:
    """Encode a content-bound project and return measured media receipts.

    Raises on changed/missing assets, unsupported layouts or glyphs, encoder
    failure and deadlines. The final output is atomically replaced only after
    encoding/muxing and ffprobe validation succeed.
    """
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe are required for native rendering")
    timeout_seconds = _number(timeout_seconds, "timeout_seconds", 0.01, 86400)
    project, root, project_file = _load_project(project_path)
    destination = Path(output).resolve() if output is not None else root / "render.mp4"
    if destination.suffix.lower() != ".mp4":
        raise ValueError("native v1 renderer outputs MP4 only")
    asset_paths = {_local(root, a["path"]) for a in project.get("assets", [])}
    receipt_path = destination.with_suffix(".receipt.json")
    if destination in asset_paths or destination == project_file or receipt_path in asset_paths or receipt_path == project_file:
        raise ValueError("render output cannot overwrite a project input")
    destination.parent.mkdir(parents=True, exist_ok=True)
    settings = project["render"]
    width, height = settings["width"], settings["height"]
    fps = settings["fps"]
    frame_count = settings["frame_count"]
    duration = frame_count / fps
    deadline = time.monotonic() + timeout_seconds
    started = time.monotonic()
    readers = {}
    process = None
    with tempfile.TemporaryDirectory(prefix=".rvpm-render-", dir=destination.parent) as temp:
        temp = Path(temp)
        video = temp / "video.mp4"
        log_path = temp / "encoder.log"
        try:
            with log_path.open("wb") as log:
                process = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-threads", "2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", str(video)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
                os.set_blocking(process.stdin.fileno(), False)
                for number in range(frame_count):
                    if time.monotonic() > deadline:
                        raise RuntimeError("render deadline exceeded")
                    frame = _frame_at(project, root, number / fps, readers)
                    _pipe_frame(process, frame.tobytes(), deadline)
                process.stdin.close()
                try:
                    status = process.wait(timeout=max(0.01, deadline - time.monotonic()))
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("encoder completion deadline exceeded") from exc
                if status != 0:
                    raise RuntimeError("FFmpeg encode failed: " + log_path.read_text(errors="replace")[-2000:])
            final = video
            if project.get("audio"):
                audio = project["audio"]
                source = _local(root, audio["path"])
                offset = audio.get("offset", 0)
                if offset >= 0:
                    chain = f"[1:a]adelay={round(offset * 1000)}:all=1,apad,atrim=duration={duration:.9f},asetpts=PTS-STARTPTS[a]"
                else:
                    chain = f"[1:a]atrim=start={-offset:.9f},asetpts=PTS-STARTPTS,apad,atrim=duration={duration:.9f}[a]"
                final = temp / "muxed.mp4"
                try:
                    mux = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(video), "-protocol_whitelist", "file,pipe", "-format_whitelist", AUDIO_DEMUXERS, "-i", str(source), "-filter_complex", chain, "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{duration:.9f}", "-movflags", "+faststart", "-y", str(final)], capture_output=True, timeout=max(0.01, deadline - time.monotonic()))
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("audio mux deadline exceeded") from exc
                if mux.returncode:
                    raise RuntimeError("audio mux failed: " + mux.stderr.decode(errors="replace")[-2000:])
            try:
                probe = subprocess.run([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(final)], capture_output=True, text=True, timeout=max(0.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("output validation deadline exceeded") from exc
            if probe.returncode:
                raise RuntimeError("render validation failed: " + probe.stderr[-2000:])
            metadata = json.loads(probe.stdout)
            video_stream = next((s for s in metadata["streams"] if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in metadata["streams"] if s.get("codec_type") == "audio"), None)
            if not video_stream or int(video_stream.get("nb_read_frames", 0)) != frame_count or video_stream.get("width") != width or video_stream.get("height") != height:
                raise RuntimeError("rendered dimensions/frame count differ from the project")
            if project.get("audio") and not audio_stream:
                raise RuntimeError("explicit audio binding is missing from output")
            os.replace(final, destination)
        except (OSError, av.error.FFmpegError) as exc:
            raise RuntimeError(f"native render failed: {exc}") from exc
        finally:
            if process is not None:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
            for reader in readers.values():
                if isinstance(reader, _Footage):
                    reader.close()
    receipt = {
        "schema_version": 1, "kind": "rea-video-render-receipt",
        "path": str(destination), "sha256": _digest(destination), "bytes": destination.stat().st_size,
        "duration": float(video_stream.get("duration", duration)), "frame_count": frame_count,
        "width": width, "height": height, "fps": fps, "audio_present": audio_stream is not None,
        "project_sha256": _digest(project_file), "content_sha256": project.get("content_sha256"), "template_sha256": project.get("template_sha256"),
        "reference_sha256": project.get("reference", {}).get("sha256"),
        "content_assets": [{"path": a["path"], "sha256": a["sha256"], "role": a["role"]} for a in project.get("assets", [])],
        "checks": {"full_video_decode": True, "expected_frame_count": True, "dimensions": True, "explicit_content_bindings": True, "asset_hashes": True},
        "renderer": {"id": "native-pillow-ffmpeg-v1", "shaping": "raqm" if features.check_feature("raqm") else "basic", "output_codec": video_stream.get("codec_name"), "pixel_format": video_stream.get("pix_fmt")},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": project.get("limits", {}),
    }
    _write(receipt_path, receipt)
    return receipt


def render_still(project_path: Path | str, seconds: float, output: Path | str) -> dict:
    """Diagnostic checkpoint of the concrete B timeline, not a reference clone."""
    project, root, _ = _load_project(project_path)
    seconds = _number(seconds, "seconds", 0, project["render"]["duration"])
    seconds = min(seconds, max(0, project["render"]["duration"] - 1e-8))
    readers = {}
    try:
        image = _frame_at(project, root, seconds, readers)
        path = Path(output).resolve()
        if path.suffix.lower() != ".png":
            raise ValueError("diagnostic still output must be PNG")
        if path in {_local(root, a["path"]) for a in project.get("assets", [])}:
            raise ValueError("diagnostic output cannot overwrite a project input")
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        return {"path": str(path), "sha256": _digest(path), "time": seconds, "width": image.width, "height": image.height}
    finally:
        for reader in readers.values():
            if isinstance(reader, _Footage):
                reader.close()
