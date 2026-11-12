"""Truth-preserving analysis interchange; editor tracks are annotations, not recovered sources."""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

from .core import sha256, validate, write_json


def _stamp(seconds: float, *, vtt: bool = False) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    sec, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{sec:02}{'.' if vtt else ','}{millis:03}"


def _cue_text(text: str) -> str:
    # Subtitle formats cannot carry arbitrary blank-line blocks as one cue.
    return "\n".join(line.strip() for line in str(text).replace("\r", "").splitlines() if line.strip())


def _cell(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r")) else value


def _rate(analysis: dict) -> Fraction:
    source = analysis["source"]
    raw = source.get("fps", 30)
    if isinstance(raw, dict):
        raw = raw.get("num", 30) / max(1, raw.get("den", 1))
    try:
        rate = Fraction(str(raw)).limit_denominator(1001)
        if rate <= 0 or rate > 240:
            raise ValueError("Invalid frame rate")
        return rate
    except (ValueError, ZeroDivisionError, TypeError) as error:
        raise ValueError("Export needs a valid presentation frame rate") from error


def native_timeline(analysis: dict) -> dict:
    validate(analysis, "rea-video-analysis")
    return {"schema_version": 1, "kind": "rea-video-timeline", "source": analysis["source"],
            "time_convention": "[start,end), seconds mapped to original PTS in evidence",
            "tracks": [{"id": "V1", "role": "flattened-reference-shot-slices", "clips": analysis["shots"]},
                       {"id": "T1", "role": "observed-text-annotations", "clips": analysis.get("captions", [])},
                       {"id": "T2", "role": "scene-and-ambiguous-text-observations", "clips": analysis.get("text_regions", [])},
                       {"id": "M1", "role": "estimated-motion", "clips": analysis.get("motion", [])}],
            "audio": analysis.get("audio", {}), "coverage": analysis.get("coverage", {}),
            "unknowns": analysis.get("unknowns", []),
            "notice": "Reference ranges and annotations; not separated original footage/layers."}


def export_analysis(analysis: dict, out_dir: str | Path, format: str = "native") -> dict:
    validate(analysis, "rea-video-analysis")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    losses = []
    captions = analysis.get("captions", [])
    shots = analysis["shots"]
    if analysis["source"]["duration"] <= 0 and format in {"srt", "vtt", "ass", "edl", "otio"}:
        raise ValueError("Timed subtitle/editor exports require video duration; use native JSON for a still image")
    if format == "native":
        path = write_json(out / "timeline.json", native_timeline(analysis))
    elif format == "csv":
        path = out / "shots.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["id", "start_seconds", "end_seconds", "source_sha256", "type"])
            for shot in shots:
                # Protect spreadsheets from formula execution by untrusted labels.
                label = _cell(shot.get("id", ""))
                writer.writerow([label, shot["start"], shot["end"], analysis["source"]["sha256"],
                                 _cell(shot.get("transition", shot.get("type", "shot")))])
        losses = ["Hierarchy, motion, style, audio and uncertainty are retained in native JSON only."]
    elif format in {"srt", "vtt"}:
        path = out / f"subtitles.{format}"
        parts = ["WEBVTT\n"] if format == "vtt" else []
        for i, cue in enumerate(captions, 1):
            text = _cue_text(cue.get("text", ""))
            # Plain subtitles: text cannot inject WebVTT markup.
            if format == "vtt":
                text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f"{i}\n{_stamp(cue['start'], vtt=format=='vtt')} --> "
                         f"{_stamp(cue['end'], vtt=format=='vtt')}\n{text}\n")
        path.write_text("\n".join(parts), encoding="utf-8")
        losses = ["Text/visible cue times only; typography, effects and evidence stay in JSON.",
                  "Timestamps rounded to milliseconds."]
    elif format == "ass":
        path = out / "overlays.ass"
        width, height = analysis["source"]["width"], analysis["source"]["height"]
        style = analysis.get("style", {})
        size = max(12, round(style.get("font_size_ratio", .065) * height))
        lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
                 "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                 "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
                 "Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
                 f"Style: Default,Be Vietnam Pro,{size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,"
                 "-1,0,0,0,100,100,0,0,1,2,1,2,20,20,24,1", "[Events]",
                 "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        def ass_time(t):
            cs = max(0, round(t * 100))
            h, cs = divmod(cs, 360000)
            m, cs = divmod(cs, 6000)
            sec, cs = divmod(cs, 100)
            return f"{h}:{m:02}:{sec:02}.{cs:02}"
        for cue in captions:
            text = _cue_text(cue.get("text", "")).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            text = text.replace("\n", "\\N")
            lines.append(f"Dialogue: 0,{ass_time(cue['start'])},{ass_time(cue['end'])},Default,,0,0,0,,{text}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        losses = ["ASS is a caption timing export with explicit Be Vietnam Pro substitute style.",
                  "Font identity/effects/word highlight are not recovered by this adapter.",
                  "Timestamps rounded to centiseconds; native style evidence stays in JSON."]
    elif format == "otio":
        try:
            import opentimelineio as otio
        except ImportError as error:
            raise ValueError("OTIO export requires: pip install 'rea-video-pro-max[interop]'") from error
        rate = float(_rate(analysis))
        timeline = otio.schema.Timeline(name="REA inferred edit timeline")
        track = otio.schema.Track(name="Observed reference ranges", kind="Video")
        source = analysis["source"]
        for shot in shots:
            span = otio.opentime.TimeRange(otio.opentime.RationalTime(shot["start"] * rate, rate),
                                           otio.opentime.RationalTime((shot["end"] - shot["start"]) * rate, rate))
            reference = otio.schema.ExternalReference(target_url=Path(source["path"]).resolve().as_uri())
            clip = otio.schema.Clip(name=shot["id"], source_range=span, media_reference=reference)
            clip.metadata["rea_video"] = {"source_sha256": source["sha256"], "role": "flattened-reference",
                                         "analysis": json.dumps(shot, ensure_ascii=False)}
            track.append(clip)
        timeline.tracks.append(track)
        timeline.metadata["rea_video"] = {"unknowns": json.dumps(analysis.get("unknowns", [])),
                                          "annotations": json.dumps(captions, ensure_ascii=False)}
        path = out / "timeline.otio"
        otio.adapters.write_to_file(timeline, str(path))
        reread = otio.adapters.read_from_file(str(path))
        if len(list(reread.find_clips())) != len(shots):
            raise RuntimeError("OTIO readback did not preserve clip count")
        losses = ["Flattened reference slices; original layer/source assets remain unknown.",
                  "Caption/effect hypotheses are metadata, not editable NLE effect nodes.",
                  "OTIO uses the declared nominal rate; original per-frame PTS/coverage remains in native analysis.",
                  "OTIO reader round-trip checked; specific NLE import is not certified."]
    elif format == "edl":
        rate = _rate(analysis)
        clock = analysis["source"].get("presentation_clock", {})
        if rate.denominator != 1 or clock.get("status") != "measured" or clock.get("variable_intervals") is not False:
            raise ValueError("EDL supports tested integer CFR only; use native/OTIO for fractional/VFR timing")
        fps = int(rate)
        def tc(t):
            frames = round(t * fps)
            h, frames = divmod(frames, 3600 * fps)
            m, frames = divmod(frames, 60 * fps)
            sec, frames = divmod(frames, fps)
            return f"{h:02}:{m:02}:{sec:02}:{frames:02}"
        lines = ["TITLE: REA OBSERVED EDIT", "FCM: NON-DROP FRAME", ""]
        for i, shot in enumerate(shots, 1):
            lines += [f"{i:03}  AX       V     C        {tc(shot['start'])} {tc(shot['end'])} "
                      f"{tc(shot['start'])} {tc(shot['end'])}", f"* FROM CLIP NAME: {Path(analysis['source']['path']).name}"]
        path = out / "timeline.edl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        losses = ["Integer-CFR cut list only; no layer/transition/effect semantics. Frame-rounded times.",
                  "Reference slices, not original camera source in/out."]
    elif format == "fcpxml":
        raise ValueError("FCPXML not certified in this release; native/OTIO preserve declared semantics")
    else:
        raise ValueError(f"Unsupported export format: {format}")
    receipt = {"schema_version": 1, "kind": "rea-video-export-receipt", "format": format,
               "file": path.name, "source_sha256": analysis["source"]["sha256"],
               "sha256": sha256(path),
               "losses": losses, "caption_count": len(captions), "shot_count": len(shots)}
    write_json(out / f"{format}-receipt.json", receipt)
    return receipt
