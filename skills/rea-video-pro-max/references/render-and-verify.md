# Render and verify the new video

## Render the resolved project

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Rendering uses Pillow for 2D frames, PyAV for bound footage decoding and FFmpeg/libx264 for MP4 encoding. It does not depend on FFmpeg `drawtext`, `ass` or `subtitles` filters. Optional explicit audio is encoded/muxed separately. It does not invoke a generative-video model.

Supported choices include graphic/image/video backgrounds, bounded static/panzoom motion, word groups and highlighting, caption static/fade/pop/slide entry, and cut/dissolve/fade/wipe transition primitives. The particular inferred template may use only a subset. Unsupported arbitrary effects are not silently recovered by selecting a similar name.

Rendering checks copied asset/font hashes and rejects changed or missing dependencies. Do not disable that check to make a stale project pass; recomposite from the intended new inputs. Short video assets hold their final frame for a longer scene. Scene footage audio is muted unless separately bound. Native v1 rejects rotated/anamorphic bound footage; prepare upright square-pixel media first.

Keep the generated `render.receipt.json` beside the output. Style-transfer verification checks exact project/output hashes and runs independent OCR for caption content; the included command therefore needs local Tesseract and `eng` data. Choose the actual caption language for other inputs. Decode-only success cannot establish that the requested words appeared.

## Check three different outcomes

| Outcome | Evidence needed |
| --- | --- |
| B contains the requested new content | Compare bindings with resolved text, scene order and asset hashes; inspect actual media; check reference-reuse provenance |
| B follows the supported style contract | Check normalized anchor/type treatment, grouping, entry/transition/motion family and intended rhythm; record deliberate changes |
| B is a usable video | Decode the output; inspect dimensions, duration, frame coverage and render receipt; watch beginning, representative caption changes, transitions and end; listen when sound was supplied |

Whole-frame pixel similarity to A is not a useful primary success criterion for a different story with different assets. Compare supported style properties and the resolved B timeline instead. Exact-looking pixels do not prove that hidden editing history was recovered.

Machine verification is bounded. A passing receipt does not certify all fonts, all effects, all players, natural phrasing or aesthetic quality. Read individual checks and any skipped/unavailable property. Report a partial or failed check honestly and repair the concrete failure where possible. When human playback inspection cannot be performed, name that remaining gap.

## Deliver the useful handoff

For a creation request, return the playable MP4, portable project directory, template/content bindings and verification record. Include concise notes on inferred substitutions, estimated vs supplied word timing, material unsupported effects and any remaining playback/language gap. Preserve native data when exporting simpler formats. Do not stop at an attractive report when the user asked for a rendered B.

For analysis-only requests, use the analysis verification mode instead; B rendering is not required.
