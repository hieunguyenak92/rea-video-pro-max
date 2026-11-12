# REA-Video-Pro-Max

## Give Claude & Codex an editor’s eye.

**Break down the pacing, captions and motion in a reference video. Turn those decisions into a reusable style. Render a new video with your own words and media.**

Great edits have a language. Make it part of your creative toolkit.

[**▶ Explore the live demo**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**Get the skill**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [Release v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Claude Code / Codex skill · CLI + optional MCP · Local processing · Apache-2.0**

---

## From “I love this edit” to “Here’s my version.”

You find a video with the right energy: the rhythm of its cuts, the way captions land, a highlight that moves through each phrase, a zoom that gives a still image momentum.

REA-Video-Pro-Max turns the supported parts of that style into something you can inspect, adjust and reuse. Bring a new script, images, footage or narration. Keep an editable project and an actual rendered video at the end.

| Reference A | Your new video B |
| :---: | :---: |
| [![A frame from the owned reference video](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![A rendered frame with new words and independent media](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| Study the shot rhythm and caption treatment. | Apply the reusable style to a different story. |

*Actual frames from the included owned demo. B uses new text, independently generated media and new caption timing. The [interactive walkthrough](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) lets you scrub both videos and inspect the recorded timeline, template, project and verification.*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## Put a reference to work

| What you want to do | What you walk away with |
| --- | --- |
| Understand why an edit feels the way it does | Shot intervals, visible text, caption appearance, apparent motion and audio cues, linked to timestamps and evidence. |
| Carry a subtitle treatment into a new story | Reusable typography, layout and highlight palettes, applied to the new words and their new timing. |
| Build a repeatable video format | A style template you can bind to another script and another set of assets. |
| Direct the result | A native JSON timeline/project with copied assets and hashes that you can inspect, change and render again. |
| Bring the analysis into your own pipeline | Structured files, an offline inspector, subtitle exports and bounded timeline interchange. |

Use it for a new product introduction, an educational clip, a creator series, an editing study or a custom video tool. When you only need the breakdown, the analysis and timeline are complete deliverables on their own.

## One prompt to start the workflow

Install the bundled skill, give your agent the reference and your new content, then ask:

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

You direct the story. The skill gives the agent a concrete workflow and executable tools for analysis, composition, rendering and verification.

## What makes the workflow useful

- **An edit you can inspect.** Decoded presentation timestamps, frame evidence and coverage make the timeline traceable. Measured signals, model results and inferred editing choices keep their own labels.
- **Subtitle detail that survives the handoff.** Estimate visible size, position, fill and outline; retain distinct observed highlight palettes and style variants. Reflow and retime the new words during composition.
- **Motion with a sense of direction.** Fit bounded similarity/affine motion and temporal curve candidates. The native renderer can reuse a supported signed zoom component, including zoom out.
- **A project you can keep building on.** New images, footage, fonts and optional audio are copied into a portable project. Explicit bindings and hashes make the chosen content inspectable.
- **Speech when the task needs it.** Optional local faster-whisper ASR provides model-derived word windows. Strict script/audio matching can bind them to the new content; an explicit local model is required.
- **A result you can check.** Verify project/output identity, decode the rendered video and independently OCR-check caption content. Keep the evidence alongside the output.

The native renderer supports **static / fade / pop / slide captions**, **cut / dissolve / fade / wipe transitions**, and **static / signed panzoom backgrounds**. Analysis can retain richer motion observations than the native renderer can reproduce. [Exact support](docs/SUPPORT-MATRIX.md).

## Get your first result

### 1. Set up the runtime

Use **Python 3.11+**, **FFmpeg + FFprobe** and an FFmpeg build with **libx264**. Install **Tesseract with `eng` language data** to run the included OCR and caption-verification example. Python dependencies are installed below.

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

These shell commands target macOS/Linux. Release CI passed on Linux and macOS; Windows native rendering is not certified. `doctor` reports the tools actually available on your machine.

### 2. Give your agent the skill

Copy the **whole** `skills/rea-video-pro-max` folder into your project’s skill directory:

| Host | Project-local destination |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

You can also extract the [skill ZIP](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) there. Keep its `lib`, `assets`, `scripts` and `references` together. For a ZIP-only installation, install its Python dependencies with `python -m pip install -r /path/to/rea-video-pro-max/requirements.txt`; the entrypoint is `python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`. The console commands below come from the checkout installation above. Your agent must use the interpreter containing those dependencies.

### 3. Run the included A → B example

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

Open `work/video-b.mp4`. Your portable project is in `work/project/`; the reference analysis is in `work/analysis/`. Use a fresh output directory for each composition. To open an offline analysis inspector, run:

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

Then open `work/report/timeline.html` locally. The [CLI, skill and optional MCP share the same kernel](skills/rea-video-pro-max/references/runtime-and-support.md).

<details>
<summary><strong>Make it yours: what goes into a content binding?</strong></summary>

A content binding is a JSON file choosing your new scenes, text, media and optional audio/font. Your agent can create it from an ordinary brief. Start with [examples/content.json](examples/content.json).

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 24,
  "scenes": [
    {
      "id": "intro",
      "text": "Your next story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

Add an `asset` path for an image or video, and `audio` for an explicit soundtrack or narration. Media paths resolve relative to this JSON file. The renderer uses the chosen new content; reuse of the exact reference media requires an explicit opt-in.

New words receive new timing. Character-weighted timing is an estimate. Supply new word windows or use strictly matched local ASR when speech timing matters. [Speech and motion guide](skills/rea-video-pro-max/references/speech-and-motion.md).

</details>

## See the work behind the promise

**v0.1.1 passed 176 local tests**, including the actual optional local ASR case. [Hosted CI passed three Linux/macOS jobs](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397). The release’s six uploaded artifacts were downloaded and checked against the local bytes and checksums.

The evidence includes a complete owned **A → analysis → style → new B** replay, an independent Vietnamese task with corrected typography/outline and two highlight regimes, and a motion task that preserves zoom-in/zoom-out direction. These are bounded owned cases; they establish the demonstrated workflow, rather than broad genre or language accuracy.

[Inspect the analysis](docs/evidence/reference-analysis.json) · [Read the template](docs/evidence/style-template.json) · [Open the project](docs/evidence/project.json) · [Check the verification](docs/evidence/verification.json) · [Validation details](docs/VALIDATION.md)

## Keep the output. Extend the system.

| Format | What it carries |
| --- | --- |
| Native JSON | Analysis, timelines, captions/style/motion/audio data, templates and editable native projects. |
| CSV | Shot rows for inspection and downstream processing. |
| SRT / WebVTT | Visible text and cue windows. |
| ASS | Caption timing with an explicit substitute style; observed appearance and uncertainty remain in the native evidence. |
| OTIO / EDL | Optional OTIO reference slices with annotations; EDL for measured integer-CFR cuts. Export receipts describe losses. |
| MP4 + offline HTML | The new video and an inspectable local analysis report. |

The native project is editable JSON. This release does not export native Premiere, Resolve, After Effects or CapCut projects, or FCPXML. External-editor imports of the supported interchange files remain unverified. [Exporter and renderer boundaries](docs/SUPPORT-MATRIX.md).

## Know the creative boundaries

The current release focuses on observable editing evidence and supported **2D** style reuse. Exact original fonts, hidden layers, plugins, source assets and project history can remain unknown. OCR and motion fits can be wrong; sampled coverage and uncertainty stay visible.

Bound footage must be upright with square pixels. Its scene audio is muted; provide audio explicitly. Complex scripts need suitable fonts/shaping; bidirectional captions are rejected. Nine README translations describe the product and do not certify nine OCR/render languages. Human review remains part of judging creative style and sound. [Full support matrix](docs/SUPPORT-MATRIX.md).

Core processing runs locally and requires no paid model API or content upload. Dependencies and optional model setup can require network access; the Claude/Codex host has its own data policies. Local reports include reference media and crops by default. `report --no-media` omits the full reference copy, while text and crops remain. [Privacy](docs/PRIVACY.md).

## Help shape the next editing workflow

**If this is a workflow you want in your creative toolkit, give the project a star.** It helps other creators and AI builders find the work.

**Fork it to build your own editing vocabulary:** add a caption treatment, develop a renderer adapter, extend an export workflow or contribute an owned reference-to-result example. Bring reproducible evidence so the next capability earns its place.

[**⭐ Star on GitHub**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Fork and build**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [Contribute](CONTRIBUTING.md) · [Report a task](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

Independent project, inspired by [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video). [Apache-2.0](LICENSE); separate font, codec and model terms are preserved in [NOTICE](NOTICE).

[Support](SUPPORT.md) · [Maintenance](docs/MAINTENANCE.md) · [Skill instructions](skills/rea-video-pro-max/SKILL.md)
