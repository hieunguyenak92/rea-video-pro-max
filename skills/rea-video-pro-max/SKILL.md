---
name: rea-video-pro-max
description: Analyze a reference video or frame into an evidence-backed edit timeline and reusable caption, motion and rhythm style; apply that style to new text and media and render a different video. Use for video edit breakdown, subtitle-style analysis and reference-to-new-content creation.
---

# REA-Video-Pro-Max

Convert a flattened reference into inspectable editing evidence and a reusable style contract. When the task includes creation, bind new content and render a different video. The reference is evidence, not an implicit footage or music source.

## Choose the requested result

- **Analyze a video or frame:** read [analysis.md](references/analysis.md). Deliver the analysis, inferred timeline, relevant exports and meaningful findings. A frame supports layout/type/color evidence, not animation or sound.
- **Create a new video from a reference:** analyze first, then read [style-and-content.md](references/style-and-content.md) and [render-and-verify.md](references/render-and-verify.md). Deliver the template, content bindings, portable project, rendered B and verification result.
- **Use an existing template:** inspect its provenance and supported primitives, then begin at content binding. Do not reanalyze A unless needed.
- **Setup or unsupported effect/language/export:** read [runtime-and-support.md](references/runtime-and-support.md).
- **A public YouTube/Facebook/TikTok URL:** read [url-ingestion.md](references/url-ingestion.md), acquire one bounded local copy first, then continue with the normal analysis workflow. Never treat a URL as a local media path.
- **Speech timing or global motion fitting:** read [speech-and-motion.md](references/speech-and-motion.md). Use an explicit local model for ASR and preserve model-derived timing separately from visible text.

Keep these four artifacts distinct: observed reference timeline, inferred editing operations, reusable StyleTemplate, and new-content concrete timeline. A renderer choice for B is not a historical fact about A.

## Run the bundled implementation

Resolve the skill directory from this file. Run its `scripts/rea-video-pro-max.py` with the Python environment containing the dependencies. The examples below use the repository layout; inside an installed skill, replace the prefix with that skill's absolute directory.

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py --help
```

Use explicit output paths in the user's workspace. Preserve original inputs. `compose --out` expects a fresh directory; `template --out` expects a JSON file. Consult subcommand `--help` before using optional flags. A configured local MCP server may expose the same kernel: discover its actual tool schemas rather than invent tool names or assume a provider is installed.

For an authorized public platform URL, install the optional downloader and use the dedicated URL command. It records a source manifest and then hands a local file to the unchanged analysis kernel:

```sh
python -m pip install 'rea-video-pro-max[url]'
rea-video-pro-max analyze-url 'https://www.youtube.com/shorts/VIDEO_ID' --out ./work/url-analysis --ocr required --ocr-lang eng
```

When running from an extracted skill ZIP rather than a checkout, install `yt-dlp>=2025.01.15,<2027` directly in the interpreter used by the skill. The ZIP does not install optional dependencies automatically.

For a split workflow, run `fetch-url URL --out ./work/source`, read the recorded `downloaded_path` in `work/source/url-source.json`, then pass that local path to `analyze`. The one-command `analyze-url` workflow downloads into `source/`, analyzes into `analysis/` and returns both paths. URL acquisition is opt-in and bounded; it accepts supported public platform hosts only, one non-live video, no credentials, no playlist, no private/DRM bypass, and no automatic model download. If the optional downloader is unavailable or the platform requires login, provide a local video instead.

## Reference → style → new video

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content ./content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Inspect results between stages. An empty OCR track, a partial sampled range, or unsupported motion cannot become a confident recovered template merely because commands completed. Refine the supported parameters from evidence or mark implementation choices explicitly. Do not replace substantive analysis with a generic aesthetic prompt.

## Preserve the useful boundaries

- Treat measured metadata, detected text, fitted parameters, supplied data, inferred mechanisms and unknowns separately. Preserve PTS/time base and coverage. OCR engine scores are not calibrated probabilities.
- Identify the job of a caption: subtitle, title, label or persistent graphic. Do not silently label all visible text as speech. Supplied transcript text is supplied evidence.
- Reflow and retime new words. Never copy A's word timestamps onto B. Character-weighted estimates are not audio alignment; `audio-anchored` mode requires new supplied or strictly matched ASR word windows, with the timing origin retained.
- Use explicit new script/assets, or create independent procedural visuals when consistent with the task. Missing new footage is not permission to reuse A. No clean plate or burn-in removal is required for independent B media.
- Carry template approximations and unknowns into the handoff. Original font, hidden layers, source clips, easing, plugins and generative prompts can remain unknown.
- Keep optional model/API use within the user's existing authorization. The native pipeline works without a cloud model. Do not imply installation, account access or a paid provider is automatic.

## Finish with evidence

For analysis: open representative evidence frames/crops, review time coverage and verify the native data; return files plus concise supported findings and material uncertainty.

For creation: verify content/assets, style invariants and decoded playback; inspect beginning, transitions and end; listen when audio was supplied. Explain estimated timing, unsupported effects or verification failures. A project file alone does not satisfy a requested rendered video.

Use exact measured capability statements. “Strongest” and “universal recovery” are not verified properties of this release.
