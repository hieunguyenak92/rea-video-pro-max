# Runtime and support boundaries

## Setup

From a checkout, create an isolated Python 3.11+ environment and install the package with `python -m pip install -e .`. The core requires Pillow, NumPy and PyAV plus FFmpeg/FFprobe on `PATH`; the output encoder requires libx264, and explicit audio output requires a suitable AAC encoder. The optional extras are `.[mcp]` for local stdio MCP and `.[interop]` for OTIO export.

For an extracted skill without the root package files, install `Pillow>=11,<13`, `numpy>=2,<3` and `av>=14,<18` into the selected interpreter, then run the bundled script. Keep the whole `lib`, `assets`, `references` and `scripts` tree. Do not run installation in a host environment unrelated to the task.

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

Read actual package, binary, encoder, OCR and font availability. A dependency being installed is not proof that its behavior was tested on the user's file. Do not silently download models, request a cloud API or replace the native renderer when a dependency is missing. Use the user's existing authorization for ordinary project setup, and explain the precise missing capability if it blocks the requested result.

## Conditional capabilities

- **OCR:** optional local Tesseract. `auto` reports unavailable/partial output; `required` fails when the requested language cannot run. OCR visible text is distinct from audio transcription.
- **Transcripts:** supplied text/cues stay supplied; imported ASR artifacts retain model/provider/source provenance. Plain-text timing syntax is not parsed into observed captions. Optional `.[asr]` supports explicit local faster-whisper models; no model weights or diarization are bundled. Read [speech-and-motion.md](speech-and-motion.md) for strict new-audio binding and verified limits.
- **Font:** bundled Be Vietnam Pro is a licensed explicit substitute. Candidate font fit does not identify the original font. Supplied fonts need glyph coverage; complex scripts require a suitable shaping build and dedicated verification. Native v1 rejects bidirectional captions.
- **Media:** codecs depend on the local decoder. Analysis accounts for supported display rotation and pixel aspect metadata; native rendering requires upright square-pixel bound footage.
- **Exports:** native JSON, CSV, SRT, WebVTT and bounded ASS; optional OTIO reader round trip; integer-CFR EDL. FCPXML and specific external NLE imports are not certified.
- **External providers:** optional capabilities are not installed or certified by this skill's presence. Discover tool schemas, preserve provider provenance and report unavailable work honestly.

## Native budgets

These are admission/operation limits, not measured performance promises. Analysis admits up to 8 GiB source size and 16 megapixels per decoded frame, limits the decoded pass to one million frames/900 seconds of wall time, and stores up to 600 sampled evidence frames. Visual sampling defaults to 4 fps. Report separate decoded and visual/OCR coverage when limits are reached.

Composition admits 1–256 scenes, even canvas dimensions from 64 to 3840 with at most 3840×2160 pixels, 1–60 fps, at most 600 seconds/36,000 frames, and at most 1 GiB per bound file. Keep files and budgets appropriate to the user's machine; these limits are not throughput benchmarks.

## Limits that remain unknown

A flattened video does not uniquely reveal original source footage, occluded pixels, hidden layers, the exact original font/plugin/project, 3D scene, AI model or prompt. Native v1 focuses on observable timing, visible text and bounded 2D style reuse. Complex compositing, source-layer unmixing, arbitrary 3D reconstruction, HDR mastering and unrestricted NLE effect round trips are outside its verified scope.

Core analysis/rendering do not upload media or call a paid model API. Your agent host has separate account and data policies. Reports, crops and copied project media are local outputs that can contain sensitive content; use an explicit output directory and share them intentionally. Reports copy reference media and evidence by default; `report --no-media` omits the full media copy, not OCR text, paths or crops. macOS is the measured development platform; Linux CI is an intended target and Windows native rendering is not certified.
