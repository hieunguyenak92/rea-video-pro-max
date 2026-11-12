# Extract style and bind new content

## Separate reusable rules from reference facts

The analysis explains A. A style template keeps transferable typography, normalized placement, bounded entry/transition families and relative rhythm. Content bindings supply B's words, scene durations, media, colors, optional audio and font. Composition resolves those inputs into a new timeline.

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
```

Inspect `style`, `rhythm`, `motion`, `evidence`, `implementation_choices`, `unknowns` and `support`. The native extractor can substitute a licensed bundled font or a bounded primitive. A `pop` chosen to approximate a scale candidate does not prove that the original used that effect. Static defaults without text observations are implementation choices, not recovered caption style.

Choose the style invariants relevant to the user's result: caption anchor and treatment, word grouping, transition family, motion family or relative shot rhythm. Distinguish them from degrees of freedom: the script, scene count, footage, colors if authorized, line wrapping, durations and output canvas. A deliberately changed parameter should be explained as an adaptation rather than a failed recovery.

## Write content bindings

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 30,
  "timing_policy": "relative",
  "scenes": [
    {
      "id": "new-intro",
      "text": "A different story starts here",
      "duration": 3.0,
      "asset": "assets/new-shot.png",
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

The `asset` field is optional. Without it the native renderer generates an independent graphic background; it does not pull footage from A. Image/video/font/audio paths resolve relative to the bindings file. Use supplied or authorized media. Scene video is muted; add a top-level explicit `audio` binding for sound. Supply `font` for a suitable licensed TTF/OTF when the bundled font lacks the needed glyphs.

New content can need more space and time than A. Recompute wrapping for the target canvas and font. Shorten or split text when it cannot fit the supported layout; do not make unreadable text fit by arbitrary shrinking. Verify readable hold time against the intended use. Non-space-delimited scripts need dedicated grouping support; do not equate a whitespace group with a linguistic word.

## Choose timing honestly

- `relative`: recompute timing for the new words and supplied scene duration. Without word windows, the implementation uses character-weighted estimates. This is useful for silent graphic videos and drafts, not a verified narration alignment.
- `fixed`: require explicit scene durations and preserve their clock, with no implicit transition overlap contraction.
- `audio-anchored`: require explicit scene durations and `words` windows for each whitespace-delimited word. These are user-supplied new-content timings, not automatic ASR.

For `scene.words`, provide ordered, non-overlapping `{ "text": "A", "start": 0.0, "end": 0.25 }` entries in scene-local seconds for every word. Do not reuse A's word windows. If accurate narration synchronization is required and no aligned windows are available, produce or obtain alignment through an authorized capable tool, then disclose its source and inspect playback.

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content ./content.json --out ./work/project
```

Use a new output directory. The result stores `project.json`, the template, content bindings, resolved timeline and copied media/font hashes. Check `provenance`, `assets` and captions before rendering. Assets with A's exact hash are rejected by default; do not enable explicit reference reuse for a task asking for independent B media. Hash inequality alone cannot prove creative independence—inspect the actual supplied content.

The new video does not require a clean plate or removal of burned-in captions from A. Use independent B visuals and render the supported style onto them.
