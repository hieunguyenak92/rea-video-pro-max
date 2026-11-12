# Analyze the reference

## Establish the observable scope

Use the actual media file, not a thumbnail or a verbal description of it. Confirm that it decodes, note display dimensions/rotation, and preserve its identity and timestamp evidence. Still images use the same `analyze` path but cannot establish duration, cuts, animation, beat or speech timing.

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze ./reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py report ./work/analysis/analysis.json --out ./work/report
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/analysis/analysis.json --mode analysis
```

Read subcommand help for `--sample-fps`, `--max-seconds` and supplied transcript options. Explicitly request `--ocr required` when the task cannot succeed without OCR; `auto` may legitimately produce partial analysis when OCR is unavailable. Language data availability does not certify recognition quality. Choose the actual visible language rather than inferring it from the conversation language. The local report copies the reference media and evidence by default; `report --no-media` omits the full media copy but keeps analysis text/crops.

## Inspect the data before interpreting it

Start with `analysis.json`, its `coverage`, `unknowns` and toolchain. The output also includes the inferred timeline, captions, subtitle styles, coarse motion, audio cues, shot CSV and evidence frames/crops. Use native JSON as the source of truth; simpler exports omit evidence and semantics.

The decoded signal pass and sampled visual/OCR pass have separate coverage. A complete decode does not prove that every brief overlay was inspected. Missing PTS requires disclosed fallback timing. The evidence sample budget and time limit can leave later text uninspected. State the analyzed range and the unobserved range when material to the task.

Review at least the event boundaries and representative caption variants relevant to the request. Correct demonstrable OCR errors without describing your correction as raw observed output. Do not fill missing words from contextual plausibility and call them recovered.

## Reason by editing layer

| Layer | Useful analysis | Avoid concluding |
| --- | --- | --- |
| Shot rhythm | Observed intervals, cut candidates, relative short/long pattern | Original camera clip in/out or recovered source files |
| Visible text | Readable wording, cue visibility, region, persistence | Guaranteed speech transcript or word-level ASR alignment |
| Typography | Normalized size/anchor, fill/stroke candidates, wrapping, candidate font fit | Exact font identity from a single raster match |
| Caption animation | Observed region changes and supported family candidate | Exact easing/keyframes/plugin without evidence |
| Motion | Coarse apparent image translation or scale evidence | Whether movement came from camera, subject or editor |
| Transition | Supported cut/gradual-change candidate | Original compositing graph or arbitrary transition recovery |
| Audio | Signal activity, onset candidates, supplied transcript identity | Guaranteed BPM, beat, speaker or dialogue transcription |

Persistent top labels and changing bottom subtitles should remain separate explanatory tracks when the evidence supports that distinction. A highlight color may be a decorative accent rather than a spoken-word highlight. Tracking gaps, masking and compression can imitate entrance/exit effects; describe ambiguity.

## Export only the required subset

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py export ./work/analysis/analysis.json --format native --out ./work/export/native
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py export ./work/analysis/analysis.json --format srt --out ./work/export/srt
```

CSV, SRT, WebVTT and ASS are available bounded exports. OTIO requires its optional dependency and represents flattened reference slices with annotations; it is not the original layered project. EDL is restricted to integer CFR cut lists. FCPXML is explicitly unavailable in this release. Read each export's loss receipt and disclose relevant losses.

An analysis-only request is complete when the requested analysis/timeline is substantive, inspectable and verified. Creating B is a separate branch when requested; do not render a cosmetic reconstruction of A as a substitute.
