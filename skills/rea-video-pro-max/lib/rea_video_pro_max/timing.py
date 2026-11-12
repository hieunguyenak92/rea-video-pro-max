"""Bind new speech observations only when the exact new script/asset matches."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from .core import bounded_number, confined, sha256, validate


def _normalized(word):
    return "".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFC", word).casefold()))


def bind_speech(content: dict, transcript: dict, base_dir: str | Path, *, workspace=None) -> dict:
    """Strict matching, not forced alignment or correction of a mismatched script."""
    validate(content, "rea-video-content")
    if transcript.get("kind") != "rea-video-transcript" or transcript.get("channel") != "audio-speech-asr":
        raise ValueError("Expected a local ASR transcript artifact")
    result = copy.deepcopy(content)
    base = Path(base_dir).resolve()
    if not isinstance(content.get("audio"), str) or content.get("audio_offset", 0) != 0:
        raise ValueError("Speech binding needs explicit new audio and zero audio_offset")
    audio = (base / content["audio"]).resolve(strict=True)
    if workspace:
        confined(workspace, audio, must_exist=True)
        for scene in content["scenes"]:
            if scene.get("asset"):
                confined(workspace, base / scene["asset"], must_exist=True)
        if content.get("font"):
            confined(workspace, base / content["font"], must_exist=True)
    if sha256(audio) != transcript.get("source", {}).get("sha256"):
        raise ValueError("Transcript source does not match the bound new audio bytes")
    coverage = transcript.get("coverage", {})
    if coverage.get("partial") or coverage.get("gaps"):
        raise ValueError("Speech binding requires complete audio coverage without missing-sample gaps")
    duration = bounded_number(coverage.get("end"), "speech duration", .1, 600)
    if abs(coverage.get("first_audio_seconds", 0)-coverage.get("clock_origin_seconds", 0)) > 1/16000:
        raise ValueError("New audio and video clock origins differ; prepare an aligned audio file or supply reviewed word windows")
    words = transcript.get("words", [])
    if not isinstance(words, list) or not words:
        raise ValueError("Transcript has no timed speech words")
    flattened = [word for scene in result["scenes"] for word in scene.get("text", "").split()]
    if len(flattened) != len(words) or any(not isinstance(w, dict) or _normalized(t) != _normalized(w.get("text", "")) for t, w in zip(flattened, words)):
        raise ValueError("New script differs from ASR word sequence; review/correct transcription or supply independently aligned word windows")
    previous = 0
    for word in words:
        start = bounded_number(word.get("start"), "word start", previous, duration)
        end = bounded_number(word.get("end"), "word end", start, duration)
        if end <= start:
            raise ValueError("Zero-duration ASR words need review; they cannot be silently retimed")
        previous = end
    cursor, word_index = 0.0, 0
    for index, scene in enumerate(result["scenes"]):
        texts = scene.get("text", "").split()
        if not texts:
            raise ValueError("Every audio-bound scene requires spoken text")
        selected = words[word_index:word_index+len(texts)]
        word_index += len(texts)
        end = words[word_index]["start"] if word_index < len(words) else duration
        if end-cursor < .1:
            raise ValueError("Speech scene is shorter than native renderer minimum; merge scenes")
        scene["duration"] = end-cursor
        scene["words"] = [{"text": text, "start": word["start"]-cursor, "end": word["end"]-cursor,
                           "timing": "model-derived-asr"} for text,word in zip(texts,selected)]
        scene["word_timing_origin"] = {"status": "model-derived", "method": "strict-script-match-to-new-audio-ASR", "scene_index": index}
        cursor = end
    result["timing_policy"] = "audio-anchored"
    result["speech_provenance"] = {"transcript_sha256": hashlib.sha256(json.dumps(transcript,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                                    "source_sha256": transcript["source"]["sha256"], "provider": transcript.get("provider", {}),
                                    "status": "model-derived", "method": "strict-word-sequence-binding", "limits": "ASR timing is approximate, not forced alignment; matching text does not certify spoken-word boundaries"}
    return result
