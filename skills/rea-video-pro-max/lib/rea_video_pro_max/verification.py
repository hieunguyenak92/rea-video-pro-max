"""Independent decode/identity checks; analysis quality requires annotated truth."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import av
from PIL import Image

from .core import read_json, sha256, validate

MEDIA_OPTIONS = {"protocol_whitelist": "file,pipe", "format_whitelist": "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,avi"}


def _words(text):
    text = unicodedata.normalize("NFC", text).casefold()
    return re.findall(r"[^\W_]+", text, re.UNICODE)


def decode_media(path: str | Path) -> dict:
    """Decode every video/audio packet; do not mistake ffprobe metadata for playback."""
    count = samples = 0
    times = []
    widths, heights = set(), set()
    with av.open(str(path), options=MEDIA_OPTIONS) as container:
        for packet in container.demux():
            for frame in packet.decode():
                if isinstance(frame, av.VideoFrame):
                    count += 1
                    widths.add(frame.width)
                    heights.add(frame.height)
                    if frame.pts is None:
                        raise ValueError("Rendered frame lacks PTS")
                    times.append(float(frame.pts * frame.time_base))
                elif isinstance(frame, av.AudioFrame):
                    samples += frame.samples
        rate = float(container.streams.video[0].average_rate or 0) if container.streams.video else 0
    if not count or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("No decoded video or non-monotonic presentation time")
    return {"frames_decoded": count, "audio_samples_decoded": samples,
            "widths": sorted(widths), "heights": sorted(heights), "fps": rate,
            "first_pts_seconds": times[0], "last_pts_seconds": times[-1],
            "duration_seconds": times[-1] - times[0] + (1 / rate if rate else 0)}


def _ocr_cues(project, media, language):
    binary = shutil.which("tesseract")
    if not binary:
        return {"status": "not-run", "reason": "Tesseract is unavailable"}
    cues = project.get("captions", [])
    # Bound work; every scene is still represented for ordinary short projects.
    cues = cues[:64]
    if not cues:
        return {"status": "not-applicable", "reason": "No captions requested"}
    targets = sorted([(c["start"] + (c["end"]-c["start"])*.65, c) for c in cues], key=lambda x: x[0])
    checks, index = [], 0
    with tempfile.TemporaryDirectory(prefix="rea-ocr-check-") as directory, av.open(str(media), options=MEDIA_OPTIONS) as video:
        for frame in video.decode(video=0):
            t = float(frame.pts * frame.time_base)
            while index < len(targets) and t >= targets[index][0]:
                _, cue = targets[index]
                image = frame.to_image()
                # Expected anchor geometry defines a crop; OCR supplies the text observation.
                anchor = {**project.get("style", {}), **cue.get("style", {})}.get("anchor_y", .82)
                y0, y1 = max(0, int(image.height * (anchor-.25))), min(image.height, int(image.height*(anchor+.25)))
                crop = image.crop((0, y0, image.width, max(y0+1, y1)))
                crop = crop.resize((crop.width*2, crop.height*2), Image.Resampling.LANCZOS)
                path = Path(directory) / "caption.png"
                crop.save(path)
                result = subprocess.run([binary, str(path), "stdout", "-l", language, "--psm", "6"],
                                        capture_output=True, text=True, timeout=30, check=False)
                expected, observed = _words(cue["text"]), _words(result.stdout)
                passed = result.returncode == 0 and bool(expected) and any(observed[i:i+len(expected)] == expected for i in range(len(observed)-len(expected)+1))
                checks.append({"cue_id": cue["id"], "sample_seconds": t,
                               "expected": cue["text"], "observed": result.stdout.strip(),
                               "passed": passed, "method": "tesseract-native-render-caption-crop"})
                index += 1
            if index == len(targets):
                break
    return {"status": "passed" if index == len(targets) and all(c["passed"] for c in checks) else "failed",
            "cues_checked": len(checks), "cues_total": len(project.get("captions", [])),
            "coverage": "first 64 cue interiors; static frame per cue; not animation/highlight quality certification",
            "language": language, "checks": checks}


def verify(artifact: str | Path, *, mode: str = "analysis", render_path: str | Path | None = None,
           ocr_lang: str | None = None) -> dict:
    path = Path(artifact).resolve()
    if path.is_dir():
        path /= "project.json" if mode == "style-transfer" else "analysis.json"
    value = read_json(path)
    checks = []
    limits = []
    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    if mode == "analysis":
        validate(value, "rea-video-analysis")
        source = Path(value["source"]["path"])
        check("source-identity", source.is_file() and sha256(source) == value["source"]["sha256"],
              "Original bytes match the recorded SHA-256")
        check("coverage-present", bool(value.get("coverage")), value.get("coverage", {}))
        missing = []
        # File references, unlike PTS IDs, must resolve inside the analysis directory.
        for file in value.get("evidence", []):
            if isinstance(file, dict) and file.get("path"):
                target = (path.parent / file["path"]).resolve()
                if not target.is_relative_to(path.parent) or not target.is_file():
                    missing.append(file["path"])
        check("evidence-files", not missing, {"missing": missing})
        limits.append("Integrity/structure checks do not certify OCR, cuts, motion or original editing history. Annotated independent fixtures are required.")
    elif mode == "style-transfer":
        from .render import _load_project
        loaded = _load_project(path)
        project = loaded[0] if isinstance(loaded, tuple) else loaded
        # Loader validates actual relative asset bytes, caption/scene ranges and render budgets.
        check("portable-project", True, "Manifest hashes, fonts, scene coverage and frame budgets validated")
        provenance = project.get("provenance", {})
        check("explicit-new-content", provenance.get("content") == "explicit-new-content-bindings", provenance)
        reused = provenance.get("reference_media_reused", False)
        check("reference-reuse-policy", not reused or provenance.get("reference_reuse_authorized"), provenance)
        if render_path is None:
            check("render-present", False, "Supply --render to verify an actual new video")
        else:
            rendered = Path(render_path).resolve()
            receipt_path = rendered.with_suffix(".receipt.json")
            if receipt_path.is_symlink():
                raise ValueError("Render receipt symlinks are not accepted")
            receipt = read_json(receipt_path) if receipt_path.is_file() else {}
            check("render-project-identity", receipt.get("project_sha256") == sha256(path) and receipt.get("sha256") == sha256(rendered),
                  "Render receipt binds the exact output bytes to this project revision")
            decoded = decode_media(render_path)
            settings = project["render"]
            check("decoded-frame-count", decoded["frames_decoded"] == settings["frame_count"], decoded)
            check("render-geometry", decoded["widths"] == [settings["width"]] and decoded["heights"] == [settings["height"]], decoded)
            check("render-clock", abs(decoded["fps"]-settings["fps"]) < .002 and abs(decoded["duration_seconds"]-settings["duration"]) <= 1/settings["fps"]+.002, decoded)
            check("bound-audio", not project.get("audio") or decoded["audio_samples_decoded"] > 0, decoded)
            if ocr_lang:
                ocr = _ocr_cues(project, render_path, ocr_lang)
                check("observed-caption-content", ocr["status"] in {"passed", "not-applicable"}, ocr)
            else:
                check("observed-caption-content", not project.get("captions"), "Caption content needs independent observation; supply --ocr-lang or review output manually")
                limits.append("Rendered caption content was not OCR-checked; request --ocr-lang for sampled independent text checks.")
        limits.append("Decode and project checks do not certify perceived style quality, transition/motion recovery or speech alignment. Review frame evidence and fixture metrics.")
    elif mode == "export":
        if value.get("kind") != "rea-video-export-receipt":
            raise ValueError("Export mode expects an export receipt JSON")
        name = value.get("file")
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError("Export receipt file must be a single local filename")
        exported = (path.parent / name).resolve()
        if not exported.is_relative_to(path.parent):
            raise ValueError("Export file escapes receipt directory")
        check("export-file", exported.is_file() and exported.stat().st_size > 0, str(exported))
        check("export-identity", exported.is_file() and sha256(exported) == value.get("sha256"), "File bytes match the export receipt")
        check("loss-receipt", isinstance(value.get("losses"), list), value.get("losses"))
        limits.append("File presence and loss metadata do not certify import into a specific editing application.")
    else:
        raise ValueError("mode must be analysis, style-transfer or export")
    return {"schema_version": 1, "kind": "rea-video-verification", "mode": mode,
            "status": "passed" if all(c["passed"] for c in checks) else "failed",
            "checks": checks, "limits": limits}
