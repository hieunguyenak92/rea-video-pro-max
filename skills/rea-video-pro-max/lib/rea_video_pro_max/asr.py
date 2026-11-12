"""Optional offline ASR with explicit CTranslate2 model files and bounded execution.

Speech observations remain a separate, model-derived channel from visible OCR.
No model names, downloads, remote protocols or model-adjacent code are executed.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import av
import numpy as np

from .core import bounded_number, read_json, sha256, write_json

SAMPLE_RATE = 16000
MAX_SECONDS = 1800
MAX_SOURCE_BYTES = 8 * 1024**3
MAX_MODEL_BYTES = 2 * 1024**3
MEDIA_FORMATS = "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,avi,mpeg,mpegts,ogg,flv,asf,mxf,nut,wav,mp3,flac,aac,aiff,ac3,au"


def _local(value, *, directory=False):
    if not isinstance(value, (str, Path)) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(value)):
        raise ValueError("ASR accepts explicit local paths only; URLs/model IDs are not supported")
    path = Path(value).expanduser().resolve(strict=True)
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError("model must be a directory" if directory else "source must be a regular file")
    return path


def _model_files(model):
    required = ["model.bin", "config.json", "tokenizer.json"]
    vocabulary = "vocabulary.txt" if (model / "vocabulary.txt").is_file() else "vocabulary.json"
    required.append(vocabulary)
    optional = [name for name in ["preprocessor_config.json"] if (model / name).exists()]
    files, total = [], 0
    for name in required + optional:
        path = model / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(model):
            raise ValueError(f"complete local model requires regular, non-symlinked {name}; no fallback download")
        size = path.stat().st_size
        if not size or size > (MAX_MODEL_BYTES if name == "model.bin" else 16 * 1024**2):
            raise ValueError("local model file is empty or exceeds the model-file budget")
        total += size
        if total > MAX_MODEL_BYTES:
            raise ValueError("local model exceeds the 2 GiB profile budget")
        if name in {"config.json", "tokenizer.json", "preprocessor_config.json"}:
            read_json(path)
        files.append(path)
    return files


def _decode(source, maximum):
    maximum_samples = math.ceil(maximum * SAMPLE_RATE)
    chunks, gaps = [], []
    cursor = observed_samples = 0
    first_pts = first_time_base = first_seconds = origin = None
    clock_method = "first decoded audio presentation timestamp"
    partial = False
    try:
        with av.open(str(source), options={"protocol_whitelist": "file,pipe", "format_whitelist": MEDIA_FORMATS}) as container:
            if not container.streams.audio:
                raise ValueError("source has no audio stream")
            stream = container.streams.audio[0]
            if len(stream.layout.channels) > 8 or (stream.codec_context.sample_rate or 0) > 192000:
                raise ValueError("audio source exceeds 8-channel/192 kHz decode profile")
            videos = [s for s in container.streams.video if not (int(s.disposition) & 0x400)]
            if videos:
                video = max(videos, key=lambda s: s.width * s.height)
                if video.start_time is not None and video.time_base is not None:
                    origin = float(video.start_time * video.time_base)
                    clock_method = "video stream reported start PTS"
            resampler = av.AudioResampler(format="fltp", layout="mono", rate=SAMPLE_RATE)
            missing_pts = 0
            def append(chunk):
                nonlocal cursor, observed_samples, partial, missing_pts
                data = chunk.to_ndarray().reshape(-1).astype(np.float32)
                if not np.all(np.isfinite(data)):
                    raise ValueError("audio contains non-finite decoded samples")
                if chunk.pts is None or chunk.time_base is None:
                    position = cursor
                    missing_pts += 1
                else:
                    position = round((float(chunk.pts * chunk.time_base) - origin) * SAMPLE_RATE)
                if position < cursor:
                    data = data[min(len(data), cursor - position):]
                    position = cursor
                if position > cursor:
                    gap_end = min(position, maximum_samples)
                    if gap_end > cursor:
                        gaps.append({"start": cursor / SAMPLE_RATE, "end": gap_end / SAMPLE_RATE,
                                     "status": "measured", "interpretation": "no decoded samples; zero padding preserves source clock"})
                        chunks.append(np.zeros(gap_end - cursor, dtype=np.float32))
                        cursor = gap_end
                if position >= maximum_samples:
                    partial = True
                    return
                remaining = maximum_samples - cursor
                if len(data) > remaining:
                    partial = True
                data = data[:remaining]
                if len(data):
                    chunks.append(data)
                    cursor += len(data)
                    observed_samples += len(data)
            for frame in container.decode(stream):
                if first_seconds is None:
                    first_pts = frame.pts
                    first_time_base = str(frame.time_base) if frame.time_base else None
                    first_seconds = float(frame.pts * frame.time_base) if frame.pts is not None and frame.time_base else 0.0
                    if origin is None:
                        origin = first_seconds
                if frame.samples > 192000 * 10:
                    raise ValueError("decoded audio frame exceeds 10-second sample budget")
                for chunk in resampler.resample(frame):
                    append(chunk)
                if partial or cursor >= maximum_samples:
                    partial = True
                    break
            if not partial:
                for chunk in resampler.resample(None):
                    append(chunk)
            stream_index = stream.index
    except av.error.FFmpegError as error:
        raise ValueError("source is unreadable or is not a permitted flat local audio/video format") from error
    if not observed_samples:
        raise ValueError("no audio samples inside the requested source-clock window")
    samples = np.concatenate(chunks).astype("<f4", copy=False)
    return samples, {"stream_index": stream_index, "first_audio_pts": first_pts, "first_audio_time_base": first_time_base,
                     "first_audio_seconds": first_seconds, "clock_origin_seconds": origin, "clock_origin_method": clock_method,
                     "sample_rate": SAMPLE_RATE, "samples": len(samples), "observed_samples": observed_samples,
                     "sample_sha256": hashlib.sha256(samples.tobytes()).hexdigest(), "sample_format": "little-endian float32 mono",
                     "start": 0, "end": len(samples) / SAMPLE_RATE, "partial": partial,
                     "max_seconds": maximum, "gaps": gaps[:500], "resampled_chunks_missing_pts": missing_pts}


def _run(request):
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError("Local ASR requires pip install 'rea-video-pro-max[asr]' (faster-whisper)") from error
    source = _local(request["source"])
    model_dir = _local(request["model_dir"], directory=True)
    model_files = _model_files(model_dir)
    source_before = sha256(source)
    inventory = [{"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)} for path in model_files]
    samples, coverage = _decode(source, request["max_seconds"])
    model = WhisperModel(str(model_dir), device="cpu", compute_type=request["compute_type"], cpu_threads=request["cpu_threads"],
                         num_workers=1, local_files_only=True)
    if not model.model.is_multilingual and request["language"] not in (None, "en"):
        raise ValueError("selected local model is English-only; it cannot verify another language")
    segments, info = model.transcribe(samples, language=request["language"], task="transcribe", beam_size=5,
                                     temperature=0.0, word_timestamps=True, condition_on_previous_text=False,
                                     vad_filter=False, max_new_tokens=224, log_progress=False)
    result_segments, result_words = [], []
    for segment in segments:
        if len(result_segments) >= 10000:
            raise RuntimeError("ASR exceeds the 10,000-segment result budget")
        start = bounded_number(segment.start, "model segment start", 0, coverage["end"] + .1)
        end = bounded_number(segment.end, "model segment end", start, coverage["end"] + .1)
        words = []
        for word in segment.words or []:
            if len(result_words) >= 100000:
                raise RuntimeError("ASR exceeds the 100,000-word result budget")
            wstart = bounded_number(word.start, "model word start", 0, coverage["end"] + .1)
            wend = bounded_number(word.end, "model word end", wstart, coverage["end"] + .1)
            item = {"text": word.word.strip(), "start": wstart, "end": wend,
                    "status": "model-derived", "method": "whisper-cross-attention-word-timestamps",
                    "model_probability": float(word.probability), "zero_duration": wstart == wend}
            words.append(item)
            result_words.append(item)
        result_segments.append({"id": f"speech-{len(result_segments)+1}", "start": start, "end": end,
                                "text": segment.text.strip(), "words": words, "status": "model-derived",
                                "avg_log_probability": float(segment.avg_logprob),
                                "no_speech_model_probability": float(segment.no_speech_prob)})
    if sha256(source) != source_before or any(sha256(model_dir / row["name"]) != row["sha256"] for row in inventory):
        raise ValueError("source/model changed during transcription; result identity is invalid")
    return {"schema_version": 1, "kind": "rea-video-transcript", "status": "completed", "channel": "audio-speech-asr",
            "source": {"path": str(source), "sha256": source_before, "bytes": source.stat().st_size},
            "coverage": coverage, "time_convention": "seconds from recorded clock origin; video start PTS when available, otherwise first audio PTS",
            "text": " ".join(segment["text"] for segment in result_segments), "segments": result_segments, "words": result_words,
            "language": {"requested": request["language"], "detected": info.language, "status": "model-derived",
                         "model_probability": float(info.language_probability), "multilingual_model": bool(model.model.is_multilingual)},
            "provider": {"name": "faster-whisper", "version": importlib.metadata.version("faster-whisper"),
                         "runtime": "CTranslate2", "runtime_version": importlib.metadata.version("ctranslate2"),
                         "device": "cpu", "compute_type": request["compute_type"], "cpu_threads": request["cpu_threads"],
                         "model_directory": str(model_dir), "model_files": inventory, "model_license": "not inferred; consult the local model supplier",
                         "network": "disabled; complete local model/tokenizer required", "code_loading": "installed provider only; no model-adjacent Python/plugins"},
            "limits": ["Speech text and word boundaries are model-derived; they are not visible subtitle OCR or measured ground truth.",
                       "Whisper can hallucinate, omit, reorder or mistranscribe speech; inspect important names, language and noisy/silent regions.",
                       "Word probabilities are model scores, not calibrated accuracy guarantees; timestamps are approximate cross-attention estimates, not forced alignment.",
                       "No speaker diarization, voice identity, source separation or verified speech/subtitle correspondence.",
                       "Native provider is CPU-only; model/language accuracy requires separate task evidence. Model weights are not bundled or downloaded.",
                       "Zero padding represents missing timestamped samples, not observed silence; large gaps can reduce transcription quality."]}


def transcribe(source: str | Path, model_dir: str | Path, out_path: str | Path | None = None, *,
               language: str | None = None, max_seconds: float = 600.0, timeout_seconds: float = 300.0,
               cpu_threads: int = 2, compute_type: str = "int8") -> dict:
    """Transcribe an admitted local source with an explicit local model directory.

    The inference process is deadline-bounded and inherits the caller's process
    group, so a workspace job cancellation also stops nested ASR inference.
    """
    source = _local(source)
    model_dir = _local(model_dir, directory=True)
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("ASR source exceeds 8 GiB")
    model_files = _model_files(model_dir)
    max_seconds = bounded_number(max_seconds, "max_seconds", .1, MAX_SECONDS)
    timeout_seconds = bounded_number(timeout_seconds, "timeout_seconds", .01, 3600)
    threads = bounded_number(cpu_threads, "cpu_threads", 1, 8)
    if not threads.is_integer():
        raise ValueError("cpu_threads must be integer")
    if language is not None and (not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}", language)):
        raise ValueError("language must be a lowercase provider language code, e.g. en or vi")
    if compute_type not in {"int8", "float32"}:
        raise ValueError("CPU ASR compute_type must be int8 or float32")
    destination = Path(out_path).expanduser().resolve() if out_path is not None else None
    if destination is not None and (destination == source or destination in model_files or destination.is_relative_to(model_dir)):
        raise ValueError("transcript output cannot overwrite source/model files")
    request = {"source": str(source), "model_dir": str(model_dir), "language": language,
               "max_seconds": max_seconds, "cpu_threads": int(threads), "compute_type": compute_type}
    environment = dict(os.environ)
    environment.update({"PYTHONPATH": str(Path(__file__).resolve().parent.parent), "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false"})
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="rvpm-local-asr-") as temporary:
        temporary = Path(temporary)
        write_json(temporary / "request.json", request)
        with (temporary / "stderr.log").open("wb") as log:
            process = subprocess.Popen([sys.executable, "-m", "rea_video_pro_max.asr", "--worker", str(temporary / "request.json"),
                                        str(temporary / "result.json")], env=environment,
                                       cwd=Path(__file__).resolve().parent.parent, stdout=subprocess.DEVNULL, stderr=log)
            try:
                process.wait(timeout=timeout_seconds)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                process.kill()
                process.wait(timeout=10)
                raise RuntimeError("local ASR deadline exceeded or interrupted; inference child stopped") from None
        if not (temporary / "result.json").is_file():
            raise RuntimeError("local ASR worker failed: " + (temporary / "stderr.log").read_text(errors="replace")[-1500:])
        result = read_json(temporary / "result.json")
        if process.returncode or result.get("status") == "error":
            raise RuntimeError("local ASR failed: " + result.get("message", "unknown provider error"))
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    if destination is not None:
        write_json(destination, result)
    return result


def _main():
    if len(sys.argv) != 4 or sys.argv[1] != "--worker":
        raise ValueError("use the transcribe API or public CLI; this entry point is an internal bounded worker")
    try:
        result = _run(read_json(sys.argv[2]))
    except Exception as error:
        write_json(sys.argv[3], {"status": "error", "error": type(error).__name__, "message": str(error)[:2000]})
        return 1
    write_json(sys.argv[3], result)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
