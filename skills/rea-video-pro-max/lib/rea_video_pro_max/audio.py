"""Bounded streaming signal analysis. No speech/music/SFX identity claims."""
from __future__ import annotations

import math
from pathlib import Path

import av
import numpy as np


def _intervals(flags, times, end):
    result = []
    start = None
    for flag, t in zip(flags, times):
        if flag and start is None:
            start = float(t)
        elif not flag and start is not None:
            if t-start >= .12:
                result.append({"start": round(start, 6), "end": round(float(t), 6)})
            start = None
    if start is not None and end-start >= .12:
        result.append({"start": round(start, 6), "end": round(float(end), 6)})
    return result


def analyze_audio(source: str | Path, *, duration: float, video_origin: float = 0, max_seconds: float | None = None) -> dict:
    rate, window, hop = 16000, 512, 256
    energies, fluxes, sample_positions = [], [], []
    pending = np.empty(0, np.float32)
    previous_spectrum = None
    sample_cursor = 0
    decoded_samples = 0
    origin = None
    source_start_pts = None
    source_time_base = None
    peak = 0.0
    partial = False
    discontinuities = []
    resampled_pts_missing = 0
    decoded_end = 0.0
    with av.open(str(source), options={"protocol_whitelist": "file,pipe", "format_whitelist": "mov,mp4,m4a,3gp,3g2,mj2,matroska,webm,avi,mpeg,mpegts,ogg,flv,asf,mxf,nut,wav,mp3,flac,aac,aiff,ac3,au"}) as container:
        if not container.streams.audio:
            return {"status": "absent", "has_audio": False, "onsets": [], "silences": [], "tempo": {"status": "unavailable", "reason": "no audio stream"}}
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=rate)
        for frame in container.decode(stream):
            if origin is None:
                source_start_pts = frame.pts
                source_time_base = {"num": frame.time_base.numerator, "den": frame.time_base.denominator} if frame.time_base else None
                origin = float(frame.pts * frame.time_base) if frame.pts is not None and frame.time_base else float(stream.start_time * stream.time_base) if stream.start_time is not None else 0.0
            if max_seconds is not None and frame.pts is not None and float(frame.pts * frame.time_base)-video_origin >= max_seconds:
                partial = True
                break
            for chunk in resampler.resample(frame):
                data = chunk.to_ndarray().reshape(-1).astype(np.float32)
                absolute_chunk_start = float(chunk.pts * chunk.time_base) if chunk.pts is not None and chunk.time_base else None
                if absolute_chunk_start is None:
                    chunk_start = sample_cursor + len(pending)
                    absolute_chunk_start = origin + chunk_start/rate
                    resampled_pts_missing += 1
                else:
                    chunk_start = round((absolute_chunk_start-origin)*rate)
                expected_start = sample_cursor + len(pending)
                if abs(chunk_start-expected_start) > 4:
                    discontinuities.append({"time": round(absolute_chunk_start-video_origin, 6), "gap_seconds": round((chunk_start-expected_start)/rate, 6),
                                            "gap_interval": [round(origin+expected_start/rate-video_origin, 6), round(absolute_chunk_start-video_origin, 6)], "status": "measured"})
                    pending = np.empty(0, np.float32)
                    sample_cursor = chunk_start
                    previous_spectrum = None
                if max_seconds is not None:
                    remaining = max(0, int((video_origin + max_seconds - absolute_chunk_start) * rate))
                    data = data[:remaining]
                if not len(data):
                    continue
                decoded_end = max(decoded_end, absolute_chunk_start-video_origin+len(data)/rate)
                decoded_samples += len(data)
                if decoded_samples > rate * 7200:
                    partial = True
                    break
                peak = max(peak, float(np.max(np.abs(data))))
                pending = np.concatenate((pending, data))
                while len(pending) >= window:
                    block = pending[:window]
                    energy = float(np.sqrt(np.mean(block * block)))
                    spectrum = np.abs(np.fft.rfft(block * np.hanning(window)))
                    flux = float(np.maximum(0, spectrum - previous_spectrum).sum()) if previous_spectrum is not None else 0.0
                    energies.append(energy)
                    fluxes.append(flux)
                    sample_positions.append(sample_cursor)
                    previous_spectrum = spectrum
                    pending = pending[hop:]
                    sample_cursor += hop
            if partial:
                break
    offset = (origin or 0) - video_origin
    times = np.asarray(sample_positions, float) / rate + offset
    energy_array = np.asarray(energies)
    flux_array = np.asarray(fluxes)
    if not len(energies):
        return {"status": "unavailable", "has_audio": True, "reason": "audio too short for 512-sample windows", "onsets": [], "silences": []}
    threshold = max(.002, float(np.max(energy_array)) * .04)
    silence = energy_array < threshold
    flux_threshold = float(np.median(flux_array) + 3.0 * np.median(np.abs(flux_array-np.median(flux_array))))
    flux_threshold = max(flux_threshold, float(np.max(flux_array)) * .12, .01)
    onsets = []
    for i in range(1, len(fluxes)-1):
        if 0 <= times[i] < duration and flux_array[i] >= flux_threshold and flux_array[i] >= flux_array[i-1] and flux_array[i] >= flux_array[i+1] and energy_array[i] >= threshold:
            candidate = {"time": round(float(times[i]), 6), "sample_index": int(sample_positions[i]), "strength": round(float(flux_array[i]), 5), "status": "measured", "method": "positive-spectral-flux", "role": "signal_onset_not_sfx_identity"}
            if not onsets or candidate["time"] - onsets[-1]["time"] >= .12:
                onsets.append(candidate)
            elif candidate["strength"] > onsets[-1]["strength"]:
                onsets[-1] = candidate
    tempo = {"status": "unknown", "reason": "insufficient periodic onset evidence"}
    if len(onsets) >= 4 and not discontinuities:
        intervals = np.diff([x["time"] for x in onsets])
        median = float(np.median(intervals))
        jitter = float(np.median(np.abs(intervals-median))) / max(median, .001)
        bpm = 60 / median if median else 0
        while 0 < bpm < 50:
            bpm *= 2
        while bpm > 200:
            bpm /= 2
        if jitter < .18 and bpm > 0:
            tempo = {"status": "estimated", "bpm": round(bpm, 2), "method": "median-onset-interval", "relative_jitter": round(jitter, 4), "alternatives": [round(bpm/2, 2), round(bpm*2, 2)], "limits": "periodic onsets may be sound effects rather than a musical beat"}
    envelope_stride = max(1, math.ceil(len(energies)/1500))
    end = min(duration, float(times[-1])+window/rate)
    visible = (times >= 0) & (times < duration)
    silences = _intervals(silence[visible], times[visible], end)
    if discontinuities:
        # A silence interval cannot bridge missing audio packets: distinguish
        # low observed energy from regions with no samples.
        for gap in discontinuities:
            if gap["gap_seconds"] <= 0:
                continue
            begin, finish = gap["gap_interval"]
            split = []
            for region in silences:
                if region["end"] <= begin or region["start"] >= finish:
                    split.append(region)
                else:
                    if min(region["end"], begin)-region["start"] >= .12:
                        split.append({"start": region["start"], "end": min(region["end"], begin)})
                    if region["end"]-max(region["start"], finish) >= .12:
                        split.append({"start": max(region["start"], finish), "end": region["end"]})
            silences = split
    return {"status": "measured", "has_audio": True, "stream_index": stream.index,
            "source_start_pts": source_start_pts, "source_time_base": source_time_base,
            "analysis_sample_rate": rate, "sample_origin_seconds": round(offset, 9), "decoded_samples": decoded_samples,
            "coverage": {"start": round(max(0, offset), 6), "end": round(end, 6), "partial": partial,
                         "decoded_end": round(min(duration, decoded_end), 6), "unwindowed_tail_seconds": round(max(0, min(duration, decoded_end)-end), 6),
                         "discontinuities": discontinuities[:500], "resampled_pts_missing": resampled_pts_missing},
            "peak_dbfs": round(20*math.log10(max(peak, 1e-12)), 3),
            "rms_mean": round(float(energy_array.mean()), 7), "silence_rms_threshold": round(threshold, 7),
            "onsets": onsets[:2000], "onsets_omitted": max(0, len(onsets)-2000),
            "silences": silences, "tempo": tempo,
            "envelope": [{"time": round(float(times[i]), 6), "rms": round(float(energies[i]), 6)} for i in range(0, len(energies), envelope_stride) if visible[i]],
            "unknowns": ["speech transcription (ASR not run)", "speaker identity", "original music/speech/effects stems", "music and SFX semantic labels"],
            "method": "streamed-mono-16k-rms-and-spectral-flux", "loudness_semantics": "RMS/peak are not LUFS or true-peak measurements"}
