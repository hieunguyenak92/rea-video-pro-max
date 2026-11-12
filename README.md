# REA-Video-Pro-Max

## Reverse-engineer the edit. Create something new in its style.

**Turn a reference video into an evidence-backed timeline and a reusable style template. Then bind a different script and different media, and render your own video.**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[Recorded walkthrough](docs/index.html) · [Reference A](docs/media/reference.mp4) · [New-content B](docs/media/adapted.mp4) · [Verification](docs/VALIDATION.md) · [Support matrix](docs/SUPPORT-MATRIX.md)

A strong edit is a system of decisions: where a shot ends, how words group, which word lights up, when a title settles, how motion meets sound. REA-Video-Pro-Max makes the supported parts of that system inspectable and reusable.

```text
Reference A → analysis + inferred timeline → style template
                                             + new script / media
                                             → editable project → Video B
```

Use it through a Claude Code or Codex skill, the local CLI, or the optional local MCP interface. Analysis can also stand alone: a timeline and detailed files are valid deliverables when that is the task.

## See the actual handoff

The recorded example uses owned synthetic media. Its reference and adapted videos contain different text and media. The analysis, template, content bindings, project and verification record remain available for inspection. The walkthrough is a recorded result; the static website does not run inference or upload a visitor's video.

| Stage | Artifact |
| --- | --- |
| Read the edit | Shot intervals, visible text tracks, style estimates, coarse motion and audio cues, coverage and unknowns |
| Keep the evidence | Source identity, decoded presentation timestamps, frame/region references and method labels |
| Extract the grammar | Caption/layout settings, motion and rhythm choices, content slots and explicit approximations |
| Supply new content | New scene text, colors, images or footage; optional audio and font |
| Create the result | A portable native project, new caption timing and a locally encoded video |

## Ask in ordinary language

```text
Use REA-Video-Pro-Max on reference.mp4. Explain its shot rhythm, subtitle
style and motion, and save the analysis and inferred edit timeline.
Then use my new script and the assets in ./my-assets to make a different
video with a similar editing style. Keep the template and editable project,
verify the new content and playback, and report any unsupported effects.
```

For analysis alone: “Break down this video shot by shot and show which caption and motion properties are measured, estimated or unknown.” For a single frame: “Analyze its typography, layout and colors.” A still image cannot establish animation timing or sound.

## First result

You need Python 3.11+, FFmpeg and FFprobe. The Python runtime uses Pillow, NumPy and PyAV. Tesseract is optional for OCR; installed language data controls which OCR languages can run. See [support and prerequisites](docs/SUPPORT-MATRIX.md) for the exact tested boundary.

macOS is the measured development platform. Linux is an intended CI target; Windows native rendering is not certified. Creation verification uses the exact render receipt and an independent OCR pass for caption content, so the included end-to-end path needs Tesseract with `eng` data.

From the Git checkout:

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

Run the included path from reference to new-content render:

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Commands use the checkout layout. In a packaged skill folder, the entrypoint is `scripts/rea-video-pro-max.py`; keep its `lib`, `assets` and `references` folders together. Use the Python interpreter in which the dependencies are installed. Do not copy the entrypoint alone.

### Bring your own content

`examples/content.json` is a synthetic example of a **content binding**: the new text and media that fill the template's slots. It is a JSON file, not a video-editor project.

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 30,
  "scenes": [
    {
      "id": "intro",
      "text": "Your new story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

A scene may supply an `asset` path to an image or video. Paths are resolved relative to the bindings file. Supply `audio` or `font` when needed. The project records copied assets and hashes; the reference video is not silently used as replacement footage or music. New speech and new words need new timing. When exact spoken-word alignment is unavailable, the timing method remains explicit.

Bound scene-video audio is muted; supply an explicit new audio binding for sound. Short footage holds its final frame. Native v1 requires upright square-pixel bound footage. Complex and bidirectional scripts have additional shaping/grouping limits; see the support matrix before committing to a language.

## Install the agent skill

Copy the **whole** `skills/rea-video-pro-max` folder into the skill directory used by your host, or ask your agent to install it from this checkout. Typical project-local locations are `.claude/skills/rea-video-pro-max` for Claude Code and `.agents/skills/rea-video-pro-max` for Codex. Keep runtime dependencies in an isolated Python environment. Installing a skill does not install FFmpeg, OCR language data or model weights.

The [skill entrypoint](skills/rea-video-pro-max/SKILL.md) routes analysis, template extraction and creation tasks to their relevant references. It preserves the distinction between the reference's observed timeline, inferred editing operations, reusable style and the new video's concrete project. Your host still provides its own account, file access and execution permissions.

## What you can inspect and export

Analysis stores structured JSON alongside human-readable reports and evidence. Supported exports are selected explicitly; an exporter receipt identifies the represented subset and anything omitted or approximated.

- **Native JSON:** analysis, timeline, caption/style/motion/audio data, templates and projects.
- **CSV:** shot rows for inspection and downstream work.
- **SRT / WebVTT / ASS:** timed subtitle data in the capabilities of each format. SRT does not retain the full typography or motion style.
- **Timeline interchange:** use only adapters reported available by the installed version. Importability and a loss receipt do not imply that every editor can reproduce arbitrary effects.
- **Video:** the native software renderer builds the supported composition from new bindings and encodes it through FFmpeg. Rendering does not require FFmpeg's optional `drawtext`, `ass` or `subtitles` filters.

The exact command and format boundary belongs to the installed CLI's `--help` and [support matrix](docs/SUPPORT-MATRIX.md). Native JSON retains information that simpler formats cannot represent.

## Evidence before certainty

Measured metadata, detected text, fitted style and inferred mechanism are different kinds of evidence. An OCR result is not a guaranteed transcript. Apparent scale change does not prove a camera zoom. A font candidate is not a recovered original font. Missing model/provider work is reported as unavailable or partial, not passed.

A flattened video cannot uniquely reveal the original source clips, hidden pixels, original editor project, plugins, lighting rig, AI model or prompt. This release focuses on observable timing, captions and supported 2D editing primitives. It is not a universal video decompiler or a proven market leader. Complex occlusion, exact source-layer separation, arbitrary 3D reconstruction, HDR mastering and unrestricted NLE round trips are outside the verified boundary. Complex-script rendering needs shaping support and its own tests; nine README translations do not certify nine OCR or rendering languages.

New-content creation is checked against its bindings and style contract, rather than whole-frame pixel identity with the reference. Technical verification and human judgment about creative quality remain distinct. [Measured validation and remaining limits](docs/VALIDATION.md).

## Local processing and attribution

Core analysis and rendering run locally. This skill does not require a paid model API, upload video to a hosted inference service, or publish media. Installing dependencies or using an optional provider can involve network activity. Your Claude/Codex host has separate data policies. See [privacy](docs/PRIVACY.md).

Local reports copy reference media and evidence by default. `report --no-media` omits the full media copy, but keeps OCR text, local paths and crops. Review outputs before sharing.

Inspired by [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video). REA-Video-Pro-Max is an independent product; it is not an official upgrade, endorsement or mandatory wrapper around that runtime. Third-party source, font, media, codec and model terms remain separate. See the repository license and notices before redistributing assets.

[Get support](SUPPORT.md) · [Maintenance plan](docs/MAINTENANCE.md) · [Support matrix](docs/SUPPORT-MATRIX.md) · [Local release record](docs/RELEASE.md)

[Deeper local speech and motion (English technical reference)](skills/rea-video-pro-max/references/speech-and-motion.md).
