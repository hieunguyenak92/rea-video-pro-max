# Support matrix

This is the **implemented boundary of v0.1.0**, not a certification of every codec, language, editor or operating system. [Validation](VALIDATION.md) records the environment and cases actually run. `doctor` reports local availability; availability alone does not prove output quality.

## Runtime and platforms

| Component | Requirement / boundary |
| --- | --- |
| Python | 3.11+ declared; see validation for the interpreter actually tested |
| Native dependencies | Pillow 11–12, NumPy 2, PyAV 14–17; isolated environment recommended |
| System tools | FFmpeg and FFprobe on `PATH`; libx264 for MP4 output; AAC encoding for explicit audio output |
| macOS | Development and measured local validation platform; exact version in validation |
| Linux | Intended CI/runtime target; only CI results actually completed count as evidence |
| Windows | Not certified. Native pipe handling and FFmpeg invocation need platform-specific validation |
| Browser | Static report/demo viewing only; no browser renderer or hosted inference dependency |
| Cloud models | Not required by the native pipeline; no bundled paid API, ASR or video-generation service |
| Optional MCP | Local stdio server using the official Python SDK, explicit workspace, job execution and artifact reads |
| Optional OTIO | Install `.[interop]`; native OTIO adapter readback, not specific NLE certification |

The README activation comment for PowerShell shows how Python virtual environments are activated; it does not certify Windows media rendering.

## Analysis

| Capability | Native behavior | Important limit |
| --- | --- | --- |
| Local video input | Decode selected non-attached video stream; preserve PTS/time-base evidence | Decoder/codec dependent; missing PTS fallback disclosed |
| Still-image input | Layout/color/visible text evidence, including supported image orientation | No temporal, shot-rhythm or audio inference |
| Display metadata | Analysis handles supported rotation and sample-aspect metadata | Unusual/malformed transforms can be rejected |
| Shot/transition candidates | Signal changes and bounded cut/gradual-change hypotheses | Not original camera source in/out or arbitrary transition graph |
| Visible text | Optional local Tesseract, regions, cue tracking and OCR engine score | Not guaranteed speech or exact transcript; score is not a calibrated probability |
| Subtitle appearance | Raster-derived size/position/color/stroke estimates and font candidates | Exact original font/easing/plugin unknown; masks and occlusion remain unresolved |
| Motion | Optional coarse translation; default bounded similarity/affine fit and constant/linear/ease-in-out trajectory candidates | Sampled image-space motion; rejection/coverage/residuals explicit, no camera/object/layer decomposition or 3D recovery |
| Audio | Local signal activity/onset cues; separate supplied/imported transcript data | No bundled model weights, diarization or guaranteed musical-beat identification |
| Optional local ASR | Explicit complete CTranslate2 model, guarded 16k decode, CPU faster-whisper and approximate word timestamps | Actual tiny.en English case measured; no automatic downloads, no forced alignment or blanket multilingual certification |
| Supplied transcript | Local text; structured JSON cue windows when provided | Supplied, not independently verified or merged into observed OCR |
| Evidence | Frame/region files, source identity, methods, unknowns and coverage | Sampled visual coverage differs from full decoded signal coverage |

Admission/operation limits: up to 8 GiB source, 16 megapixels per frame, one million decoded frames, 900 seconds of wall time and 600 sampled evidence frames. Sampling defaults to 4 fps; requested sample rate is limited to `(0, 30]`. `--max-seconds` can bound the analyzed range. Budget exhaustion is reported as partial coverage, not full-video inspection. These are limits, not performance benchmarks.

## New-content composition and rendering

| Capability | Native behavior | Important limit |
| --- | --- | --- |
| Content binding | New scene text, graphics, image/video assets, optional font/audio | No reference-media fallback; exact reference hash reuse rejected by default |
| Native project | Copied assets/font, hashes, template/content identity, resolved timeline | A native portable project, not an original Premiere/Resolve/AE/CapCut file |
| Timing | New word grouping and character-weighted estimates; supplied or strictly matched new-audio ASR windows | ASR cross-attention estimates are not forced alignment; mismatched script/audio is rejected |
| Captions | Fill/stroke/box/shadow, normalized anchor, wrapping and per-word highlight | Supported 2D primitive subset; unsupported layout/overflow fails |
| Caption entrance | Static, fade, pop, slide | Fixed bounded native families, not recovered arbitrary keyframes |
| Background | Independent graphics, images, decoded video; static/signed panzoom and supported curve | Zoom-out direction preserved; affine rotation/shear are analysis data, not arbitrary native effects. Upright square-pixel footage; short assets hold final frame |
| Transitions | Cut, dissolve, fade, wipe | Relative-timing overlap differs from fixed/audio-anchored timing; inspect resolved timeline |
| Audio | Explicit new audio binding, offset, local encode/mux | Scene-video audio muted; no automatic music extraction, TTS or alignment |
| Font/language | Licensed bundled Be Vietnam Pro; suitable supplied font; glyph checks | Bidirectional captions rejected. Complex scripts require RAQM and separate tests |
| Video output | Software raster → FFmpeg/libx264, MP4/yuv420p | SDR 2D output; no HDR mastering or generative-video synthesis |
| Verification | Exact render receipt/project/output identity, structure/provenance, decoded playback and independent OCR caption check | Style-transfer caption-content pass needs OCR; machine checks do not replace creative, listening or broad player review |

Composition admits 1–256 scenes; even dimensions 64–3840 with no more than 3840×2160 pixels; 1–60 fps; at most 600 seconds/36,000 frames; up to 1 GiB per bound asset. These admission limits do not promise real-time rendering. Nine README translations are documentation coverage, **not nine verified OCR/render languages**.

## Export behavior

| Format | Supported representation | Loss / certification boundary |
| --- | --- | --- |
| Native JSON | Timeline, captions, motion/audio annotations, provenance, uncertainty | Preserves the native model; does not turn unknown history into fact |
| CSV | Shot editorial rows | Captions, hierarchy, motion, style and uncertainty remain in native JSON |
| SRT / WebVTT | Visible text and cue windows | No full typography/effects; OCR timing is not spoken alignment |
| ASS | Caption timing with explicit Be Vietnam Pro substitute style | No original font/effect/highlight recovery; centisecond rounding |
| OTIO | Flattened reference slices with annotations; adapter readback | Optional dependency; effect hypotheses are metadata, not NLE effect nodes |
| EDL | Integer-CFR non-drop-frame cut list | Fractional/VFR rejected; no layer/transition/effect semantics |
| FCPXML | Unavailable | Explicit error; not certified in v0.1.0 |
| Premiere / Resolve / After Effects / CapCut project | Unavailable | No claim of native application project recovery or import validation |

Read each export receipt's `losses`. Successful syntax or adapter readback does not certify import fidelity in an external editor. B's portable native project and renderer are distinct from A's flattened-reference interchange exports.

## Outside the verified scope

Original source recovery, clean-plate unmixing, arbitrary mask/occlusion separation, exact hidden layer/plugin/keyframe recovery, 3D scene reconstruction, original generative prompt identification, unrestricted NLE round trips and market-superiority claims. Unsupported providers and unrun language/platform combinations remain unverified.
