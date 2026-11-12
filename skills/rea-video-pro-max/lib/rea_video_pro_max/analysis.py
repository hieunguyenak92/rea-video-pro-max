"""Reference-video analysis: measured signals, inferred edit timeline and evidence.

The source is never edited. Native timeline references denote flattened-video
slices, not recovered original footage or separated layers. Semantic origin,
font identities outside the supplied catalog and hidden assets remain unknown.
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from fractions import Fraction
from collections import Counter

import av
import numpy as np
from PIL import Image, ImageOps

from .audio import analyze_audio
from .perception import TextTracker, detect_text, fit_motion, font_candidates, ocr_capabilities, phase_translation

MAX_PIXELS = 16_000_000
MAX_EVIDENCE = 600
MAX_FRAMES = 1_000_000
MAX_SOURCE_BYTES = 8 * 1024**3
MAX_JSON_OUTPUT = 16 * 1024**1024
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
LOCAL_MEDIA_FORMATS = "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,avi,mpeg,mpegts,ogg,flv,gif,apng,asf,mxf,nut,wav,mp3,flac,aac,aiff,ac3,au"


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if len(raw.encode("utf-8")) > MAX_JSON_OUTPUT:
        raise ValueError(f"{path.name} exceeds the 16 MiB JSON artifact budget; lower sample_fps/max_seconds or use analysis-only evidence files")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
        file.write(raw)
        temp = Path(file.name)
    os.replace(temp, path)


def _digest(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rational(value):
    return {"num": int(value.numerator), "den": int(value.denominator)} if value is not None else None


def _presentation_clock(frames, nominal_rate):
    try:
        rate = Fraction(str(nominal_rate))
        nominal = 1/rate if rate > 0 else None
    except (ValueError, ZeroDivisionError):
        nominal = None
    counts = Counter()
    missing = 0
    variable, quantized = False, False
    largest_deviation = Fraction(0)
    largest_tolerance = Fraction(0)
    previous = None
    for row in frames:
        base = row.get("time_base")
        if row.get("pts") is None or not base:
            missing += 1
            previous = None
            continue
        tick = Fraction(base["num"], base["den"])
        absolute = row["pts"]*tick
        if previous is not None:
            interval = absolute-previous[0]
            counts[interval] += 1
            tolerance = max(tick, previous[1])
            largest_tolerance = max(largest_tolerance, tolerance)
            if nominal is not None:
                deviation = abs(interval-nominal)
                largest_deviation = max(largest_deviation, deviation)
                variable |= deviation > tolerance
                quantized |= deviation > 0
        previous = absolute, tick
    sufficient = sum(counts.values()) >= 2 and not missing and nominal is not None
    exact_values = sorted(counts)
    return {"status": "measured" if sufficient else "unknown", "method": "exact-rational-decoded-PTS-differences",
            "nominal_frame_interval": _rational(nominal), "observed_interval_count": sum(counts.values()),
            "observed_intervals": [{**_rational(value), "seconds": float(value), "count": counts[value]} for value in exact_values[:128]],
            "interval_values_omitted": max(0, len(exact_values)-128), "variable_intervals": bool(variable) if sufficient else None,
            "quantization_jitter_within_tolerance": bool(quantized and not variable) if sufficient else None,
            "jitter_tolerance": _rational(largest_tolerance), "max_nominal_deviation": _rational(largest_deviation),
            "missing_pts": missing, "limits": "CFR consistency is checked only across analyzed decoded frames; tolerance is one source time-base tick per adjacent pair"}


def _probe(source: Path):
    binary = shutil.which("ffprobe")
    if not binary:
        raise RuntimeError("ffprobe is required for media stream admission")
    result = subprocess.run([binary, "-v", "error", "-protocol_whitelist", "file,pipe", "-format_whitelist", LOCAL_MEDIA_FORMATS,
                             "-show_streams", "-show_format", "-of", "json", str(source)], capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise ValueError("media probe failed: " + result.stderr.decode("utf-8", "replace")[:400])
    if len(result.stdout) > 4*1024*1024:
        raise ValueError("media metadata exceeds 4 MiB limit")
    return json.loads(result.stdout)


def _fraction(value, fallback=0.0):
    try:
        if isinstance(value, str) and "/" in value:
            num, den = value.split("/", 1)
            return float(num)/float(den)
        return float(value)
    except (ValueError, TypeError, ZeroDivisionError):
        return fallback


def _display(image: Image.Image, sar=1.0, rotation=0.0):
    if sar != 1:
        image = image.resize((max(1, round(image.width*sar)), image.height), Image.Resampling.BICUBIC)
    if rotation:
        image = image.rotate(rotation, expand=True)
    return image


def _thumbnail(image):
    # A fixed display-space descriptor; not used as full-resolution evidence.
    return np.asarray(image.convert("RGB").resize((96, 54)), dtype=np.uint8)


def _histogram(array):
    result = []
    for channel in range(3):
        result.extend(np.histogram(array[:, :, channel], bins=16, range=(0, 256))[0] / array.shape[0] / array.shape[1])
    return np.asarray(result)


def _shot_events(descriptors, duration):
    if not descriptors:
        return [], []
    scores = np.asarray([x["difference"] for x in descriptors[1:]], float)
    median = float(np.median(scores)) if len(scores) else 0
    mad = float(np.median(np.abs(scores-median))) if len(scores) else 0
    threshold = max(.11, median + 8 * max(mad, .001))
    # Dark palettes can change decisively while mean RGB remains well below
    # 11%. A distribution jump supplies a separate, contrast-aware branch.
    palette_threshold = max(.025, median + 8 * max(mad, .001))
    histogram_scores = np.asarray([row["histogram_distance"] for row in descriptors[1:]], float)
    histogram_median = float(np.median(histogram_scores)) if len(histogram_scores) else 0
    histogram_mad = float(np.median(np.abs(histogram_scores-histogram_median))) if len(histogram_scores) else 0
    histogram_threshold = max(.30, histogram_median+8*max(histogram_mad, .002))
    def is_boundary(row):
        return ((row["difference"] >= threshold and (row["histogram_distance"] > .18 or row["difference"] > .25))
                or (row["difference"] >= palette_threshold and row["histogram_distance"] >= histogram_threshold))
    candidates = []
    transitions = []
    ramp_indices = set()
    rgb = np.asarray([row["rgb"] for row in descriptors], float)/255
    deltas = np.diff(rgb, axis=0)
    for center in range(1, len(deltas)-1):
        window = deltas[center-1:center+2]
        lengths = np.linalg.norm(window, axis=1)
        if lengths.min() < .008 or lengths.max() > lengths.min()*2.5:
            continue
        directions = window/lengths[:, None]
        if min(float(np.dot(directions[0], directions[1])), float(np.dot(directions[1], directions[2]))) >= .97:
            ramp_indices.update((center, center+1, center+2))
    if ramp_indices:
        ordered = sorted(ramp_indices)
        runs = []
        for index in ordered:
            if not runs or index > runs[-1][-1]+1:
                runs.append([index])
            else:
                runs[-1].append(index)
        for run in runs:
            first, last = descriptors[run[0]-1], descriptors[run[-1]]
            near_black = min(first["luma"], last["luma"]) < .05
            transitions.append({"id": f"transition-{len(transitions)+1:04d}", "type": "fade_candidate" if near_black else "color_ramp_candidate",
                                "start": first["time"], "end": last["time"], "status": "inferred", "method": "coherent-multi-frame-rgb-ramp",
                                "evidence": [first["frame_id"], last["frame_id"]], "limits": "appearance ramp can also be lighting, grade or non-identifiable rapid color edits"})
    flash_return_indices = set()
    for i in range(1, len(descriptors)):
        if i in flash_return_indices or i in ramp_indices:
            continue
        row = descriptors[i]
        if is_boundary(row):
            # Near-white/black single-frame flashes are signals, not duplicate cuts.
            if i + 1 < len(descriptors):
                after = descriptors[i+1]
                before = descriptors[i-1]
                return_distance = float(np.linalg.norm(np.asarray(after["rgb"])-np.asarray(before["rgb"]))/255/math.sqrt(3))
                flash = (row["luma"] > .95 or row["luma"] < .025) and return_distance < .06 and is_boundary(after)
                if flash:
                    transitions.append({"id": f"transition-{len(transitions)+1:04d}", "type": "flash_candidate", "start": row["time"], "end": after["time"], "status": "inferred", "method": "luma-extreme-return", "evidence": [row["frame_id"], after["frame_id"]]})
                    flash_return_indices.add(i+1)
                    continue
            candidates.append(row)
    boundaries = [0.0, *[x["time"] for x in candidates], duration]
    shots = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        if end <= start:
            continue
        shot = {"id": f"shot-{len(shots)+1:04d}", "start": round(start, 9), "end": round(end, 9),
                "duration": round(end-start, 9), "status": "detected", "method": "adaptive-rgb-histogram-cut",
                "boundary": {"start_status": "media-start" if i == 0 else "candidate", "threshold": round(threshold, 6),
                             "palette_rgb_threshold": round(palette_threshold, 6), "histogram_threshold": round(histogram_threshold, 6)}}
        if i:
            boundary = candidates[i-1]
            previous = descriptors[max(0, boundary["index"]-1)]
            shot["boundary"].update({"start_pts": boundary["pts"], "time_base": boundary["time_base"], "start_interval": [previous["time"], boundary["time"]], "score": round(boundary["difference"], 6)})
            shot["evidence"] = [boundary["frame_id"]]
        shots.append(shot)
    # Detect monotone fades to/from black with observable luma evidence.
    if len(descriptors) >= 4:
        dark = [x["luma"] < .05 for x in descriptors]
        signal_times = np.asarray([x["time"] for x in descriptors])
        for i in range(1, len(descriptors)):
            if dark[i-1] != dark[i]:
                center = descriptors[i]["time"]
                begin, end = np.searchsorted(signal_times, [center-.45, center+.45])
                nearby = descriptors[int(begin):int(end)]
                if len(nearby) < 4:
                    continue
                values = np.asarray([x["luma"] for x in nearby])
                delta = np.diff(values)
                monotonic = max(float(np.mean(delta >= -.01)), float(np.mean(delta <= .01)))
                if values.max()-values.min() > .14 and monotonic >= .88 and np.max(np.abs(delta)) < threshold:
                    if any(event["type"] == "fade_candidate" and event["start"] <= nearby[-1]["time"] and event["end"] >= nearby[0]["time"] for event in transitions):
                        continue
                    if transitions and abs(transitions[-1]["start"]-nearby[0]["time"]) < .4:
                        continue
                    transitions.append({"id": f"transition-{len(transitions)+1:04d}", "type": "fade_candidate", "start": nearby[0]["time"], "end": nearby[-1]["time"], "status": "inferred", "method": "monotone-luma-ramp-near-black", "evidence": [nearby[0]["frame_id"], nearby[-1]["frame_id"]], "limits": "appearance ramp could also be scene lighting"})
    return shots, transitions


def _parse_supplied_transcript(path, duration, analysis_source_hash=None):
    if path is None:
        return None
    source = Path(path).expanduser().resolve()
    limit = 16*1024*1024 if source.suffix.lower() == ".json" else 1024*1024
    if not source.is_file() or source.stat().st_size > limit:
        raise ValueError("transcript must be a local file no larger than 16 MiB JSON / 1 MiB text")
    raw = source.read_text(encoding="utf-8-sig")
    result = {"origin": "user_supplied", "source_sha256": _digest(source), "text": raw, "status": "supplied", "limits": "supplied text is not OCR-visible text or a verified speech transcript"}
    if source.suffix.lower() == ".json":
        def invalid_constant(value):
            raise ValueError(f"non-finite transcript JSON constant: {value}")
        try:
            value = json.loads(raw, parse_constant=invalid_constant)
        except RecursionError as error:
            raise ValueError("transcript JSON exceeds nesting limit") from error
        if not isinstance(value, (list, dict)):
            raise ValueError("JSON transcript must contain a cue list or object")
        asr_import = isinstance(value, dict) and value.get("kind") == "rea-video-transcript"
        if asr_import:
            media_source = value.get("source", {})
            if not isinstance(media_source, dict):
                raise ValueError("ASR transcript source must be an object")
            result.update({"origin": "imported_model_derived_asr", "status": "model-derived", "import_origin": "user_supplied_artifact",
                           "text": value.get("text", ""), "provider": value.get("provider"), "source_media": media_source,
                           "source_matches_analysis": media_source.get("sha256") == analysis_source_hash if analysis_source_hash else None,
                           "model_coverage": value.get("coverage"), "language": value.get("language"), "words": value.get("words", []),
                           "analysis_import_range": [0, duration], "words_time_scope": "external artifact original range; not aligned to visible OCR",
                           "limits": "imported speech text/times remain model-derived; external source identity/coverage is preserved and is not visible OCR or measured speech truth",
                           "time_convention": value.get("time_convention")})
        cues = value if isinstance(value, list) else value.get("segments", []) if asr_import else value.get("captions", value.get("cues", []))
        if not isinstance(cues, list):
            raise ValueError("JSON transcript cues must be a list")
        cleaned = []
        for cue in cues:
            if not isinstance(cue, dict) or not isinstance(cue.get("text"), str):
                raise ValueError("each supplied cue requires text")
            try:
                if isinstance(cue.get("start"), bool) or isinstance(cue.get("end"), bool):
                    raise ValueError("boolean timestamps are invalid")
                start, end = float(cue["start"]), float(cue["end"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("each supplied cue requires finite numeric start/end") from error
            if asr_import and math.isfinite(start+end) and (start >= duration or end <= 0):
                continue
            if not math.isfinite(start+end) or not 0 <= start < min(end, duration) or (not asr_import and end > duration + .1):
                raise ValueError("supplied cue times must be finite and within the analyzed range")
            cleaned.append({"start": start, "end": min(end, duration), "text": cue["text"], "origin": result["origin"],
                            "status": "model-derived" if asr_import else "supplied", "original_range": [start, end]})
        result["cues"] = cleaned
    return result


def _aggregate_style(captions):
    subset = [x for x in captions if x.get("role") == "caption_candidate"] or captions
    if not subset:
        return {"status": "unknown", "reason": "no readable text detected", "font_family": "unknown"}
    def med(key, default):
        values = [x["style"].get(key, default) for x in subset]
        return np.median(values, axis=0).tolist()
    representative = max(subset, key=lambda x: x["end"]-x["start"])
    result = {**representative["style"], "font_size_ratio": round(float(med("font_size_ratio", .07)), 6),
            "fill": [int(x) for x in med("fill", [255, 255, 255])], "stroke": [int(x) for x in med("stroke", [0, 0, 0])],
            "stroke_width_ratio": round(float(med("stroke_width_ratio", .002)), 6),
            "position": [round(float(x), 6) for x in med("position", [.5, .8])],
            "source_caption_ids": [x["id"] for x in subset], "status": "estimated",
            "method": "median-caption-raster-appearance", "font_candidates": representative.get("font_candidates", [])}
    palette = []
    for caption in subset:
        for entry in caption["style"].get("highlight_palette", []):
            existing = next((item for item in palette if np.linalg.norm(np.asarray(item["fill"])-np.asarray(entry["fill"])) < 35), None)
            if existing:
                existing["source_caption_ids"].append(caption["id"])
                existing["evidence"] = list(dict.fromkeys([*existing["evidence"], *entry["evidence"]]))
            else:
                palette.append({"fill": entry["fill"], "source_caption_ids": [caption["id"]], "evidence": entry["evidence"], "status": "inferred"})
    if palette:
        result["highlight_palette"] = palette
        result["highlight"] = palette[0]["fill"]
        result["highlight_mode"] = "word-progress-candidate"
        result["highlight_status"] = "inferred"
    return result


def _reading_matches(reading, alternatives):
    reading = " ".join(re.findall(r"\w+", reading.casefold()))
    if not reading:
        return False
    for value in alternatives:
        value = " ".join(re.findall(r"\w+", value.casefold()))
        if value and difflib.SequenceMatcher(None, value, reading).ratio() >= .76:
            return True
    return False


def _classify_text_regions(regions, *, allow_single_observation=False):
    """Keep weak/scene readings without promoting diagram shapes to subtitles."""
    selected = []
    for region in regions:
        reasons = []
        glyphs = sum(character.isalnum() for character in region["text"])
        score = region.get("engine_score", 0)
        if score < 60:
            reasons.append("low_uncalibrated_engine_score")
        if region["bbox"][3] > .25:
            reasons.append("region_height_unusual_for_subtitle")
        if glyphs < 3 and (score < 85 or len(region["observations"]) < 2):
            reasons.append("ambiguous_short_reading")
        if not glyphs:
            reasons.append("no_alphanumeric_glyphs")
        if region.get("role") == "caption_candidate" and (region.get("style", {}).get("position", [0, 0])[1] < .70 or region["bbox"][1] + region["bbox"][3] < .72):
            reasons.append("caption_lane_uncertain")
        words = [word for observation in region.get("observations", []) for word in observation.get("word_appearances", [])]
        if words:
            heights = np.asarray([word["bbox"][3] for word in words], float)
            centers = np.asarray([word["bbox"][1]+word["bbox"][3]/2 for word in words], float)
            # A subtitle line has one coherent baseline and comparable glyph
            # scale. Graphic rings/symbols produce OCR boxes with large height
            # and baseline variance; keep them for evidence, never reuse them.
            if len(words) >= 2:
                height_ratio = float(max(heights)/max(min(heights), 1e-6))
                baseline_span = float(max(centers)-min(centers))
                if height_ratio > 2.6:
                    reasons.append("word_height_incoherent")
                if baseline_span > max(.08, float(np.median(heights))*.9):
                    reasons.append("word_baseline_incoherent")
                region["layout_quality"] = {"word_count": len(words), "height_ratio": round(height_ratio, 5),
                                             "baseline_span": round(baseline_span, 5), "status": "coherent" if not any(reason in reasons for reason in ("word_height_incoherent", "word_baseline_incoherent")) else "incoherent",
                                             "method": "word-box-height-and-baseline-dispersion"}
        if len(region.get("observations", [])) < 2 and not allow_single_observation:
            reasons.append("single_temporal_observation")
        if not region.get("font_candidates") or max(candidate.get("glyph_iou", 0) for candidate in region.get("font_candidates", [])) < .10:
            reasons.append("weak_closed_catalog_geometry_fit")
        region["quality"] = {"status": "suspect" if reasons else "candidate", "reasons": reasons,
                             "method": "OCR-score-and-layout-heuristics", "limits": "uncalibrated triage; legitimate short inserts and unusual typography remain available in text_regions"}
        if region.get("role") == "caption_candidate" and not reasons:
            selected.append(region)
    return selected


def _embedded_subtitles(path, probe, *, video_origin, duration):
    inventory = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "subtitle"]
    if not inventory:
        return {"status": "absent", "streams": [], "events": []}
    supported = {"ass", "ssa", "srt", "subrip", "webvtt", "mov_text", "text"}
    streams = [{"stream_index": stream["index"], "codec": stream.get("codec_name"), "language": stream.get("tags", {}).get("language"),
                "origin": "embedded_subtitle_stream", "status": "pending" if stream.get("codec_name") in supported else "unsupported",
                "events": [], "limits": "stream text/times do not prove it is visible in flattened video; original formatting is not reconstructed"} for stream in inventory[:16]]
    selected = {stream["stream_index"]: stream for stream in streams if stream["status"] == "pending"}
    events, budget_exhausted = [], False
    if selected:
        with av.open(str(path), options={"protocol_whitelist": "file,pipe", "format_whitelist": LOCAL_MEDIA_FORMATS}) as container:
            active = [stream for stream in container.streams.subtitles if stream.index in selected]
            for packet_index, packet in enumerate(container.demux(*active)):
                if packet_index >= 20000 or len(events) >= 10000:
                    budget_exhausted = True
                    break
                if not packet.size:
                    continue
                target = selected[packet.stream.index]
                if packet.pts is None or not packet.time_base:
                    target["status"] = "partial"
                    target["timing_issue"] = "packets without PTS retained only as an uncertainty"
                    continue
                start = float(packet.pts*packet.time_base)-video_origin
                end = start + float(packet.duration*packet.time_base) if packet.duration else None
                if start >= duration or end is not None and end <= 0:
                    continue
                try:
                    texts = []
                    for rectangle in packet.decode():
                        raw = getattr(rectangle, "dialogue", None) or getattr(rectangle, "text", None)
                        if raw:
                            texts.append(raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw))
                    raw_text = "\n".join(texts)
                    text = re.sub(r"\{[^}]*\}", "", raw_text).replace(r"\N", "\n").replace(r"\n", "\n").replace(r"\h", " ")
                    if not text.strip():
                        continue
                    event = {"id": f"embedded-{len(events)+1:05d}", "stream_index": packet.stream.index, "text": text, "raw_dialogue": raw_text,
                             "start": round(max(0, start), 9), "end": round(min(duration, end), 9) if end is not None else None,
                             "source_start": round(start, 9), "pts": packet.pts, "duration_ticks": packet.duration, "time_base": _rational(packet.time_base),
                             "origin": "embedded_subtitle_stream", "status": "reported", "timing_status": "measured-packet-PTS" if end is not None else "unknown-end",
                             "method": "container-subtitle-packet-decoder", "limits": "not merged with pixel OCR or supplied/ASR speech; raw dialogue may contain formatting"}
                    target["events"].append(event)
                    events.append(event)
                except (av.error.FFmpegError, ValueError) as error:
                    target["status"] = "partial"
                    target["reason"] = str(error)[:300]
    for stream in streams:
        if stream["status"] == "pending":
            stream["status"] = "partial" if budget_exhausted else "decoded"
    return {"status": "partial" if budget_exhausted or any(stream["status"] in {"partial", "unsupported"} for stream in streams) else "decoded",
            "streams": streams, "events": events, "budget_exhausted": budget_exhausted, "packet_budget": 20000, "cue_budget": 10000}


def _refine_caption_timing(path, captions, shots, frame_index, samples, out, *, stream_index, origin, sar, rotation, lang, started, budget=240):
    """Bounded local OCR pass on actual display frames around sampled edges.

    PTS are measured; text presence remains model-derived. Unresolved/over-budget
    edges retain their coarse intervals rather than gaining fabricated precision.
    """
    eligible = sorted(captions, key=lambda cue: (cue.get("role") != "caption_candidate", cue["start"]))[:40]
    wanted = {}
    for cue in eligible:
        cue["timing"]["sampled_intervals"] = {key: list(cue["timing"][key]) for key in ("onset_interval", "offset_interval")}
        cue["timing"]["local_observations"] = []
        begin, end = cue["timing"]["onset_interval"], cue["timing"]["offset_interval"]
        for row in frame_index:
            if begin[0]-.000001 <= row["time"] <= begin[1]+.000001 or end[0]-.000001 <= row["time"] <= end[1]+.000001:
                # Frame at the next shot belongs to that next segment, including
                # when identical words happen to remain visible across a cut.
                segment = next((shot for shot in shots if shot["id"] == cue.get("shot_id")), None)
                if segment and not segment["start"]-.000001 <= row["time"] < segment["end"]-.000001:
                    continue
                wanted.setdefault(row["index"], []).append(cue)
    if not wanted:
        return {"status": "not-run", "reason": "no temporal cue windows", "ocr_calls": 0, "budget": budget}
    known_samples = {row["id"]: row for row in samples}
    last_wanted = max(wanted)
    calls, frames_inspected, failures, evidence_omitted = 0, set(), [], 0
    budget_exhausted = False
    with av.open(str(path), options={"protocol_whitelist": "file,pipe", "format_whitelist": LOCAL_MEDIA_FORMATS}) as container:
        stream = next(item for item in container.streams.video if item.index == stream_index)
        for index, frame in enumerate(container.decode(stream)):
            if index > last_wanted or calls >= budget or time.monotonic()-started > 900:
                budget_exhausted = calls >= budget or time.monotonic()-started > 900
                break
            if index not in wanted:
                continue
            row = frame_index[index]
            image = _display(frame.to_image(), sar, rotation)
            for cue in wanted[index]:
                if calls >= budget:
                    budget_exhausted = True
                    break
                # Existing positive OCR is evidence on this same decoded frame.
                present = any(observation["evidence"] == row["id"] for observation in cue["observations"])
                if not present:
                    x, y, w, h = cue["bbox"]
                    left, top = max(0, round((x-.12*w)*image.width)), max(0, round((y-.7*h)*image.height))
                    right, bottom = min(image.width, round((x+1.12*w)*image.width)), min(image.height, round((y+1.7*h)*image.height))
                    crop = image.crop((left, top, right, bottom))
                    if crop.height < 90:
                        crop = crop.resize((crop.width*2, crop.height*2))
                    try:
                        readings = detect_text(crop, lang, timeout=8, psm=6)
                        calls += 1
                        present = any(_reading_matches(reading["text"], cue["text_alternatives"]) for reading in readings)
                    except (subprocess.TimeoutExpired, RuntimeError, OSError) as error:
                        failures.append({"time": row["time"], "caption_id": cue["id"], "reason": str(error)[:200]})
                        calls += 1
                        continue
                frames_inspected.add(index)
                if row["id"] not in known_samples:
                    if len(samples) >= MAX_EVIDENCE:
                        evidence_omitted += 1
                        cue["timing"]["local_observations"].append({"time": row["time"], "pts": row["pts"], "time_base": row["time_base"], "present": present,
                                                                     "evidence": row["id"], "status": "model-derived", "method": "tesseract-ROI-reading-match",
                                                                     "evidence_path_status": "omitted-evidence-budget"})
                        continue
                    evidence_path = out / "evidence" / f"{row['id']}.jpg"
                    if evidence_path.is_symlink():
                        raise ValueError("refusing evidence symlink")
                    preview = image.copy()
                    preview.thumbnail((1280, 1280))
                    with tempfile.NamedTemporaryFile(suffix=".jpg", dir=out/"evidence", delete=False) as file:
                        temp = Path(file.name)
                    try:
                        preview.save(temp, quality=90)
                        os.replace(temp, evidence_path)
                    finally:
                        temp.unlink(missing_ok=True)
                    source_hash = samples[0]["source_sha256"]
                    sample = {**row, "path": str(evidence_path.relative_to(out)), "sha256": _digest(evidence_path), "source_sha256": source_hash,
                              "coordinate_space": "display", "width": image.width, "height": image.height, "inspection": "cue-boundary-local-ROI-OCR"}
                    samples.append(sample)
                    known_samples[row["id"]] = sample
                cue["timing"]["local_observations"].append({"time": row["time"], "pts": row["pts"], "time_base": row["time_base"], "present": present,
                                                             "evidence": row["id"], "status": "model-derived", "method": "tesseract-ROI-reading-match"})
    refined = 0
    for cue in eligible:
        observations = sorted(cue["timing"]["local_observations"], key=lambda row: row["time"])
        onset = [row for row in observations if row["time"] <= cue["first_seen"]+.000001]
        offset = [row for row in observations if row["time"] >= cue["last_seen"]-.000001]
        segment = next((shot for shot in shots if shot["id"] == cue.get("shot_id")), None)
        segment_start, segment_end = (segment["start"], segment["end"]) if segment else (0, frame_index[-1]["time"]+frame_index[-1]["duration"])
        onset_refined = offset_refined = False
        absent = [row for row in onset if not row["present"]]
        if absent:
            lower = absent[-1]
            visible = next((row for row in onset if row["present"] and row["time"] > lower["time"]), None)
            if visible:
                cue["start"] = visible["time"]
                cue["timing"]["onset_interval"] = [lower["time"], visible["time"]]
                onset_refined = True
        elif onset and onset[0]["present"] and abs(onset[0]["time"]-segment_start) < .000001:
            cue["start"] = segment_start
            cue["timing"]["onset_interval"] = [segment_start, segment_start]
            onset_refined = True
        missing = next((row for row in offset if not row["present"]), None)
        if missing:
            visible = [row for row in offset if row["present"] and row["time"] < missing["time"]]
            if visible:
                cue["end"] = missing["time"]
                cue["timing"]["offset_interval"] = [visible[-1]["time"], missing["time"]]
                offset_refined = True
        elif offset and offset[-1]["present"] and abs(cue["end"]-segment_end) < .000001:
            last_frame = next((row for row in reversed(frame_index) if row["time"] < segment_end-.000001), None)
            if last_frame and offset[-1]["evidence"] == last_frame["id"]:
                cue["end"] = segment_end
                cue["timing"]["offset_interval"] = [offset[-1]["time"], segment_end]
                offset_refined = True
        if onset_refined or offset_refined:
            cue["timing"].update({"status": "model-derived" if onset_refined and offset_refined else "estimated", "method": "decoded-PTS-local-ROI-OCR",
                                  "onset_refined": onset_refined, "offset_refined": offset_refined,
                                  "limits": "text visibility is OCR-derived; interval width reports actual decoded-frame precision, not universal accuracy"})
            cue["evidence"] = list(dict.fromkeys([*cue["evidence"], *[row["evidence"] for row in observations]]))
            refined += int(onset_refined and offset_refined)
    samples.sort(key=lambda row: row["index"])
    return {"status": "partial" if budget_exhausted or failures or refined < len(captions) else "completed", "ocr_calls": calls,
            "decoded_frames_inspected": len(frames_inspected), "budget": budget, "caption_budget": 40,
            "fully_refined_cues": refined, "candidate_cues": len(captions), "budget_exhausted": budget_exhausted, "failures": failures,
            "evidence_omitted": evidence_omitted, "evidence_budget": MAX_EVIDENCE}


def analyze(source: str | Path, out_dir: str | Path, *, ocr: str = "auto", ocr_lang: str = "eng", max_seconds: float | None = None, sample_fps: float = 4.0, transcript: str | Path | None = None, motion_profile: str = "affine") -> dict:
    started = time.monotonic()
    path = Path(source).expanduser().resolve()
    out = Path(out_dir).expanduser().resolve()
    if not path.is_file():
        raise ValueError("source must be an existing local media file")
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds 8 GiB admission limit")
    output_names = ("analysis.json", "timeline.json", "captions.json", "subtitle-styles.json", "motion.json",
                    "audio-cues.json", "embedded-subtitles.json", "composition.json", "uncertainties.json", "shots.csv")
    if path == out or path in [out / name for name in output_names] or path.is_relative_to(out / "evidence"):
        raise ValueError("output must not overwrite the source")
    if isinstance(sample_fps, bool) or not isinstance(sample_fps, (int, float)) or not math.isfinite(sample_fps) or not 0 < sample_fps <= 30:
        raise ValueError("sample_fps must be finite and in (0, 30]")
    if max_seconds is not None and (isinstance(max_seconds, bool) or not isinstance(max_seconds, (int, float)) or not math.isfinite(max_seconds) or not 0 < max_seconds <= 7200):
        raise ValueError("max_seconds must be finite and in (0, 7200]")
    if not isinstance(ocr, str) or ocr not in {"auto", "off", "tesseract", "required", "on"}:
        raise ValueError("ocr must be auto, off, tesseract or required")
    if not isinstance(motion_profile, str) or motion_profile not in {"affine", "coarse", "off"}:
        raise ValueError("motion_profile must be affine, coarse or off")
    if not isinstance(ocr_lang, str) or not re.fullmatch(r"[A-Za-z0-9_+/.-]{1,100}", ocr_lang) or ".." in ocr_lang:
        raise ValueError("invalid Tesseract language identifier")
    out.mkdir(parents=True, exist_ok=True)
    evidence_dir = out / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    # Do not follow attacker-created output links into arbitrary locations.
    if evidence_dir.resolve().parent != out or evidence_dir.is_symlink():
        raise ValueError("evidence output must remain inside analysis directory")
    source_hash = _digest(path)
    caps = ocr_capabilities(ocr_lang) if ocr != "off" else {"available": False, "reason": "disabled by request"}
    if ocr in {"required", "on", "tesseract"} and not caps["available"]:
        raise RuntimeError(caps["reason"])
    tracker = TextTracker(1/sample_fps)
    text_samples = []
    descriptors, samples, frame_index = [], [], []
    motions = []
    ocr_calls, ocr_reused, ocr_failures = 0, 0, []
    ocr_regions_omitted = 0
    previous_ocr_descriptor = None
    previous_texts = []
    previous_sample = None
    previous_tiny = None
    previous_hist = None
    next_sample = 0.0
    limit_reason = None
    missing_pts = 0
    font_dir = Path(__file__).resolve().parents[2] / "assets" / "fonts"
    if not font_dir.is_dir():
        font_dir = Path(__file__).resolve().parent / "resources" / "fonts"
    is_image = path.suffix.lower() in IMAGE_SUFFIXES
    stream_info = None
    rotation, sar = 0.0, 1.0
    origin = 0.0
    actual_end, nominal_interval = 0.0, 0.0
    if is_image:
        try:
            with Image.open(path) as opened:
                if opened.width * opened.height > MAX_PIXELS:
                    raise ValueError("image exceeds 16 megapixel admission limit")
                if getattr(opened, "n_frames", 1) > 1:
                    raise ValueError("multi-frame PNG/WebP/TIFF images require conversion to a flat video container")
                original = ImageOps.exif_transpose(opened).convert("RGB")
        except Image.DecompressionBombError as error:
            raise ValueError("image decompression bomb exceeds admission limit") from error
        source_info = {"path": str(path), "sha256": source_hash, "type": "image", "width": original.width, "height": original.height, "duration": 0.0, "fps": None, "time_base": None, "stream_index": None}
        iterator = [(original, None, None, 0.0, 0.0)]
        container = None
    else:
        probe = _probe(path)
        videos = [x for x in probe.get("streams", []) if x.get("codec_type") == "video" and not x.get("disposition", {}).get("attached_pic")]
        if not videos:
            raise ValueError("no decodable non-attached video stream")
        stream_info = videos[0]
        if int(stream_info.get("width", 0)) * int(stream_info.get("height", 0)) > MAX_PIXELS:
            raise ValueError("video exceeds 16 megapixel frame admission limit")
        for item in stream_info.get("side_data_list", []):
            if "rotation" in item:
                rotation = float(item["rotation"])
        rotation = float(stream_info.get("tags", {}).get("rotate", rotation))
        if ":" in stream_info.get("sample_aspect_ratio", ""):
            sar = _fraction(stream_info["sample_aspect_ratio"].replace(":", "/"), 1.0) or 1.0
        if not .1 <= sar <= 10 or abs(rotation) > 360:
            raise ValueError("unsupported display transformation metadata")
        fps = _fraction(stream_info.get("avg_frame_rate")) or _fraction(stream_info.get("r_frame_rate")) or 30
        nominal_interval = 1 / fps
        declared_duration = _fraction(stream_info.get("duration")) or _fraction(probe.get("format", {}).get("duration"))
        container = av.open(str(path), options={"protocol_whitelist": "file,pipe", "format_whitelist": LOCAL_MEDIA_FORMATS})
        stream = next(x for x in container.streams.video if x.index == int(stream_info["index"]))
        stream.thread_type = "AUTO"
        first_pts = [None]
        def frames():
            for index, frame in enumerate(container.decode(stream)):
                absolute = float(frame.pts * frame.time_base) if frame.pts is not None and frame.time_base else None
                if first_pts[0] is None:
                    first_pts[0] = absolute or 0.0
                t = absolute-first_pts[0] if absolute is not None else index/fps
                duration = float(frame.duration * frame.time_base) if frame.duration and frame.time_base else nominal_interval
                yield frame, frame.pts, frame.time_base, t, duration
        iterator = frames()
        source_info = {"path": str(path), "sha256": source_hash, "type": "video", "width": int(stream_info["width"]), "height": int(stream_info["height"]),
                       "coded_width": int(stream_info["width"]), "coded_height": int(stream_info["height"]), "fps": fps,
                       "frame_rate": stream_info.get("avg_frame_rate"), "time_base": _rational(stream.time_base), "stream_index": stream.index,
                       "duration": declared_duration, "rotation": rotation, "sample_aspect_ratio": sar,
                       "codec": stream_info.get("codec_name"), "pixel_format": stream_info.get("pix_fmt"),
                       "color": {key: stream_info.get(key) for key in ("color_space", "color_transfer", "color_primaries", "color_range")},
                       "stream_metadata": {"start_time": stream_info.get("start_time"), "duration": stream_info.get("duration"), "disposition": stream_info.get("disposition")}}
    try:
        for index, (frame, pts, time_base, t, frame_duration) in enumerate(iterator):
            if index >= MAX_FRAMES or time.monotonic()-started > 900:
                limit_reason = "decoded frame budget" if index >= MAX_FRAMES else "900-second analysis deadline"
                break
            if not is_image and max_seconds is not None and t >= max_seconds:
                break
            if t < -.001 or (frame_index and t < frame_index[-1]["time"]):
                raise ValueError("non-monotonic decoded presentation timestamps")
            if pts is None and not is_image:
                missing_pts += 1
            image = frame if is_image else _display(frame.to_image(), sar, rotation)
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("display-transformed frame exceeds pixel budget")
            source_info["width"], source_info["height"] = image.size
            if index == 0 and not is_image:
                origin = float(pts*time_base) if pts is not None and time_base else 0.0
                source_info["start_pts"] = pts
                source_info["presentation_origin_seconds"] = origin
            actual_end = max(actual_end, t+frame_duration)
            frame_id = f"frame-{index:08d}"
            row = {"id": frame_id, "index": index, "pts": pts, "time_base": _rational(time_base), "time": round(t, 9), "duration": round(frame_duration, 9), "timestamp_status": "not-applicable" if is_image else "measured" if pts is not None else "estimated-from-nominal-fps"}
            frame_index.append(row)
            tiny = _thumbnail(image)
            hist = _histogram(tiny)
            difference = float(np.mean(np.abs(tiny.astype(float)-previous_tiny.astype(float)))/255) if previous_tiny is not None else 0.0
            descriptor = {"index": index, "frame_id": frame_id, "time": round(t, 9), "pts": pts, "time_base": _rational(time_base),
                          "difference": difference, "histogram_distance": float(np.abs(hist-previous_hist).sum()/3) if previous_hist is not None else 0.0,
                          "luma": float(tiny.mean()/255), "rgb": [round(float(x), 3) for x in tiny.mean(axis=(0, 1))]}
            descriptors.append(descriptor)
            previous_tiny, previous_hist = tiny, hist
            if t + .000001 < next_sample and not is_image:
                continue
            next_sample = t + 1/sample_fps
            if len(samples) >= MAX_EVIDENCE:
                continue
            evidence_path = evidence_dir / f"{frame_id}.jpg"
            if evidence_path.is_symlink():
                raise ValueError("refusing evidence symlink")
            preview = image.copy()
            preview.thumbnail((1280, 1280))
            with tempfile.NamedTemporaryFile(suffix=".jpg", dir=evidence_dir, delete=False) as file:
                temp_evidence = Path(file.name)
            try:
                preview.save(temp_evidence, quality=90)
                os.replace(temp_evidence, evidence_path)
            finally:
                temp_evidence.unlink(missing_ok=True)
            sample = {**row, "path": str(evidence_path.relative_to(out)), "sha256": _digest(evidence_path), "source_sha256": source_hash, "coordinate_space": "display", "width": image.width, "height": image.height}
            samples.append(sample)
            if motion_profile != "off" and previous_sample is not None and difference < .11:
                motions.append({"time": round(t, 9), "start": previous_sample["time"], "evidence": [previous_sample["id"], frame_id], **phase_translation(previous_sample["tiny"], tiny)})
            previous_sample = {"time": t, "id": frame_id, "tiny": tiny}
            observations = []
            if caps["available"]:
                current_descriptor = np.asarray(image.convert("RGB").resize((320, 180)), float)
                change = np.abs(current_descriptor-previous_ocr_descriptor) if previous_ocr_descriptor is not None else None
                # A small highlighted word can scarcely change whole-frame mean
                # luminance. The color max gate preserves those local changes.
                reusable = change is not None and float(change.mean()) < .15 and float(change.max()) < 6
                if reusable:
                    observations = previous_texts
                    ocr_reused += 1
                else:
                    try:
                        observations = detect_text(image, ocr_lang)
                        if len(observations) > 200:
                            ocr_regions_omitted += len(observations)-200
                            observations = sorted(observations, key=lambda row: (row["role"] != "caption_candidate", -row["engine_score"]))[:200]
                        ocr_calls += 1
                        previous_texts, previous_ocr_descriptor = observations, current_descriptor
                    except (subprocess.TimeoutExpired, RuntimeError, OSError) as exc:
                        ocr_failures.append({"time": t, "reason": str(exc)[:300]})
                text_samples.append((observations, t, frame_id))
    finally:
        if container is not None:
            container.close()
    if not frame_index:
        raise ValueError("media produced no decoded frames in the requested range")
    main_sample_count = len(samples)
    main_sample_end = samples[-1]["time"] if samples else 0
    duration = 0.0 if is_image else round(actual_end, 9)
    if not is_image and not source_info["duration"]:
        source_info["duration"] = duration
    requested_end = min(source_info["duration"], max_seconds) if max_seconds is not None else source_info["duration"]
    analyzed_end = min(duration, requested_end) if requested_end else duration
    source_info["presentation_clock"] = _presentation_clock(frame_index, source_info.get("frame_rate") or source_info.get("fps")) if not is_image else {"status": "not-applicable", "variable_intervals": None}
    shots, transitions = _shot_events(descriptors, analyzed_end) if not is_image else ([], [])
    # Associate after full-frame cut detection, so identical words on different
    # shots remain distinct observed events rather than one clipped track.
    for observations, t, frame_id in text_samples:
        shot_id = next((shot["id"] for shot in shots if shot["start"] <= t < shot["end"]), None)
        tracker.update(observations, t, frame_id, shot_id=shot_id)
    captions = tracker.finish(analyzed_end if not is_image else 1.0)
    # Cap temporal estimates by the native observed shot boundaries.
    for caption in captions:
        caption["source_origin"] = "pixel_derived"
        caption["source_sha256"] = source_hash
        appearance_id = caption.get("appearance_evidence", caption["evidence"][0])
        first_ref = next((x for x in samples if x["id"] == appearance_id), None)
        if first_ref:
            with Image.open(out/first_ref["path"]) as sampled:
                representative = next((observation for observation in caption["observations"] if observation["evidence"] == appearance_id), caption["observations"][0])
                word_appearances = representative.get("word_appearances", [])
                caption["font_candidates"] = font_candidates(sampled.convert("RGB"), caption["bbox"], caption["text"], font_dir, words=word_appearances)
                if caption["font_candidates"]:
                    fitted = caption["font_candidates"][0]
                    if fitted["fit_score"] > 0 and fitted["width_relative_error"] < .25:
                        caption["style"].update({"font_size_ratio": round(fitted["size_px"]/sampled.height, 6),
                                                  "font_size_ratio_status": "candidate", "font_size_method": "closed-catalog-raster-geometry-fit",
                                                  "font_size_evidence": [first_ref["id"]], "render_font_candidate": fitted["font_file"],
                                                  "font_size_limits": fitted["size_semantics"]})
        for shot in shots:
            if shot["start"] <= caption["first_seen"] < shot["end"]:
                caption["shot_id"] = shot["id"]
                caption["end"] = min(caption["end"], shot["end"])
                caption["timing"]["onset_interval"][0] = max(shot["start"], caption["timing"]["onset_interval"][0])
                caption["timing"]["offset_interval"][1] = caption["end"]
                break
        if is_image:
            caption.update({"start": 0.0, "end": 0.0, "first_seen": 0.0, "last_seen": 0.0})
            caption["timing"] = {"status": "not-applicable", "method": "single-static-image", "limits": "image has no temporal duration"}
    text_regions = captions
    captions = _classify_text_regions(text_regions, allow_single_observation=is_image)
    refinement = {"status": "not-run", "reason": "no video captions or OCR unavailable", "ocr_calls": 0, "budget": 240}
    if not is_image and captions and caps["available"]:
        refinement = _refine_caption_timing(path, captions, shots, frame_index, samples, out, stream_index=source_info["stream_index"],
                                            origin=origin, sar=sar, rotation=rotation, lang=ocr_lang, started=started)
    motion_groups = []
    for shot in shots if motion_profile != "off" else []:
        points = [x for x in motions if shot["start"] < x["time"] < shot["end"]]
        motion_groups.append({"id": f"motion-{shot['id']}", "shot_id": shot["id"], "start": shot["start"], "end": shot["end"], **fit_motion(points)})
    if is_image:
        audio = {"status": "not-applicable", "has_audio": False, "onsets": [], "silences": []}
        embedded = {"status": "not-applicable", "streams": [], "events": []}
    else:
        try:
            embedded = _embedded_subtitles(path, probe, video_origin=origin, duration=analyzed_end)
        except (av.error.FFmpegError, ValueError, OSError) as exc:
            embedded = {"status": "unavailable", "reason": str(exc)[:500], "streams": [], "events": []}
        try:
            audio = analyze_audio(path, duration=analyzed_end, video_origin=origin, max_seconds=max_seconds if max_seconds is not None else analyzed_end)
        except (av.error.FFmpegError, ValueError, OSError) as exc:
            audio = {"status": "unavailable", "reason": str(exc)[:500], "has_audio": None, "onsets": [], "silences": []}
    for shot in shots:
        onsets = audio.get("onsets", [])
        if onsets:
            nearest = min(onsets, key=lambda x: abs(x["time"]-shot["start"]))
            shot["nearest_audio_onset"] = {"time": nearest["time"], "lag_seconds": round(shot["start"]-nearest["time"], 6), "status": "measured", "limits": "temporal proximity does not prove deliberate sync"}
    style = _aggregate_style(captions)
    supplied = _parse_supplied_transcript(transcript, analyzed_end, analysis_source_hash=source_hash)
    complete = not limit_reason and (is_image or analyzed_end + max(nominal_interval, .03) >= requested_end)
    coverage = {"requested_range": [0, requested_end], "decoded_range": [0, analyzed_end], "decoded_frame_extent": [0, duration], "complete": complete,
                "decoded_frames": len(frame_index), "indexed_frames": len(frame_index), "missing_pts": missing_pts,
                "decoded_frames_semantics": "indexed presentation frames in analyzed range; decoder boundary/lookahead frames are not counted",
                "signal_analyzed_frames": len(descriptors), "visual_evidence_samples": len(samples), "sample_fps_requested": sample_fps,
                "evidence_sample_budget": MAX_EVIDENCE, "main_pass_evidence_samples": main_sample_count, "evidence_budget_exhausted": main_sample_count == MAX_EVIDENCE,
                "ocr": {"status": "sampled-plus-local-refinement" if refinement.get("ocr_calls") else "sampled" if caps["available"] else "unavailable", "calls": ocr_calls, "reused": ocr_reused, "sampled_range": [0, main_sample_end], "failures": ocr_failures, "language": ocr_lang,
                        "regions_per_frame_budget": 200, "regions_omitted": ocr_regions_omitted, "track_budget": tracker.max_tracks, "track_observations_omitted": tracker.omitted_observations},
                "cue_boundary_refinement": refinement,
                "semantic_vision": {"status": "not_run", "reason": "no VLM provider called"}, "limit_reason": limit_reason,
                "outside_requested_range": [requested_end, source_info["duration"]] if max_seconds is not None and requested_end < source_info["duration"] else None}
    unknowns = [
        {"id": "original-project", "status": "unknown", "question": "Original editing software, source assets and unique layer/keyframe graph", "reason": "flattened media does not uniquely identify the original project"},
        {"id": "font-identity", "status": "unknown", "question": "Exact original font", "reason": "font fitting searches only the bundled catalog; candidates are not identity proof"},
        {"id": "production-origin", "status": "unknown", "question": "Filmed, AI-generated, 3D or hybrid origin", "reason": "appearance statistics cannot certify production origin"},
        {"id": "semantic-audio", "status": "not_run", "question": "Speech transcript, speaker and separated music/SFX", "reason": "signal analysis only; no ASR/source-separation model called"},
        {"id": "motion-scope", "status": "unknown", "question": "Perspective, original easing/keyframes and hidden masks", "reason": "coarse apparent translation only; other transforms remain unsupported"},
    ]
    if supplied and supplied.get("origin") == "imported_model_derived_asr":
        for unknown in unknowns:
            if unknown["id"] == "semantic-audio":
                unknown["question"] = "Native ASR, diarization and separated music/SFX"
                unknown["reason"] = "native ASR/separation not run by analyze; imported model-derived speech remains a separate channel with provider/source identity"
        if supplied.get("source_matches_analysis") is False:
            unknowns.append({"id": "external-asr-relationship", "status": "unknown", "reason": "imported transcript source hash differs from analyzed media; no media/speech/OCR correspondence is inferred"})
    if not caps["available"]:
        unknowns.append({"id": "ocr-unavailable", "status": "unavailable", "reason": caps["reason"]})
    if main_sample_count == MAX_EVIDENCE:
        unknowns.append({"id": "ocr-coverage-budget", "status": "partial", "reason": "visual/OCR sample budget reached; full decoded signal pass remains separate", "uninspected_after": main_sample_end})
    if ocr_regions_omitted or tracker.omitted_observations:
        unknowns.append({"id": "text-region-budget", "status": "partial", "reason": "dense text exceeded per-frame/track budgets; omitted counts are recorded in coverage.ocr"})
    claims = [{"id": "shot-map", "status": "detected", "method": "adaptive-rgb-histogram-cut", "value": len(shots), "evidence": [x["id"] for x in frame_index if x["index"] in {int(y.get("evidence", ["frame-00000000"])[0].split("-")[-1]) for y in shots}]},
              {"id": "caption-style", "status": style["status"], "value": style, "evidence": sorted({ref for caption in captions for ref in caption["evidence"]})}]
    analysis = {"schema_version": 1, "kind": "rea-video-analysis", "source": source_info, "coverage": coverage,
                "shots": shots, "transitions": transitions, "captions": captions, "text_regions": text_regions, "style": style, "motion": motion_groups,
                "audio": audio, "embedded_subtitles": embedded, "claims": claims, "unknowns": unknowns, "supplied_transcript": supplied,
                "evidence": samples, "toolchain": {"python_av": av.__version__, "numpy": np.__version__, "ocr": {"engine": "tesseract" if caps["available"] else None, "language": ocr_lang, "available": caps["available"]}, "analysis_seconds": round(time.monotonic()-started, 3)},
                "limits": ["global motion is approximate translation only", "all OCR/style values are estimates, not recovered original parameters", "no semantic video-origin certification", "sampled OCR plus bounded local refinement cannot certify every frame's text", "subtitle-candidate triage can retain legitimate short/unusual captions only in text_regions"]}
    analysis["coarse_motion"] = motion_groups
    if motion_profile == "off" or is_image:
        motion_groups = []
        coverage["motion"] = {"profile": motion_profile, "status": "not-applicable" if is_image else "disabled", "pair_budget": 192}
    elif motion_profile == "coarse":
        coverage["motion"] = {"profile": "coarse", "status": "completed", "method": "phase-translation-linear-fit"}
    elif len(shots) > 2000:
        coverage["motion"] = {"profile": "affine", "status": "unavailable", "reason": "shot count exceeds 2,000-shot affine profile", "fallback": "explicit coarse translation", "pair_budget": 192}
    else:
        from .motion import analyze_motion
        motion_groups = analyze_motion(analysis, out, max_pairs=192)
        coverage["motion"] = {"profile": "affine", "status": "completed", "pair_budget": 192,
                              "selected_pairs": sum(item["coverage"]["selected_pairs"] for item in motion_groups),
                              "accepted_pairs": sum(item["coverage"]["accepted_pairs"] for item in motion_groups),
                              "rejected_pairs": sum(item["coverage"]["rejected_pairs"] for item in motion_groups),
                              "pairs_omitted_by_budget": sum(item["coverage"]["pairs_omitted_by_budget"] for item in motion_groups),
                              "limits": "sampled apparent image-space fits; rejected pairs break trajectories; no camera/object or original-keyframe recovery"}
        for unknown in unknowns:
            if unknown["id"] == "motion-scope":
                unknown["reason"] = "sampled similarity/affine and temporal curve candidates; perspective, camera/object identity, original keys and hidden layers remain unknown"
        analysis["limits"][0] = "sampled image-space similarity/affine and curve candidates; hidden layers and original motion parameters remain unknown"
    analysis["motion"] = motion_groups
    analysis["toolchain"]["analysis_seconds"] = round(time.monotonic()-started, 3)
    timeline = {"schema_version": 1, "kind": "rea-video-timeline", "source": {"sha256": source_hash, "path": str(path), "duration": source_info["duration"]},
                "duration": analyzed_end, "time_semantics": "seconds relative to first displayed video PTS; source PTS retained in frame-index.json", "intervals": "half-open",
                "tracks": [{"id": "video", "type": "flattened-reference", "events": shots}, {"id": "transitions", "type": "inferred-transitions", "events": transitions}, {"id": "text", "type": "subtitle-candidates", "events": captions}, {"id": "scene-text", "type": "scene-or-suspect-text-candidates", "events": [region for region in text_regions if region not in captions]}, {"id": "embedded-subtitles", "type": "embedded-stream-text-not-observed-pixels", "events": embedded["events"]}, {"id": "motion", "type": "apparent-motion", "events": motion_groups}, {"id": "audio", "type": "signal-onsets", "events": audio.get("onsets", [])}], "unknowns": unknowns, "coverage": coverage}
    _write_json(evidence_dir/"frame-index.json", {"schema_version": 1, "kind": "rea-video-frame-index", "source_sha256": source_hash, "frames": frame_index})
    _write_json(out/"analysis.json", analysis)
    _write_json(out/"timeline.json", timeline)
    _write_json(out/"captions.json", {"schema_version": 1, "kind": "rea-video-captions", "origin": "pixel_derived", "captions": captions, "text_regions": text_regions, "supplied_transcript": supplied})
    _write_json(out/"subtitle-styles.json", {"schema_version": 1, "kind": "rea-video-subtitle-style", "style": style, "caption_styles": [{"id": x["id"], "style": x["style"], "font_candidates": x.get("font_candidates", [])} for x in captions]})
    _write_json(out/"motion.json", {"schema_version": 1, "kind": "rea-video-motion", "motion": motion_groups})
    _write_json(out/"audio-cues.json", {"schema_version": 1, "kind": "rea-video-audio", "audio": audio})
    _write_json(out/"embedded-subtitles.json", {"schema_version": 1, "kind": "rea-video-embedded-subtitles", "subtitles": embedded})
    _write_json(out/"composition.json", {"schema_version": 1, "kind": "rea-video-composition", "text_regions": [{"id": x["id"], "bbox": x["bbox"], "start": x["start"], "end": x["end"], "status": "observed-region-not-separated-layer", "quality": x["quality"]} for x in text_regions], "production_origin": "unknown", "original_layers": "unknown"})
    _write_json(out/"uncertainties.json", {"schema_version": 1, "kind": "rea-video-unknowns", "unknowns": unknowns})
    if (out/"shots.csv").is_symlink():
        raise ValueError("refusing shots.csv output symlink")
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=out, delete=False) as file:
        temp_csv = Path(file.name)
        writer = csv.DictWriter(file, fieldnames=["id", "start", "end", "duration", "status", "method"])
        writer.writeheader()
        writer.writerows({key: shot[key] for key in writer.fieldnames} for shot in shots)
    os.replace(temp_csv, out/"shots.csv")
    if _digest(path) != source_hash:
        raise RuntimeError("source changed during analysis; evidence is invalid")
    return analysis
