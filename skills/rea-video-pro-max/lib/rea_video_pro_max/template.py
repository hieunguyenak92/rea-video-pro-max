"""Evidence-linked style extraction and content-bound composition.

The reference timeline explains A.  A template retains reusable parameters.
Only explicit content bindings populate B; reference media is never a fallback.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import shutil
import statistics
import unicodedata
from pathlib import Path

from PIL import ImageFont, features

SCHEMA_VERSION = 1
MAX_SCENES = 256
MAX_DURATION = 600.0
MAX_PIXELS = 3840 * 2160
MAX_FRAMES = 36000
SUPPORTED_TRANSITIONS = {"cut", "dissolve", "fade", "wipe"}
SUPPORTED_ENTRIES = {"static", "fade", "pop", "slide"}
OBSERVED_STATUSES = {"measured", "estimated", "model-derived", "inferred", "candidate"}
VARIANT_FIELDS = {"font_size_ratio", "fill", "stroke", "stroke_width_ratio", "anchor", "anchor_x", "anchor_y",
                  "max_width_ratio", "box_color", "shadow", "highlight", "entry", "entry_duration", "line_height"}


def _number(value, name, minimum=0.0, maximum=math.inf):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return result


def _color(value, default):
    if value is None:
        return list(default)
    if not isinstance(value, (list, tuple)) or len(value) not in (3, 4):
        raise ValueError("colors must be [red, green, blue] or RGBA")
    return [int(_number(channel, "color channel", 0, 255)) for channel in value]


def _median(values, default):
    values = [float(value) for value in values if isinstance(value, (int, float)) and math.isfinite(value)]
    return statistics.median(values) if values else default


def _digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _style_value(captions, style, name, default):
    if name in style:
        return copy.deepcopy(style[name])
    for caption in captions:
        if name in caption.get("style", {}):
            return copy.deepcopy(caption["style"][name])
    return copy.deepcopy(default)


def _validated_style(style):
    if not isinstance(style, dict):
        raise ValueError("style must be an object")
    result = copy.deepcopy(style)
    limits = {"font_size_ratio": (0.055, 0.01, 0.2), "stroke_width_ratio": (0.003, 0, 0.025),
              "anchor_x": (0.5, 0.05, 0.95), "anchor_y": (0.82, 0.05, 0.95),
              "max_width_ratio": (0.88, 0.2, 0.98), "entry_duration": (0.18, 0, 2),
              "line_height": (1.2, 1, 2)}
    for name, (default, low, high) in limits.items():
        result[name] = _number(result.get(name, default), name, low, high)
    result["words_per_group"] = int(_number(result.get("words_per_group", 5), "words_per_group", 1, 12))
    for name, default in {"fill": [255, 255, 255], "stroke": [0, 0, 0], "highlight": [255, 222, 89],
                          "box_color": [0, 0, 0, 0], "shadow": [0, 0, 0, 140]}.items():
        result[name] = _color(result.get(name), default)
    result.setdefault("entry", "static")
    result.setdefault("anchor", "bottom")
    if result["entry"] not in SUPPORTED_ENTRIES or result["anchor"] not in {"top", "center", "bottom"}:
        raise ValueError("unsupported caption entry or anchor")
    return result


def _style_regimes(captions, aggregate, shots, duration, base):
    """Keep discrete observed appearances; scheduling B is a separate inference."""
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        return [], {"colors": [], "regimes": [], "status": "unknown", "reason": "reference duration unavailable"}
    variants, colors, events = [], [], []
    omitted_variants = 0
    def color_id(value, caption_ids, evidence, status):
        color = _color(value, base["highlight"])[:3]
        match = next((row for row in colors if sum((a-b)**2 for a, b in zip(color, row["fill"])) <= 24**2), None)
        if match is None:
            if len(colors) >= 64:
                return None
            match = {"id": f"palette-{len(colors)+1}", "fill": color, "source_caption_ids": [], "evidence": [], "status": status}
            colors.append(match)
        for name, values in (("source_caption_ids", caption_ids), ("evidence", evidence)):
            for value in values:
                if value not in match[name] and len(match[name]) < 1000:
                    match[name].append(value)
        return match["id"]
    for caption in sorted(captions[:1000], key=lambda row: row.get("start", 0)):
        raw = caption.get("style", {})
        if not isinstance(raw, dict):
            raise ValueError("caption style must be an object")
        start = _number(caption.get("start", 0), "reference caption start", 0, duration)
        end = _number(caption.get("end", start), "reference caption end", start, duration + .1)
        evidence = copy.deepcopy(caption.get("evidence", caption.get("evidence_refs", [])))
        if not isinstance(evidence, list):
            evidence = []
        parameters, provenance = {}, {}
        for name in ("font_size_ratio", "fill", "stroke", "stroke_width_ratio", "anchor", "box_color", "shadow", "max_width_ratio", "entry_duration"):
            status_key = "stroke_width_status" if name == "stroke_width_ratio" else name + "_status"
            status = raw.get(status_key, raw.get("status", "unknown"))
            field_evidence = raw.get(name + "_evidence", evidence)
            if name in raw and status in OBSERVED_STATUSES and field_evidence and (raw[name] is None or isinstance(raw[name], (int, float, str, list, tuple))):
                parameters[name] = copy.deepcopy(raw[name])
                provenance[name] = {"status": status, "method": raw.get(name + "_method", raw.get("method")), "evidence": copy.deepcopy(field_evidence)}
        if raw.get("status") in OBSERVED_STATUSES and evidence:
            position = raw.get("position")
            if isinstance(position, (list, tuple)) and len(position) == 2:
                parameters["anchor_x"] = min(.95, max(.05, _number(position[0], "caption position x", 0, 1)))
                parameters["anchor_y"] = min(.95, max(.05, _number(position[1], "caption position y", 0, 1)))
            if raw.get("animation") in {"static", "scale_candidate"}:
                parameters["entry"] = "pop" if raw["animation"] == "scale_candidate" else "static"
            if isinstance(raw.get("line_height_ratio"), (int, float)):
                parameters["line_height"] = min(2, max(1, raw["line_height_ratio"] / parameters.get("font_size_ratio", base["font_size_ratio"])))
        if parameters and len(variants) >= 256:
            omitted_variants += 1
        if parameters and len(variants) < 256:
            if "font_size_ratio" in parameters:
                parameters["font_size_ratio"] = min(.16, max(.025, _number(parameters["font_size_ratio"], "variant font ratio", .001, 1)))
            if "stroke_width_ratio" in parameters:
                parameters["stroke_width_ratio"] = min(.012, _number(parameters["stroke_width_ratio"], "variant stroke ratio", 0, .1))
            checked = _validated_style({**base, **parameters})
            variants.append({"id": f"appearance-{len(variants)+1}", "relative_start": start/duration, "relative_end": min(1, end/duration),
                             "style": {name: checked[name] for name in parameters}, "source_caption_ids": [caption.get("id")],
                             "evidence": evidence[:1000], "parameter_provenance": provenance, "status": "inferred",
                             "limits": "observed raster appearance; layout/entry substitutes and new-cue placement are implementation choices"})
        palette = raw.get("highlight_palette", [])
        if not isinstance(palette, list):
            raise ValueError("caption highlight_palette must be a list")
        if not palette and raw.get("highlight") is not None:
            palette = [{"fill": raw["highlight"], "status": raw.get("highlight_status", "unknown"), "evidence": evidence}]
        for item in palette[:64]:
            if not isinstance(item, dict):
                raise ValueError("highlight palette entries must be objects")
            status = item.get("status", raw.get("highlight_status", "unknown"))
            links = item.get("evidence", evidence)
            if not isinstance(links, list):
                raise ValueError("highlight evidence must be a list")
            if status not in OBSERVED_STATUSES or not links or item.get("fill") is None:
                continue
            identity = color_id(item["fill"], [caption.get("id")], links, status)
            if identity:
                span = item.get("observed_range", [start, end])
                if not isinstance(span, (list, tuple)) or len(span) != 2:
                    raise ValueError("palette observed_range must contain start and end")
                observed_start = _number(span[0], "palette observed start", 0, duration)
                _number(span[1], "palette observed end", observed_start, duration + .1)
                events.append({"palette_id": identity, "start": observed_start, "source_caption_id": caption.get("id"),
                               "shot_id": caption.get("shot_id"), "evidence": copy.deepcopy(links)[:1000], "source_status": status})
    aggregate_palette = aggregate.get("highlight_palette", [])
    if not isinstance(aggregate_palette, list):
        raise ValueError("aggregate highlight_palette must be a list")
    for item in aggregate_palette[:64]:
        if not isinstance(item, dict) or not isinstance(item.get("evidence", []), list) or not isinstance(item.get("source_caption_ids", []), list):
            raise ValueError("aggregate highlight palette requires object records with evidence/caption lists")
        if item.get("status") in OBSERVED_STATUSES and item.get("evidence"):
            identity = color_id(item["fill"], item.get("source_caption_ids", []), item["evidence"], item["status"])
            if identity and not any(event["palette_id"] == identity for event in events):
                matches = [caption for caption in captions if caption.get("id") in item.get("source_caption_ids", [])]
                if matches:
                    first = min(matches, key=lambda row: row.get("start", 0))
                    events.append({"palette_id": identity, "start": first["start"], "shot_id": first.get("shot_id"),
                                   "source_caption_id": first.get("id"), "evidence": copy.deepcopy(item["evidence"])[:1000], "source_status": item["status"]})
    shot_map = {shot.get("id"): shot for shot in shots if isinstance(shot, dict) and shot.get("id")}
    for event in events:
        shot = shot_map.get(event.get("shot_id"))
        same_shot = {item["palette_id"] for item in events if event.get("shot_id") and item.get("shot_id") == event["shot_id"]}
        if shot and len(same_shot) == 1:
            event["start"] = _number(shot["start"], "palette shot start", 0, duration)
            event["boundary_policy"] = "inferred shot boundary; consistent observed highlight color within shot"
        else:
            event["boundary_policy"] = "first observed color; hold until next observed regime"
    regimes = []
    for event in sorted(events, key=lambda row: row["start"]):
        if regimes and regimes[-1]["palette_id"] == event["palette_id"]:
            continue
        if len(regimes) >= 256:
            break
        regimes.append({**event, "id": f"highlight-regime-{len(regimes)+1}", "relative_start": event["start"]/duration,
                        "status": "inferred"})
        regimes[-1].pop("start")
    for index, regime in enumerate(regimes):
        regime["relative_end"] = regimes[index+1]["relative_start"] if index+1 < len(regimes) else 1.0
        regime["fill"] = next(row["fill"] for row in colors if row["id"] == regime["palette_id"])
    return variants, {"colors": colors, "regimes": regimes, "status": "inferred" if regimes else "unknown",
                      "method": "discrete observed palette; nearby RGB observations share first representative, never averaged",
                      "coverage": {"reference_captions": len(captions), "captions_examined": min(1000, len(captions)),
                                   "appearance_variants": len(variants), "appearance_variants_omitted": omitted_variants,
                                   "color_limit": 64, "regime_limit": 256},
                      "limits": "sparse appearance evidence; shot boundaries/gap extension and B word scheduling are inferred, not recovered word timestamps"}


def _relative_regime(regimes, progress):
    if not regimes:
        return None
    return next((regime for regime in reversed(regimes) if regime["relative_start"] <= progress), regimes[0])


def _apply_style_schedule(scenes, template, style, duration):
    variants = template.get("style_variants", [])
    palette = template.get("highlight_palette", {}).get("regimes", [])
    if not isinstance(variants, list) or len(variants) > 256 or not isinstance(palette, list) or len(palette) > 256:
        raise ValueError("style schedule exceeds 256 appearance/highlight regimes")
    variants = sorted(variants, key=lambda row: _number(row.get("relative_start"), "style relative start", 0, 1))
    palette = sorted(palette, key=lambda row: _number(row.get("relative_start"), "highlight relative start", 0, 1))
    for scene in scenes:
        for cue in scene["captions"]:
            progress = (scene["start"] + (cue["start"]+cue["end"])/2) / duration
            variant = _relative_regime(variants, progress)
            if variant:
                override = variant.get("style", {})
                if not isinstance(override, dict) or override.keys() - VARIANT_FIELDS:
                    raise ValueError("unsupported caption style override")
                merged = _validated_style({**style, **override})
                cue["style"] = {key: merged[key] for key in override}
                cue["style_variant_id"] = variant.get("id")
            for word in cue["words"]:
                if scene["accent_explicit"]:
                    word.update({"highlight": scene["accent"], "highlight_source": "explicit-content-accent"})
                    continue
                progress = (scene["start"] + (word["start"]+word["end"])/2) / duration
                regime = _relative_regime(palette, progress)
                if regime:
                    word.update({"highlight": _color(regime.get("fill"), style["highlight"]),
                                 "highlight_regime_id": regime.get("id"), "highlight_source": "new-word-midpoint-mapped-to-reference-relative-regime"})


def extract_template(analysis: dict, out_dir: Path | None = None) -> dict:
    """Turn measured/candidate analysis into a bounded reusable style contract."""
    if analysis.get("kind") != "rea-video-analysis" or analysis.get("schema_version") != 1:
        raise ValueError("expected schema_version 1 rea-video-analysis")
    source = analysis.get("source", {})
    width = _number(source.get("width"), "reference width", 1, 16384)
    height = _number(source.get("height"), "reference height", 1, 16384)
    captions = analysis.get("captions", [])
    measured_style = analysis.get("style", {})
    if not isinstance(captions, list) or not isinstance(measured_style, dict):
        raise ValueError("analysis captions/style have invalid shape")
    if any(not isinstance(caption, dict) or not isinstance(caption.get("style", {}), dict) for caption in captions):
        raise ValueError("analysis caption/style records must be objects")
    heights = [c["bbox"][3] for c in captions if isinstance(c.get("bbox"), list) and len(c["bbox"]) == 4]
    ys = [c["bbox"][1] + c["bbox"][3] / 2 for c in captions if isinstance(c.get("bbox"), list) and len(c["bbox"]) == 4]
    font_ratio = _style_value(captions, measured_style, "font_size_ratio", _median(heights, 0.065) / 1.2)
    font_ratio = min(0.16, max(0.025, _number(font_ratio, "font_size_ratio", 0.001, 1)))
    words = [len(re.findall(r"\S+", c.get("text", ""))) for c in captions if c.get("text")]
    shots = analysis.get("shots", [])
    lengths = [s.get("end", 0) - s.get("start", 0) for s in shots if s.get("end", 0) > s.get("start", 0)]
    entry = _style_value(captions, measured_style, "entry", None)
    observed_animation = _style_value(captions, measured_style, "animation", None)
    if entry is None:
        entry = {"scale_candidate": "pop", "static": "static"}.get(observed_animation, "static")
    if isinstance(entry, dict):
        entry = entry.get("family", "fade")
    unknowns = copy.deepcopy(analysis.get("unknowns", []))
    choices = []
    if observed_animation == "scale_candidate":
        choices.append({"field": "caption.entry", "status": "implementation_choice", "reason": "bounded pop approximates inferred scale candidate; original easing/keyframes are unknown"})
    elif observed_animation is None:
        choices.append({"field": "caption.entry", "status": "implementation_choice", "reason": "static entry because no observed animation family is available"})
    if entry not in SUPPORTED_ENTRIES:
        unknowns.append({"field": "caption.entry", "observed": entry, "reason": "unsupported entry family; explicit fade substitute"})
        entry = "fade"
    if not captions:
        choices.append({"field": "style", "status": "implementation_choice", "reason": "no observed text; default caption profile is not recovered typography"})
    choices.append({"field": "font", "status": "implementation_choice", "reason": "licensed bundled font substitutes any unverified original font"})
    shadow = _style_value(captions, measured_style, "shadow", None)
    if not isinstance(shadow, (list, tuple)):
        shadow = [0, 0, 0, 0]
        choices.append({"field": "caption.shadow", "status": "implementation_choice", "reason": "no shadow added because raster analysis did not identify one reliably"})
    position = _style_value(captions, measured_style, "position", None)
    if not isinstance(position, (list, tuple)) or len(position) != 2:
        xs = [c["bbox"][0] + c["bbox"][2] / 2 for c in captions if isinstance(c.get("bbox"), list) and len(c["bbox"]) == 4]
        position = [_median(xs, 0.5), _median(ys, 0.82)]
    line_ratio = _style_value(captions, measured_style, "line_height_ratio", None)
    line_height = min(2.0, max(1.0, _number(line_ratio, "line_height_ratio", 0.001, 1) / font_ratio)) if line_ratio is not None else 1.2
    choices.append({"field": "caption.line_height", "status": "implementation_choice", "reason": "bounded spacing derived from OCR box/font ratio; original baseline spacing is unverified"})
    if "highlight" not in measured_style:
        choices.append({"field": "caption.highlight", "status": "implementation_choice", "reason": "same as fill unless a highlight color is identified or content explicitly supplies accent"})
    transition = measured_style.get("transition", analysis.get("transition"))
    candidates = analysis.get("transitions", [])
    if transition is None:
        fades = [candidate for candidate in candidates if isinstance(candidate, dict) and candidate.get("type") == "fade_candidate"]
        if fades:
            span = _median([candidate.get("end", 0) - candidate.get("start", 0) for candidate in fades], .2)
            transition = {"family": "fade", "duration": max(0, span)}
            choices.append({"field": "transition", "status": "implementation_choice", "reason": "fade-through-black approximates raster fade candidates; original blend curve is unverified"})
        else:
            transition = {"family": "cut", "duration": 0}
            choices.append({"field": "transition", "status": "implementation_choice", "reason": "cut at detected shot boundaries; no supported transition family identified"})
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("type") not in {"fade_candidate", "cut"}:
            unknowns.append({"field": "transition", "observed": candidate.get("type"), "reason": "candidate preserved as evidence; native renderer has no verified equivalent"})
    if isinstance(transition, str):
        transition = {"family": transition, "duration": 0.2 if transition != "cut" else 0}
    if not isinstance(transition, dict):
        transition = {"family": "cut", "duration": 0}
    family = transition.get("family", transition.get("type", "cut"))
    if family not in SUPPORTED_TRANSITIONS:
        unknowns.append({"field": "transition", "observed": family, "reason": "unsupported transition family; cut substitute"})
        family = "cut"
    duration = min(0.8, _number(transition.get("duration", 0), "transition duration", 0, 60)) if family != "cut" else 0
    motion_records = analysis.get("motion", [])
    amplitude = measured_style.get("panzoom", 0)
    amplitude = max(-0.2, min(0.2, _number(amplitude, "panzoom", -2, 2)))
    motion_pattern = []
    for record in motion_records[:128] if isinstance(motion_records, list) else []:
        if not isinstance(record, dict):
            continue
        item = {"family": "static", "panzoom": 0, "scale_ratio": 1, "easing": "linear", "status": "implementation_choice", "shot_id": record.get("shot_id"), "evidence": record.get("evidence", [])}
        if record.get("status") in {"model-derived", "estimated"} and "scale_start" in record and "scale_end" in record and not record.get("coverage", {}).get("rejected_pairs", 0):
            first = _number(record["scale_start"], "scale_start", .01, 100)
            last = _number(record["scale_end"], "scale_end", .01, 100)
            ratio = max(.8, min(1.25, last / first))
            curve = record.get("curve", {})
            easing = curve.get("family") if curve.get("status") == "model-derived" else "linear"
            if easing not in {"constant", "linear", "ease-in-out"}:
                easing = "linear"
            if abs(ratio - 1) >= .005 and easing != "constant":
                item.update({"family": "panzoom", "scale_ratio": ratio, "panzoom": ratio-1, "easing": easing, "status": "inferred", "source_status": record["status"]})
                choices.append({"field": "motion", "status": "implementation_choice", "reason": "B applies the signed apparent scale ratio with bounded center crop; rotation/shear/translation and original keys remain separate observations", "shot_id": record.get("shot_id"), "unbounded_scale_ratio": last/first})
        motion_pattern.append(item)
    native_motion = {"family": "panzoom" if amplitude else "static", "panzoom": amplitude, "scale_ratio": 1+amplitude, "easing": "ease-in-out", "status": "implementation_choice"}
    if motion_pattern and not amplitude:
        native_motion.update(motion_pattern[0])
    if native_motion["family"] == "static" and motion_records:
        choices.append({"field": "motion", "status": "implementation_choice", "reason": "static B background where no continuous supported scale trajectory is available"})
    native_motion["pattern"] = motion_pattern
    native_motion["reference_candidates"] = [{key: record[key] for key in ("shot_id", "family", "direction", "displacement", "status", "evidence", "curve") if key in record} for record in motion_records[:128] if isinstance(record, dict)]
    template = {
        "schema_version": 1, "kind": "rea-video-style-template",
        "reference": {"sha256": source.get("sha256"), "width": width, "height": height, "duration": source.get("duration"), "content_policy": "analysis-only; never implicit render media"},
        "style": {
            "font_size_ratio": font_ratio,
            "fill": _color(_style_value(captions, measured_style, "fill", [255, 255, 255]), [255, 255, 255]),
            "stroke": _color(_style_value(captions, measured_style, "stroke", [0, 0, 0]), [0, 0, 0]),
            "stroke_width_ratio": min(0.012, _number(_style_value(captions, measured_style, "stroke_width_ratio", 0.003), "stroke width ratio", 0, 0.1)),
            "anchor": _style_value(captions, measured_style, "anchor", "bottom"),
            "anchor_x": min(0.95, max(0.05, _number(position[0], "position x", 0, 1))),
            "anchor_y": min(0.95, max(0.05, _number(position[1], "position y", 0, 1))),
            "max_width_ratio": min(0.94, max(0.4, _number(measured_style.get("max_width_ratio", 0.88), "max width ratio", 0.1, 1))),
            "box_color": _color(_style_value(captions, measured_style, "box_color", [0, 0, 0, 0]), [0, 0, 0, 0]),
            "shadow": _color(shadow, [0, 0, 0, 0]),
            "highlight": _color(measured_style.get("highlight"), _style_value(captions, measured_style, "fill", [255, 255, 255])),
            "entry": entry, "entry_duration": min(0.4, _number(measured_style.get("entry_duration", 0.18), "entry duration", 0, 2)),
            "words_per_group": min(12, max(1, round(_median(words, 5)))),
            "line_height": line_height,
        },
        "rhythm": {"median_shot_duration": _median(lengths, 3.0), "shot_duration_pattern": lengths[:64], "timing_policy": "relative", "transition": {"family": family, "duration": duration}, "source": "observed-shot-lengths" if lengths else "implementation_choice"},
        "motion": native_motion,
        "slots": [{"role": "scene", "repeatable": True, "fields": ["text", "asset", "duration", "background", "accent"]}, {"role": "audio", "required": False}],
        "invariants": ["caption treatment and anchor", "entry motion family", "transition family", "relative shot rhythm"],
        "degrees_of_freedom": ["new words and word durations", "new footage/images/colors", "line wrapping", "scene duration", "output canvas"],
        "evidence": [{"caption_id": c.get("id"), "evidence": c.get("evidence", c.get("evidence_refs", [])), "start": c.get("start"), "end": c.get("end")} for c in captions[:1000]],
        "implementation_choices": choices, "unknowns": unknowns, "transition_candidates": copy.deepcopy(candidates),
        "support": {"renderer": "native-pillow-ffmpeg-v1", "entries": sorted(SUPPORTED_ENTRIES), "transitions": sorted(SUPPORTED_TRANSITIONS), "font_recovery": "candidate/unknown; bundled font is an explicit substitute", "shaping": "complex-script rendering requires Pillow RAQM and suitable supplied font"},
    }
    template["style"] = _validated_style(template["style"])
    variants, palette = _style_regimes(captions, measured_style, shots, source.get("duration"), template["style"])
    template["style_variants"] = variants
    template["highlight_palette"] = palette
    if palette["colors"]:
        template["style"]["highlight"] = copy.deepcopy((palette["regimes"] or palette["colors"])[0]["fill"])
    template["style_schedule"] = {"method": "relative-reference-progress", "status": "implementation_choice",
                                  "typography": "choose observed appearance at each NEW cue midpoint; use first appearance before observed start and hold nearest earlier appearance through gaps",
                                  "highlight": "choose discrete palette at each NEW word midpoint; explicit scene accent overrides",
                                  "limits": "new content has new cue/word times; reference word timestamps are never copied; sparse regime boundaries remain inferred"}
    provenance = {}
    for output_name, source_name in {"font_size_ratio": "font_size_ratio", "fill": "fill", "stroke": "stroke",
                                     "stroke_width_ratio": "stroke_width_ratio", "anchor": "anchor", "anchor_x": "position",
                                     "anchor_y": "position", "line_height": "line_height_ratio", "entry": "animation",
                                     "box_color": "box_color", "shadow": "shadow", "highlight": "highlight"}.items():
        owner, caption_id = measured_style, None
        if source_name not in owner:
            owner, caption_id = next(((c.get("style", {}), c.get("id")) for c in captions if source_name in c.get("style", {})), ({}, None))
        status_name = {"stroke_width_ratio": "stroke_width_status"}.get(source_name, source_name + "_status")
        source_value = owner.get(source_name)
        source_status = source_value.get("status", "unknown") if isinstance(source_value, dict) else owner.get(status_name, owner.get("status", "unknown"))
        if source_value is None:
            source_status = "unknown" if source_name in owner else "implementation_choice"
        provenance[output_name] = {"status": source_status if source_name in owner else "implementation_choice",
                                   "source_field": source_name, "source_value": copy.deepcopy(owner.get(source_name)),
                                   "applied_value": copy.deepcopy(template["style"][output_name]), "caption_id": caption_id,
                                   "method": owner.get(source_name + "_method", owner.get("method", "analysis record; see implementation choices for substitutions"))}
    template["parameter_provenance"] = provenance
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        _write(out_dir / "style-template.json", template)
    return template


def _resolve_file(value, base, name):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"{name} must be a local file path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"{name} does not exist: {path}")
    if path.stat().st_size > 1024 * 1024 * 1024:
        raise ValueError(f"{name} exceeds 1 GiB")
    return path


def _copy_asset(path, target, role):
    digest = _digest(path)
    suffix = path.suffix.lower()
    relative = Path("assets") / f"{role}-{digest[:20]}{suffix}"
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and _digest(destination) != digest:
        raise ValueError("asset destination digest collision")
    if not destination.exists():
        shutil.copyfile(path, destination)
    return {"path": relative.as_posix(), "sha256": digest, "bytes": path.stat().st_size, "role": role, "origin": "new-content-supplied"}


def _font_path(content, base):
    if content.get("font"):
        return _resolve_file(content["font"], base, "font")
    for assets in (Path(__file__).resolve().parents[2] / "assets" / "fonts", Path(__file__).resolve().parent / "resources" / "fonts"):
        for name in ("BeVietnamPro-Bold.ttf", "BeVietnamPro-Regular.ttf"):
            if (assets / name).is_file():
                return assets / name
    raise ValueError("bundled font unavailable; provide content.font as a licensed local TTF/OTF")


def _check_glyphs(path, text):
    if any(unicodedata.bidirectional(char) in {"R", "AL"} for char in text):
        raise ValueError("native v1 does not support bidirectional captions; use an external shaping renderer")
    complex_script = any(0x0590 <= ord(char) <= 0x109F or 0x1780 <= ord(char) <= 0x18AF or 0xA800 <= ord(char) <= 0xABFF for char in text)
    if complex_script and not features.check_feature("raqm"):
        raise ValueError("complex-script captions require Pillow with RAQM shaping and a suitable font")
    try:
        font = ImageFont.truetype(str(path), 32)
    except OSError as exc:
        raise ValueError("font is not a usable TrueType/OpenType font") from exc
    unknown = font.getmask("\U0010ffff")
    signature = (unknown.size, bytes(unknown))
    missing = sorted(char for char in set(text) if not char.isspace() and (font.getmask(char).size, bytes(font.getmask(char))) == signature)
    if missing:
        raise ValueError("font lacks glyphs for: " + " ".join(repr(c) for c in missing[:20]))


def _word_cues(text, duration, max_group, supplied=None):
    words = re.findall(r"\S+", text)
    if not words:
        return []
    if supplied is not None:
        if not isinstance(supplied, list) or len(supplied) != len(words):
            raise ValueError("scene.words must contain one timing for every whitespace-delimited word")
        spans = []
        previous = 0.0
        for text_word, span in zip(words, supplied):
            if not isinstance(span, dict) or span.get("text", text_word) != text_word:
                raise ValueError("scene.words text differs from scene.text")
            start = _number(span.get("start"), "word start", 0, duration)
            end = _number(span.get("end"), "word end", start, duration)
            if end <= start or start < previous:
                raise ValueError("word windows must be ordered, non-overlapping, and nonempty")
            previous = end
            spans.append({"text": text_word, "start": start, "end": end, "timing": "model-derived-asr" if span.get("timing") == "model-derived-asr" else "user-supplied"})
    else:
        # New text receives new weighted timing; these are not audio alignments.
        weights = [max(1, len(w)) + (2 if w.endswith(('.', '!', '?', ',', ';', ':')) else 0) for w in words]
        total = sum(weights)
        cursor = 0.0
        spans = []
        for word, weight in zip(words, weights):
            end = cursor + duration * weight / total
            spans.append({"text": word, "start": cursor, "end": end, "timing": "estimated-from-new-text"})
            cursor = end
        spans[-1]["end"] = duration
    groups = []
    for index in range(0, len(spans), max_group):
        group = spans[index:index + max_group]
        groups.append({"text": " ".join(w["text"] for w in group), "start": group[0]["start"], "end": group[-1]["end"], "words": group})
    return groups


def compose(template: dict, content: dict, out_dir: Path) -> dict:
    """Bind NEW content to a style template and write a portable render project."""
    if template.get("kind") != "rea-video-style-template" or template.get("schema_version") != 1:
        raise ValueError("expected schema_version 1 rea-video-style-template")
    if content.get("kind") not in (None, "rea-video-content") or content.get("schema_version", 1) != 1:
        raise ValueError("expected schema_version 1 rea-video-content")
    raw_width = _number(content.get("width", 640), "width", 64, 3840)
    raw_height = _number(content.get("height", 360), "height", 64, 3840)
    if not raw_width.is_integer() or not raw_height.is_integer():
        raise ValueError("canvas dimensions must be integers")
    width, height = int(raw_width), int(raw_height)
    if width * height > MAX_PIXELS or width % 2 or height % 2:
        raise ValueError("canvas must have even dimensions and at most 3840x2160 pixels")
    fps = _number(content.get("fps", 30), "fps", 1, 60)
    scenes = content.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError(f"content.scenes must contain 1..{MAX_SCENES} scenes")
    base = Path(content.get("_base_dir", ".")).resolve()
    target = Path(out_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    if (target / "project.json").exists():
        raise ValueError("project.json already exists; use a new output directory")
    style = _validated_style(template.get("style", {}))
    # Resolve once at composition rather than silently fetching missing fonts at render time.
    font_path = _font_path(content, base)
    text_joined = " ".join(str(s.get("text", "")) for s in scenes if isinstance(s, dict))
    if len(text_joined) > 100000:
        raise ValueError("bound text exceeds 100,000 characters")
    _check_glyphs(font_path, unicodedata.normalize("NFC", text_joined))
    font = _copy_asset(font_path, target, "font")
    assets = [font]
    reference_hash = template.get("reference", {}).get("sha256")
    policy = content.get("timing_policy", "relative")
    if policy not in {"relative", "fixed", "audio-anchored"}:
        raise ValueError("timing_policy must be relative, fixed or audio-anchored")
    transition = copy.deepcopy(template.get("rhythm", {}).get("transition", {"family": "cut", "duration": 0}))
    transition_family = transition.get("family", "cut")
    if transition_family not in SUPPORTED_TRANSITIONS:
        raise ValueError(f"unsupported transition: {transition_family}")
    transition_duration = _number(transition.get("duration", 0), "transition duration", 0, 2)
    output_scenes = []
    portable_content = copy.deepcopy({k: v for k, v in content.items() if k != "_base_dir"})
    portable_content["font"] = font["path"]
    captions = []
    cursor = 0.0
    ids = set()
    groups = int(_number(style.get("words_per_group", 5), "words_per_group", 1, 12))
    rhythm = template.get("rhythm", {})
    pattern = rhythm.get("shot_duration_pattern") or [rhythm.get("median_shot_duration", 3)]
    if not isinstance(pattern, list) or not 1 <= len(pattern) <= 64:
        raise ValueError("shot duration pattern requires 1..64 values")
    pattern = [min(120, max(.1, _number(value, "observed shot duration", 0.001, MAX_DURATION))) for value in pattern]
    # Preserve relative observed pacing for unbound durations, uniformly stretching
    # the pattern if the new script needs more reading time. Explicit durations win.
    rhythm_scale = max([1.0] + [len(scene.get("text", "").split()) / 2.8 / pattern[index % len(pattern)]
                                for index, scene in enumerate(scenes)
                                if isinstance(scene, dict) and isinstance(scene.get("text", ""), str) and "duration" not in scene])
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError("every scene must be an object")
        scene_id = str(scene.get("id", f"scene-{index + 1}"))
        if scene_id in ids or len(scene_id) > 128:
            raise ValueError("scene IDs must be unique and at most 128 characters")
        ids.add(scene_id)
        text = scene.get("text", "")
        if not isinstance(text, str):
            raise ValueError("scene.text must be a string")
        text = unicodedata.normalize("NFC", text)
        if policy in {"fixed", "audio-anchored"} and "duration" not in scene:
            raise ValueError(f"{policy} scenes require explicit duration")
        default_duration = pattern[index % len(pattern)] * rhythm_scale
        duration = _number(scene.get("duration", default_duration), "scene duration", 0.1, 120)
        if policy == "audio-anchored" and text and "words" not in scene:
            raise ValueError("audio-anchored timing needs user-supplied scene.words; no aligner is implied")
        overlap = min(transition_duration, duration * 0.25, output_scenes[-1]["duration"] * 0.25) if index and transition_family != "cut" else 0
        if policy in {"fixed", "audio-anchored"}:
            overlap = 0  # preserve supplied time windows; no implicit clock contraction
        start = cursor - overlap
        end = start + duration
        asset_record = None
        if scene.get("asset") is not None:
            source = _resolve_file(scene["asset"], base, f"scene {scene_id} asset")
            asset_record = _copy_asset(source, target, "media")
            if asset_record["sha256"] == reference_hash and not content.get("allow_reference_reuse", False):
                raise ValueError("reference media cannot be reused without explicit allow_reference_reuse")
            if source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                asset_record["type"] = "image"
            elif source.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}:
                asset_record["type"] = "video"
            else:
                raise ValueError(f"unsupported asset format: {source.suffix}")
            assets.append(asset_record)
            portable_content["scenes"][index]["asset"] = asset_record["path"]
        cues = _word_cues(text, duration, groups, scene.get("words"))
        output_scenes.append({
            "id": scene_id, "start": start, "end": end, "duration": duration,
            "text": text, "title": str(scene.get("title", "")), "asset": asset_record,
            "background": _color(scene.get("background"), [17, 24, 39]),
            "accent": _color(scene.get("accent"), style.get("highlight", [255, 222, 89])),
            "accent_explicit": scene.get("accent") is not None,
            "asset_start": _number(scene.get("asset_start", 0), "asset_start", 0, MAX_DURATION),
            "video_end_policy": "hold-last",
            "motion": copy.deepcopy(template.get("motion", {}).get("pattern", [])[index % len(template["motion"]["pattern"])] if template.get("motion", {}).get("pattern") else template.get("motion", {"family": "static"})),
            "transition": {"family": transition_family if overlap else "cut", "duration": overlap},
            "captions": cues,
        })
        cursor = end
    if cursor > MAX_DURATION or math.ceil(cursor * fps) > MAX_FRAMES:
        raise ValueError("project exceeds 600 seconds or 36,000 frames")
    _apply_style_schedule(output_scenes, template, style, cursor)
    for scene in output_scenes:
        for cue in scene["captions"]:
            captions.append({"id": f"{scene['id']}-caption-{len(captions) + 1}", "scene_id": scene["id"], "text": cue["text"],
                             "start": scene["start"] + cue["start"], "end": scene["start"] + cue["end"], "timing": cue["words"][0]["timing"],
                             "words": [{**word, "start": scene["start"] + word["start"], "end": scene["start"] + word["end"]} for word in cue["words"]],
                             **{key: copy.deepcopy(cue[key]) for key in ("style", "style_variant_id") if key in cue}})
    audio = None
    if content.get("audio"):
        audio = _copy_asset(_resolve_file(content["audio"], base, "audio"), target, "audio")
        if audio["sha256"] == reference_hash and not content.get("allow_reference_reuse", False):
            raise ValueError("reference audio requires explicit allow_reference_reuse")
        audio["offset"] = _number(content.get("audio_offset", 0), "audio_offset", -MAX_DURATION, MAX_DURATION)
        assets.append(audio)
        portable_content["audio"] = audio["path"]
    project = {
        "schema_version": 1, "kind": "rea-video-project",
        "render": {"width": width, "height": height, "fps": fps, "duration": cursor, "frame_count": math.ceil(cursor * fps), "encoder": "libx264", "pixel_format": "yuv420p"},
        "style": style, "motion": copy.deepcopy(template.get("motion", {"family": "static"})),
        "style_schedule": copy.deepcopy(template.get("style_schedule", {})), "highlight_palette": copy.deepcopy(template.get("highlight_palette", {})),
        "scenes": output_scenes, "captions": captions, "font": font, "audio": audio, "assets": assets,
        "timing_policy": policy, "reference": copy.deepcopy(template.get("reference", {})),
        "template_sha256": hashlib.sha256(json.dumps(template, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "content_sha256": hashlib.sha256(json.dumps({k: v for k, v in content.items() if k != "_base_dir"}, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "provenance": {"content": "explicit-new-content-bindings", "reference_media_reused": any(a["sha256"] == reference_hash for a in assets), "reference_reuse_authorized": bool(content.get("allow_reference_reuse", False)), "reference_path_included": False},
        "speech_provenance": copy.deepcopy(content.get("speech_provenance")),
        "limits": {"caption_timing": "character-weighted estimates unless scene.words supplied; not ASR alignment", "shaping": "complex scripts require Pillow RAQM and a suitable supplied font; missing glyphs rejected", "video_audio": "muted; supply an explicit audio binding", "video_end": "hold final decoded frame if asset is shorter than scene", "effects": "2D static/panzoom plus caption static/fade/pop/slide and cut/dissolve/fade/wipe subset", "footage_geometry": "square pixels; rotated or anamorphic footage is rejected; prepare upright square-pixel media first"},
    }
    _write(target / "project.json", project)
    _write(target / "style-template.json", template)
    _write(target / "content-bindings.json", portable_content)
    _write(target / "timeline.json", {"schema_version": 1, "kind": "rea-video-resolved-timeline", "duration": cursor, "scenes": output_scenes, "captions": captions})
    return project
