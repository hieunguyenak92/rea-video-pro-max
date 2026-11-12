"""Pixel-derived text and apparent-motion estimates, with explicit uncertainty.

No origin/model/editor attribution is inferred from appearance. Tesseract scores are
engine scores, not calibrated probabilities. No external model download occurs.
"""
from __future__ import annotations

import csv
import difflib
import io
import math
import shutil
import subprocess
import unicodedata
from collections import defaultdict

import numpy as np
from PIL import Image, ImageFilter


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def bbox_iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    inter = max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(0, min(ay + ah, by + bh) - max(ay, by))
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def _dominant_color(pixels):
    if not len(pixels):
        return [0, 0, 0]
    q = (np.asarray(pixels, dtype=np.uint8).reshape(-1, 3) // 24).astype(np.int16)
    values, counts = np.unique(q, axis=0, return_counts=True)
    color = values[int(np.argmax(counts))]
    mask = np.all(q == color, axis=1)
    return np.median(np.asarray(pixels).reshape(-1, 3)[mask], axis=0).astype(int).tolist()


def measure_text_style(image: Image.Image, pixel_bbox) -> dict:
    """Estimate raster appearance; the family and hidden shadow remain unknown."""
    rgb = np.asarray(image.convert("RGB"))
    height, width = rgb.shape[:2]
    x, y, w, h = [int(v) for v in pixel_bbox]
    x, y = max(0, x), max(0, y)
    w, h = max(1, min(w, width - x)), max(1, min(h, height - y))
    crop = rgb[y:y + h, x:x + w]
    pad = max(3, int(h * .3))
    region_x, region_y = max(0, x-pad), max(0, y-pad)
    region = rgb[region_y:min(height, y+h+pad), region_x:min(width, x+w+pad)]
    ring_mask = np.ones(region.shape[:2], bool)
    ring_mask[y-region_y:y-region_y+h, x-region_x:x-region_x+w] = False
    ring_color = _dominant_color(region[ring_mask] if np.any(ring_mask) else region.reshape(-1, 3))
    q = (crop.reshape(-1, 3) // 24).astype(np.int16)
    colors, counts = np.unique(q, axis=0, return_counts=True)
    scores = []
    for color, count in zip(colors, counts):
        mask = np.all(q == color, axis=1)
        actual = np.median(crop.reshape(-1, 3)[mask], axis=0)
        contrast = np.linalg.norm(actual - np.asarray(ring_color))
        fraction = count / max(1, len(q))
        # Glyph clusters must occupy some area but need not dominate the crop.
        scores.append(contrast * math.sqrt(fraction) if fraction >= .015 else -1)
    fill_index = int(np.argmax(scores))
    fill_q = colors[fill_index]
    fill = np.median(crop.reshape(-1, 3)[np.all(q == fill_q, axis=1)], axis=0).astype(int).tolist()
    distance = np.linalg.norm(crop.astype(float) - np.asarray(fill), axis=2)
    ink = distance < 50
    expanded = np.asarray(Image.fromarray((ink * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))) > 0
    surround = expanded & ~ink
    stroke = _dominant_color(crop[surround]) if np.count_nonzero(surround) > 4 else ring_color
    stroke_background_distance = float(np.linalg.norm(np.asarray(stroke)-np.asarray(ring_color)))
    visible_stroke = np.linalg.norm(np.asarray(stroke) - np.asarray(fill)) > 65 and stroke_background_distance > 6
    stroke_width = 0
    band_support = []
    if visible_stroke:
        region_ink = np.linalg.norm(region.astype(float)-np.asarray(fill), axis=2) < 50
        # Near-black panels still permit a black outline measurement, but a
        # 70-level color radius would mistake the entire panel for the outline.
        stroke_tolerance = min(70, max(4, stroke_background_distance*.35))
        region_stroke = np.linalg.norm(region.astype(float)-np.asarray(stroke), axis=2) < stroke_tolerance
        previous_band = region_ink
        for radius in range(1, min(8, max(2, math.ceil(h*.25)))+1):
            expanded_band = np.asarray(Image.fromarray((previous_band*255).astype("uint8")).filter(ImageFilter.MaxFilter(3))) > 0
            band = expanded_band & ~previous_band
            support = float(np.mean(region_stroke[band])) if np.any(band) else 0.0
            band_support.append(round(support, 4))
            if support >= .25:
                stroke_width = radius
            elif radius > 1:
                break
            previous_band = expanded_band
    cy = (y + h / 2) / height
    return {
        "font_family": "unknown", "font_family_status": "unknown",
        "font_size_ratio": round(h / height * 1.3, 6),
        "font_size_method": "glyph-height approximate; original font metrics unavailable",
        "fill": fill, "stroke": stroke,
        "stroke_width_ratio": round(stroke_width / height, 6),
        "stroke_width_status": "estimated" if visible_stroke else "unknown",
        "stroke_width_method": "morphological-ink-neighbor-bands", "stroke_band_support": band_support, "box_color": None,
        "stroke_background_color_distance": round(stroke_background_distance, 4),
        "anchor": "bottom" if cy > .65 else "top" if cy < .35 else "center",
        "position": [round((x+w/2)/width, 6), round(cy, 6)],
        "line_height_ratio": round(h / height, 6),
        "animation": "static", "shadow": {"status": "unknown"},
        "status": "estimated", "method": "quantized-raster-contrast-and-neighbor-ring",
        "limitations": ["font-size/stroke are approximate", "compressed pixels do not identify original font", "shadow and plate are not reliably separated"],
    }


def ocr_capabilities(lang="eng") -> dict:
    binary = shutil.which("tesseract")
    if not binary:
        return {"available": False, "reason": "tesseract executable not found", "languages": []}
    try:
        result = subprocess.run([binary, "--list-langs"], text=True, capture_output=True, timeout=10, check=False)
        languages = [x.strip() for x in result.stdout.splitlines()[1:] if x.strip()]
        requested = lang.split("+")
        missing = [x for x in requested if x not in languages]
        return {"available": result.returncode == 0 and not missing, "executable": binary,
                "languages": languages, "requested": requested, "reason": f"missing OCR languages: {', '.join(missing)}" if missing else None}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "reason": str(exc), "languages": []}


def detect_text(image: Image.Image, lang="eng", timeout=20, *, psm=11) -> list[dict]:
    binary = shutil.which("tesseract")
    if binary is None:
        raise RuntimeError("tesseract is unavailable")
    image = image.convert("RGB")
    original_width, original_height = image.size
    scale = min(1.0, 1280 / max(image.size))
    scaled = image.resize((max(1, round(original_width * scale)), max(1, round(original_height * scale)))) if scale < 1 else image
    payload = io.BytesIO()
    scaled.save(payload, format="PNG")
    if psm not in {6, 7, 11}:
        raise ValueError("unsupported OCR segmentation mode")
    result = subprocess.run([binary, "stdin", "stdout", "-l", lang, "--psm", str(psm), "tsv"], input=payload.getvalue(), capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError("Tesseract failed: " + result.stderr.decode("utf-8", "replace")[:500])
    if len(result.stdout) > 4 * 1024 * 1024:
        raise RuntimeError("Tesseract output exceeded 4 MiB budget")
    lines = defaultdict(list)
    for row in csv.DictReader(io.StringIO(result.stdout.decode("utf-8", "replace")), delimiter="\t"):
        text = normalize_text(row.get("text", ""))
        try:
            conf = float(row["conf"])
            box = tuple(int(row[k]) / scale for k in ("left", "top", "width", "height"))
        except (KeyError, ValueError):
            continue
        if not text or conf < 35 or box[2] < 2 or box[3] < 2:
            continue
        key = tuple(row.get(k) for k in ("page_num", "block_num", "par_num", "line_num"))
        lines[key].append({"text": text, "confidence": conf, "box": box})
    found = []
    for words in lines.values():
        words.sort(key=lambda w: w["box"][0])
        # Some Tesseract sparse-mode word boxes cover the entire line when a
        # word is colored. Bound them by the next word before measuring fill,
        # then fit visible glyph pixels so color does not masquerade as scale.
        for index, word in enumerate(words):
            x, y, w, h = word["box"]
            if index+1 < len(words):
                w = max(1, min(w, words[index+1]["box"][0]-x))
            word["box"] = (x, y, w, h)
            word_style = measure_text_style(image, word["box"])
            left, top = max(0, round(x)), max(0, round(y))
            right, bottom = min(image.width, round(x+w)), min(image.height, round(y+h))
            crop = np.asarray(image.crop((left, top, right, bottom)), float)
            mask = np.linalg.norm(crop-np.asarray(word_style["fill"]), axis=2) < 50
            if mask.size and .015 < np.mean(mask) < .8:
                rows, columns = np.where(mask)
                word["box"] = (left+int(columns.min()), top+int(rows.min()), int(columns.max()-columns.min()+1), int(rows.max()-rows.min()+1))
            word["fill"] = word_style["fill"]
        x = min(w["box"][0] for w in words)
        y = min(w["box"][1] for w in words)
        right = max(w["box"][0] + w["box"][2] for w in words)
        bottom = max(w["box"][1] + w["box"][3] for w in words)
        pixel_box = [x, y, right-x, bottom-y]
        style = measure_text_style(image, pixel_box)
        found.append({
            "text": normalize_text(" ".join(w["text"] for w in words)),
            "bbox": [round(x/original_width, 6), round(y/original_height, 6), round((right-x)/original_width, 6), round((bottom-y)/original_height, 6)],
            "style": style,
            "words": [{"text": w["text"], "bbox": [round(w["box"][0]/original_width, 6), round(w["box"][1]/original_height, 6), round(w["box"][2]/original_width, 6), round(w["box"][3]/original_height, 6)], "engine_score": w["confidence"],
                       "fill": w["fill"], "appearance_status": "estimated"} for w in words],
            "engine_score": sum(w["confidence"] for w in words) / len(words),
            "score_semantics": "Tesseract confidence score; not calibrated probability",
            "role": "caption_candidate" if style["position"][1] > .55 else "title_or_scene_text",
            "status": "model-derived", "method": f"tesseract-tsv-psm{psm}",
        })
    return found


class TextTracker:
    def __init__(self, sample_interval=.25, max_tracks=1000):
        self.interval = sample_interval
        self.tracks = []
        self.sample_index = -1
        self.last_update_time = 0.0
        self.max_tracks = max_tracks
        self.omitted_observations = 0

    def update(self, observations, t, evidence, shot_id=None):
        self.sample_index += 1
        used = set()
        for obs in observations:
            best = None
            best_score = .59
            for track in self.tracks:
                if track["id"] in used or t-track["last_seen"] > self.interval * 2.2:
                    continue
                if track.get("last_sample_index") != self.sample_index - 1:
                    continue
                if shot_id and track.get("shot_id") and shot_id != track["shot_id"]:
                    continue
                similarity = difflib.SequenceMatcher(None, track["text"].casefold(), obs["text"].casefold()).ratio()
                prefix = track["text"].casefold().startswith(obs["text"].casefold()) or obs["text"].casefold().startswith(track["text"].casefold())
                overlap = bbox_iou(track["bbox"], obs["bbox"])
                score = similarity * .75 + overlap * .25
                if (similarity >= .65 or prefix) and overlap > .12 and score > best_score:
                    best, best_score = track, score
            if best is None:
                if len(self.tracks) >= self.max_tracks:
                    self.omitted_observations += 1
                    continue
                best = {**obs, "style": dict(obs["style"]), "id": f"text-{len(self.tracks)+1:04d}", "start": t, "end": t+self.interval,
                        "first_seen": t, "last_seen": t, "shot_id": shot_id,
                        "onset_lower": self.last_update_time,
                        "observations": [], "evidence": [], "text_alternatives": {}}
                self.tracks.append(best)
            best["last_seen"] = t
            best["last_sample_index"] = self.sample_index
            best["end"] = t+self.interval
            best["observations"].append({"time": t, "bbox": obs["bbox"], "text": obs["text"], "fill": obs["style"]["fill"],
                                         "style": dict(obs["style"]), "word_appearances": obs.get("words", []), "evidence": evidence})
            best["evidence"].append(evidence)
            best["text_alternatives"][obs["text"]] = best["text_alternatives"].get(obs["text"], 0) + 1
            # Prefer a stable longer reading when a progressive reveal is observed.
            best["text"] = max(best["text_alternatives"], key=lambda x: (best["text_alternatives"][x], len(x)))
            best["words"] = obs["words"]
            used.add(best["id"])
        for track in self.tracks:
            if track["id"] not in used and track.get("last_sample_index") == self.sample_index-1:
                track["first_missing"] = t
                track["end"] = t
        self.last_update_time = t

    def finish(self, duration):
        for track in self.tracks:
            if "first_missing" not in track and duration-track["last_seen"] <= self.interval*2.2:
                track["end"] = duration
            track["end"] = min(duration, track["end"])
            track["timing"] = {"status": "estimated", "method": "sampled-visible-text-track",
                               "onset_interval": [max(0, track["onset_lower"]), track["start"]],
                               "offset_interval": [track["last_seen"], track["end"]],
                               "sample_interval": self.interval}
            observations = track["observations"]
            representative_pool = [row for row in observations if row["text"] == track["text"]] or observations
            representative = sorted(representative_pool, key=lambda row: row["bbox"][2]*row["bbox"][3])[len(representative_pool)//2]
            track["bbox"] = representative["bbox"]
            track["style"] = dict(representative["style"])
            track["words"] = representative.get("word_appearances", [])
            track["appearance_evidence"] = representative["evidence"]
            if len(observations) >= 2:
                heights = [x["bbox"][3] for x in observations]
                if max(heights) > min(heights) * 1.18:
                    track["style"]["animation"] = "scale_candidate"
                    track["style"]["animation_status"] = "inferred"
                colors = [tuple(x["fill"]) for x in observations]
                if any(np.linalg.norm(np.asarray(x)-np.asarray(colors[0])) > 65 for x in colors[1:]):
                    track["highlight"] = {"status": "candidate", "method": "temporal-fill-change", "limitations": "color change is not proof of word-level karaoke"}
                centers = np.array([[row["bbox"][0]+row["bbox"][2]/2, row["bbox"][1]+row["bbox"][3]/2] for row in observations])
                displacement = (centers[-1]-centers[0]).tolist()
                if np.max(np.linalg.norm(centers-centers[0], axis=1)) > .01 or max(heights) > min(heights)*1.12:
                    track["geometry_change"] = {"status": "model-derived", "method": "sampled-text-box-track", "center_displacement": displacement,
                                                "height_ratio_range": [round(min(heights)/heights[0], 5), round(max(heights)/heights[0], 5)],
                                                "evidence": track["evidence"], "limits": "OCR boxes reflect glyph visibility and detector variation as well as motion"}
                changes = []
                for previous, current in zip(observations, observations[1:]):
                    for index, (before, after) in enumerate(zip(previous.get("word_appearances", []), current.get("word_appearances", []))):
                        if normalize_text(before["text"]).casefold() != normalize_text(after["text"]).casefold():
                            continue
                        if "fill" not in before or "fill" not in after:
                            continue
                        if np.linalg.norm(np.asarray(before["fill"])-np.asarray(after["fill"])) > 65:
                            changes.append({"word_index": index, "text": after["text"], "start": current["time"], "previous_observation": previous["time"],
                                            "onset_interval": [previous["time"], current["time"]], "time_semantics": "first sampled changed appearance",
                                            "fill": after["fill"], "previous_fill": before["fill"], "bbox": after["bbox"],
                                            "evidence": [previous["evidence"], current["evidence"]], "status": "model-derived",
                                            "method": "sampled-word-raster-color-change", "limits": "appearance change, not a verified speech-aligned word timestamp"})
                if changes:
                    track["word_highlights"] = changes
                    fills = [word["fill"] for row in observations for word in row.get("word_appearances", []) if "fill" in word]
                    if fills:
                        baseline = _dominant_color(np.asarray(fills, dtype=np.uint8))
                        palette_groups = defaultdict(list)
                        for row in observations:
                            for word_index, word in enumerate(row.get("word_appearances", [])):
                                if "fill" in word and np.linalg.norm(np.asarray(word["fill"])-np.asarray(baseline)) > 65:
                                    palette_groups[tuple(channel//24 for channel in word["fill"])].append((row, word_index, word["fill"]))
                        palette = []
                        for entries in palette_groups.values():
                            if len(entries) < 2:
                                continue
                            palette.append({"fill": np.median([entry[2] for entry in entries], axis=0).astype(int).tolist(),
                                            "observed_range": [entries[0][0]["time"], entries[-1][0]["time"]],
                                            "word_indices": sorted({entry[1] for entry in entries}),
                                            "evidence": list(dict.fromkeys(entry[0]["evidence"] for entry in entries)), "observations": len(entries)})
                        if palette:
                            primary = max(palette, key=lambda entry: entry["observations"])
                            progressive = len({change["word_index"] for change in changes}) > 1
                            track["style"].update({"highlight": primary["fill"], "highlight_mode": "word-progress-candidate" if progressive else "word-color-change-candidate",
                                                   "highlight_status": "inferred", "highlight_palette": palette,
                                                   "highlight_method": "sampled-word-color-progression", "highlight_base_fill": baseline,
                                                   "highlight_limits": "observed color regime; new content needs newly scheduled words, not copied reference timestamps"})
            if len(observations) > 80:
                track["observations"] = observations[::math.ceil(len(observations)/80)]
        return [x for x in self.tracks if x["end"] > x["start"]]


def phase_translation(previous: np.ndarray, current: np.ndarray) -> dict:
    """Coarse apparent translation. Low texture and ambiguous peaks abstain."""
    a = np.asarray(previous, float)
    b = np.asarray(current, float)
    if a.ndim == 3:
        a, b = a.mean(axis=2), b.mean(axis=2)
    if a.std() < 2 or b.std() < 2:
        return {"status": "unknown", "reason": "insufficient texture"}
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa = np.fft.rfft2((a-a.mean()) * window)
    fb = np.fft.rfft2((b-b.mean()) * window)
    cross = fb * np.conj(fa)
    cross /= np.maximum(np.abs(cross), 1e-12)
    corr = np.fft.irfft2(cross, s=a.shape)
    y, x = np.unravel_index(np.argmax(corr), corr.shape)
    peak = float(corr[y, x])
    if peak < .06:
        return {"status": "unknown", "reason": "ambiguous correlation peak", "peak": round(peak, 5)}
    if y > a.shape[0] / 2:
        y -= a.shape[0]
    if x > a.shape[1] / 2:
        x -= a.shape[1]
    return {"status": "estimated", "dx": round(float(x/a.shape[1]), 6), "dy": round(float(y/a.shape[0]), 6),
            "peak": round(peak, 6), "method": "windowed-phase-correlation", "limits": "apparent global translation; camera/object/scale not disambiguated"}


def fit_motion(points: list[dict]) -> dict:
    valid = [x for x in points if x.get("status") == "estimated"]
    if len(valid) < 2:
        return {"status": "unknown", "reason": "insufficient reliable motion samples", "points": points}
    times = np.array([x["time"] for x in valid], float)
    xy = np.cumsum([[x["dx"], x["dy"]] for x in valid], axis=0)
    times -= times[0]
    axis = 0 if np.ptp(xy[:, 0]) >= np.ptp(xy[:, 1]) else 1
    values = xy[:, axis]
    coeff = np.polyfit(times, values, 1) if np.ptp(times) else [0, float(values.mean())]
    residual = float(np.sqrt(np.mean((np.polyval(coeff, times)-values)**2)))
    displacement = [float(x) for x in (xy[-1]-xy[0])]
    return {"status": "estimated", "method": "phase-translation-linear-fit", "family": "linear_translation_candidate",
            "direction": "right" if displacement[0] > .01 else "left" if displacement[0] < -.01 else "down" if displacement[1] > .01 else "up" if displacement[1] < -.01 else "static",
            "displacement": [round(x, 6) for x in displacement], "velocity": round(float(coeff[0]), 6),
            "residual_normalized": round(residual, 6), "points": points,
            "unknowns": ["original keyframes", "camera vs foreground", "zoom and perspective"]}


def font_candidates(image: Image.Image, bbox, text: str, font_dir, *, words=None) -> list[dict]:
    """Closed-catalog raster fitting. Never identifies an unavailable original font."""
    from pathlib import Path
    import hashlib
    from PIL import ImageDraw, ImageFont

    width, height = image.size
    x, y, w, h = [round(bbox[0]*width), round(bbox[1]*height), max(1, round(bbox[2]*width)), max(1, round(bbox[3]*height))]
    crop = image.crop((x, y, x+w, y+h)).convert("RGB")
    style = measure_text_style(image, (x, y, w, h))
    crop_array = np.asarray(crop, float)
    observed = np.linalg.norm(crop_array-np.asarray(style["fill"]), axis=2) < 55
    # Active-word colors are part of the same glyph geometry. Omitting them
    # biases a white-only template fit and can incorrectly enlarge the font.
    for word in words or []:
        if "fill" not in word:
            continue
        wx, wy, ww, wh = word["bbox"]
        left, top = max(0, round(wx*width)-x), max(0, round(wy*height)-y)
        right, bottom = min(w, round((wx+ww)*width)-x), min(h, round((wy+wh)*height)-y)
        if right > left and bottom > top:
            observed[top:bottom, left:right] |= np.linalg.norm(crop_array[top:bottom, left:right]-np.asarray(word["fill"]), axis=2) < 55
    # Keep the actual glyph aspect, rather than stretching candidates to fit.
    target = np.asarray(Image.fromarray((observed*255).astype("uint8")).resize((128, 48))) > 100
    candidates = []
    for path in sorted(Path(font_dir).glob("*.ttf"))[:12]:
        best = None
        reference = ImageFont.truetype(str(path), size=100)
        reference_box = reference.getbbox(text)
        # Glyph height is script/content dependent: accented text can be taller
        # than the em size. Search around measured width AND height instead of
        # assuming every glyph occupies a fixed fraction of its original em.
        width_size = 100*w/max(1, reference_box[2]-reference_box[0])
        sizes = {max(8, min(512, round(width_size*factor))) for factor in np.linspace(.75, 1.25, 13)}
        sizes.update(max(8, min(512, round(h*factor))) for factor in (.65, .8, .95, 1.1, 1.3, 1.5))
        for size in sorted(sizes):
            font = ImageFont.truetype(str(path), size=size)
            box = font.getbbox(text)
            glyph_w, glyph_h = max(1, box[2]-box[0]), max(1, box[3]-box[1])
            canvas = Image.new("L", (max(w, glyph_w), max(h, glyph_h)), 0)
            draw = ImageDraw.Draw(canvas)
            draw.text(((w-glyph_w)/2-box[0], (h-glyph_h)/2-box[1]), text, font=font, fill=255)
            normalized = np.asarray(canvas.crop((0, 0, w, h)).resize((128, 48))) > 100
            union = np.count_nonzero(normalized | target)
            iou = np.count_nonzero(normalized & target)/union if union else 0
            width_error = abs(glyph_w-w)/max(1, w)
            height_error = abs(glyph_h-h)/max(1, h)
            geometry = width_error + height_error
            score = float(iou - .30*width_error - .10*height_error)
            item = {"family": font.getname()[0], "face": font.getname()[1], "font_file": path.name,
                    "font_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_px": size,
                    "glyph_iou": round(float(iou), 5), "geometry_relative_error": round(geometry, 5), "fit_score": round(score, 5),
                    "width_relative_error": round(width_error, 5), "height_relative_error": round(height_error, 5),
                    "size_semantics": "compatible catalog rendering size fitted to observed glyph geometry; not the unknown original font em size",
                    "status": "candidate", "catalog_scope": "bundled OFL fonts only; original may not be present"}
            if best is None or score > best["fit_score"]:
                best = item
        if best is not None:
            candidates.append(best)
    return sorted(candidates, key=lambda x: x["fit_score"], reverse=True)[:3]
