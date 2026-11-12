# Validation record

Date: 2026-11-12. This file records executed checks, not a general compatibility
or market-superiority claim. The source includes reproducible fixtures and tests.

## Environments actually exercised

- macOS 26.1 arm64, Python 3.14.3; Pillow 12.1.1, NumPy 2.4.3, PyAV 17.1.0.
- Isolated Python 3.13.13 install with Pillow 12.3.0, NumPy 2.5.4, PyAV 17.1.0,
  official MCP SDK 1.30.0 and OpenTimelineIO 0.18.1.
- System FFmpeg/FFprobe 8.1.2, libx264/AAC and Tesseract. This FFmpeg lacks
  `ass`, `subtitles` and `drawtext`; actual B rendering uses Pillow/PyAV/FFmpeg.
- Pillow in the original environment has no RAQM. English and Vietnamese glyph
  behavior is exercised; this does not certify the installed 163 OCR languages.

## Executed evidence

- Real H.264 decode, new-caption OCR, Vietnamese typography, image/video binding,
  four transition families, caption entrance families, portable relocated rerender,
  explicit audio with measured delay/silence and deadline cleanup.
- Independent orchestration tests found and drove fixes for artifact symlink escape,
  nested binding escape, malformed artifact errors, output collision, revision
  handling, CSV formula injection and verification that accepted reordered words.
- Actual official-SDK stdio initialize/list/call plus workspace-bound
  template → compose → render → verify jobs and artifact paging. This is protocol
  client evidence; native Claude Code/Codex MCP settings have not been exercised.
- OTIO 0.18.1 writer/reader round trip on the three reference shot slices. No
  Premiere/Resolve/AE/CapCut application import is certified.
- Headless Chrome demo checks cover both real MP4s, four recorded JSON files,
  inspection, relative scrubbing, linked playback, independent audio restoration,
  desktop and 390px layouts. The website presents recorded results only.

## Owned reference and new-content video

`tools/make_fixtures.py` independently authors A, new B media and hidden truth;
it does not import the product analyzer or renderer. `tools/replay_demo.py` runs
the product on the media, then `tools/evaluate_owned.py` reads the authoring truth.
The analyzer never receives that gold JSON. The clean fixture thresholds are
declared before analysis: hard-cut F1 ≥0.95 within one 24fps frame, caption CER
≤0.05, cue error ≤one frame, normalized anchor error ≤0.04, full requested signal
coverage. This is a small owned fixture, not a representative corpus.

The first baseline found exact cuts/clean cue timing and a good anchor estimate,
but **failed caption CER (0.2941)** because diagram bars were read as subtitle
text. That failure drove separate scene/ambiguous text tracks and subtitle
classification. The final replay now passes the owned gates: hard-cut F1 **1.0**,
caption CER **0.0**, cue-boundary max error **0.0 s**, anchor-Y error
**0.001389**, and complete requested signal coverage. The independent Vietnamese
forward-use rerun also passes its four bounded gates with exact cuts, 31px
compatible catalog rendering size, 2px visible outline, distinct yellow/cyan
word palettes and actual new assets; its report is in
`evidence/independent-forward-use.md`. These are small synthetic/owned cases,
not universal accuracy evidence.

A separate motion fixture measured signed zoom-in/zoom-out recovery (sampled
scale errors **0.0033784** and **0.0000911**) and B marker area ratios **1.30675**
and **0.76885**. Its first run intentionally failed because ring graphics became
OCR text; the same temporal/layout admission gate now keeps those 217 suspect
regions in `text_regions` while leaving `captions` empty, so unknown style does
not poison B. The motion fit itself remains model-derived apparent motion, not
camera/layer history. Final replay evidence was regenerated after these fixes.

```sh
python -m pip install -e '.[test,mcp,interop]'
python -m pytest -q
ruff check .
python tools/check_repository.py
python tools/replay_demo.py --work /tmp/rea-video-fresh-replay
```

The reference includes no speech. B uses a different script, images/footage and
pulse audio. Estimated new word timing is not speech alignment. OCR verifier
requires ordered words with multiplicity, checks cue interiors and binds output
bytes to the exact project receipt. This does not certify creative quality or
all frame-by-frame animation phases.

## Limits and work not yet certified

Broad genre accuracy, arbitrary fonts, dense local/3D motion, exact hidden layers,
original source/plugin/project recovery, HDR mastering, unrestricted external
NLE round trips, all languages/OSes and superiority to other tools are unverified.
Optional model/provider checks count only when a pinned model actually ran.
See the [support matrix](SUPPORT-MATRIX.md) for the implemented subset.
