"""Strict new-speech binding rejects mismatches instead of inventing alignment."""
import copy

import pytest

from rea_video_pro_max.core import sha256
from rea_video_pro_max.timing import bind_speech


@pytest.fixture
def profile(tmp_path):
    audio = tmp_path / "new.wav"
    audio.write_bytes(b"owned-new-audio-identity")
    content = {"schema_version": 1, "kind": "rea-video-content", "audio": "new.wav",
               "scenes": [{"text": "A fresh idea."}, {"text": "Build it today!"}]}
    words = ["A", "fresh", "idea.", "Build", "it", "today!"]
    transcript = {"kind": "rea-video-transcript", "channel": "audio-speech-asr",
                  "source": {"sha256": sha256(audio)}, "coverage": {"end": 4, "partial": False, "gaps": []},
                  "words": [{"text": w, "start": i*.5, "end": (i+1)*.5} for i,w in enumerate(words)]}
    return content, transcript, tmp_path


def test_strict_new_script_binding_preserves_absolute_clock(profile):
    content, transcript, root = profile
    result = bind_speech(content, transcript, root)
    assert result["timing_policy"] == "audio-anchored"
    assert [s["duration"] for s in result["scenes"]] == [1.5, 2.5]
    assert result["scenes"][1]["words"][0]["start"] == 0
    assert result["scenes"][1]["words"][-1]["end"] == 1.5
    assert result["speech_provenance"]["status"] == "model-derived"
    assert "words" not in content["scenes"][0]


@pytest.mark.parametrize("mutation", ["wrong-asset", "wrong-order", "missing-word", "zero-word", "partial", "gap", "offset"])
def test_mismatched_or_ambiguous_speech_rejected(profile, mutation):
    content, transcript, root = copy.deepcopy(profile)
    if mutation == "wrong-asset":
        transcript["source"]["sha256"] = "0"*64
    elif mutation == "wrong-order":
        transcript["words"][0]["text"] = "fresh"
    elif mutation == "missing-word":
        transcript["words"].pop()
    elif mutation == "zero-word":
        transcript["words"][0]["end"] = 0
    elif mutation == "partial":
        transcript["coverage"]["partial"] = True
    elif mutation == "gap":
        transcript["coverage"]["gaps"] = [{"start": 1, "end": 2}]
    else:
        content["audio_offset"] = 1
    with pytest.raises(ValueError):
        bind_speech(content, transcript, root)
