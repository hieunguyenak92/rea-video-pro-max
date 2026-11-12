"""Local ASR admission, PTS/sample clocks, deadline and real-provider acceptance."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
import pytest

from rea_video_pro_max.asr import _decode, _model_files, transcribe
from rea_video_pro_max.core import sha256


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / "owned.wav"
    rate = 16000
    values = (np.sin(np.arange(rate) * 2 * np.pi * 440 / rate) * 16000).astype("<i2")
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(values.tobytes())
    return path


@pytest.fixture
def model(tmp_path):
    path = tmp_path / "local-model"
    path.mkdir()
    (path / "config.json").write_text("{}")
    (path / "tokenizer.json").write_text("{}")
    (path / "vocabulary.txt").write_text("test")
    (path / "model.bin").write_bytes(b"model-data-fixture")
    return path


def test_complete_local_model_required_no_tokenizer_fallback(model):
    assert {p.name for p in _model_files(model)} == {"model.bin", "config.json", "tokenizer.json", "vocabulary.txt"}
    (model / "tokenizer.json").unlink()
    with pytest.raises(ValueError, match="no fallback download"):
        _model_files(model)


def test_model_file_symlinks_rejected(model, tmp_path):
    external = tmp_path / "outside-tokenizer.json"
    external.write_text("{}")
    (model / "tokenizer.json").unlink()
    (model / "tokenizer.json").symlink_to(external)
    with pytest.raises(ValueError, match="non-symlinked"):
        _model_files(model)


def test_adjacent_model_code_is_not_loaded(audio, model, tmp_path):
    marker = tmp_path / "must-not-exist"
    (model / "sitecustomize.py").write_text(f"from pathlib import Path; Path({str(marker)!r}).write_text('executed')")
    (model / "__init__.py").write_text(f"from pathlib import Path; Path({str(marker)!r}).write_text('executed')")
    # Invalid model data fails inside the installed provider, without loading any model-adjacent Python.
    with pytest.raises(RuntimeError, match="local ASR failed"):
        transcribe(audio, model, max_seconds=1, timeout_seconds=10)
    assert not marker.exists()


@pytest.mark.parametrize("url", ["https://example.com/video.mp4", "http://localhost/a.wav", "file:///etc/passwd"])
def test_remote_protocols_rejected(url, model):
    with pytest.raises(ValueError, match="local paths"):
        transcribe(url, model)


@pytest.mark.parametrize("settings", [{"max_seconds": 0}, {"max_seconds": 1801}, {"max_seconds": float("nan")},
                                       {"timeout_seconds": 0}, {"cpu_threads": 2.5}, {"cpu_threads": 100},
                                       {"language": "english"}, {"compute_type": "cuda"}])
def test_invalid_runtime_budgets_fail_before_inference(audio, model, settings):
    with pytest.raises(ValueError):
        transcribe(audio, model, **settings)


def test_disguised_hls_media_is_rejected_without_external_access(tmp_path):
    source = tmp_path / "looks-local.mp4"
    source.write_text("#EXTM3U\n#EXT-X-TARGETDURATION:1\n#EXTINF:1,\nsecret-outside.ts\n#EXT-X-ENDLIST\n")
    with pytest.raises(ValueError, match="permitted flat"):
        _decode(source, 1)


def test_decode_sample_hash_and_partial_coverage(audio):
    before = sha256(audio)
    values, coverage = _decode(audio, .35)
    assert len(values) == 5600
    assert coverage["partial"] is True
    assert coverage["end"] == .35
    assert coverage["samples"] == coverage["observed_samples"] == 5600
    assert coverage["sample_sha256"] == hashlib.sha256(values.astype("<f4").tobytes()).hexdigest()
    assert coverage["first_audio_pts"] == 0 and coverage["sample_rate"] == 16000
    assert sha256(audio) == before


def test_audio_offset_keeps_video_clock_and_explicit_padding(audio, tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required to construct owned audio-offset fixture")
    media = tmp_path / "offset.mkv"
    command = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=96x64:r=10:d=1.5",
               "-itsoffset", "0.5", "-i", str(audio), "-c:v", "libx264", "-c:a", "pcm_s16le", str(media)]
    subprocess.run(command, capture_output=True, timeout=10, check=True)
    samples, coverage = _decode(media, 2)
    assert coverage["clock_origin_method"] == "video stream reported start PTS"
    assert coverage["first_audio_seconds"] == pytest.approx(.5, abs=.002)
    assert coverage["gaps"][0]["start"] == 0
    assert coverage["gaps"][0]["end"] == pytest.approx(.5, abs=.002)
    assert np.max(np.abs(samples[:7000])) == 0
    assert np.sqrt(np.mean(samples[9000:12000] ** 2)) > .1


def test_no_audio_stream_is_an_actionable_error(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required")
    path = tmp_path / "silent-video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=96x64:r=10:d=0.2",
                    "-c:v", "libx264", str(path)], capture_output=True, timeout=10, check=True)
    with pytest.raises(ValueError, match="no audio stream"):
        _decode(path, 1)


def test_deadline_stops_worker_and_preserves_output(audio, model, tmp_path):
    output = tmp_path / "result.json"
    output.write_text("existing output")
    with pytest.raises(RuntimeError, match="deadline"):
        transcribe(audio, model, output, timeout_seconds=.01)
    assert output.read_text() == "existing output"


def test_output_cannot_overwrite_inputs(audio, model):
    with pytest.raises(ValueError, match="overwrite"):
        transcribe(audio, model, audio)
    with pytest.raises(ValueError, match="overwrite"):
        transcribe(audio, model, model / "result.json")


def _real_profile():
    model = os.environ.get("REA_VIDEO_ASR_MODEL")
    fixture = os.environ.get("REA_VIDEO_ASR_FIXTURE")
    if not model or not fixture:
        pytest.skip("set REA_VIDEO_ASR_MODEL and REA_VIDEO_ASR_FIXTURE for actual local-provider acceptance")
    return Path(model), Path(fixture)


def test_real_provider_owned_english_speech(tmp_path):
    model, fixture = _real_profile()
    pytest.importorskip("faster_whisper")
    before = sha256(fixture)
    result = transcribe(fixture, model, tmp_path / "speech.json", language="en", max_seconds=30, timeout_seconds=60)
    expected = "a fresh story begins today we turn new ideas into clear video timelines".split()
    observed = re.findall(r"[a-z]+", result["text"].casefold())
    assert observed == expected
    assert len(result["words"]) == 13
    assert result["channel"] == "audio-speech-asr"
    assert result["provider"]["device"] == "cpu"
    assert result["provider"]["compute_type"] == "int8"
    assert result["coverage"]["partial"] is False
    assert result["language"]["detected"] == "en"
    assert result["language"]["status"] == "model-derived"
    assert result["source"]["sha256"] == before == sha256(fixture)
    assert all(word["status"] == "model-derived" and 0 <= word["start"] <= word["end"] <= result["coverage"]["end"] + .1
               for word in result["words"])
    assert json.loads((tmp_path / "speech.json").read_text())["coverage"]["sample_sha256"] == result["coverage"]["sample_sha256"]


def test_real_english_only_model_rejects_other_language():
    model, fixture = _real_profile()
    with pytest.raises(RuntimeError, match="English-only"):
        transcribe(fixture, model, language="vi", max_seconds=10, timeout_seconds=60)
