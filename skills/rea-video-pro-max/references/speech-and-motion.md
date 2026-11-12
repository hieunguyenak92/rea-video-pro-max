# Local speech and deeper motion

Use these lanes when the task needs speech timing or measurable transform data.
They are separate evidence channels; neither reveals the original editor project.

## Speech from an explicit local model

Install `.[asr]` in the checkout environment (or `faster-whisper>=1.2.1,<2` for an
extracted skill). The user supplies a **complete local CTranslate2 model folder**:
`model.bin`, `config.json`, `tokenizer.json` and `vocabulary.txt`/`vocabulary.json`.
No model ID, fallback tokenizer download or cloud request is accepted. Respect
the model supplier's license. Do not infer multilingual support from the API.

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py transcribe new-narration.wav --model /absolute/local/model --language en --out work/speech.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py bind-speech content.json --transcript work/speech.json --out work/audio-bound-content.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose work/style-template.json --content work/audio-bound-content.json --out work/spoken-project
```

`transcribe` performs guarded PyAV audio decode → mono 16k sample clock → CPU
faster-whisper inference in a deadline-bounded child. Text and cross-attention
word timestamps are **model-derived**, not forced alignment or visible subtitle
OCR. Voice identity, diarization and stem separation are not provided.

`bind-speech` requires the exact new audio hash, complete coverage with no missing
sample gaps, nonzero ordered word windows and a matching script word sequence.
It preserves new audio timing, splits it across scenes and marks its provenance.
It rejects mismatched words rather than inventing alignment. Review ASR mistakes
or supply independently aligned new word windows. An English-only model rejects
other requested languages. Word scores are not calibrated accuracy guarantees.

Passing the transcript to `analyze --transcript speech.json` imports a separate
model-derived artifact with provider/source identity; it never overwrites OCR.
If its source differs from the reference, the mismatch remains explicit.

The executed provider case is tiny.en, CPU int8, owned English speech. Other
model/language combinations require their own task evidence. Weights are not
bundled. See [measured validation](https://github.com/hieunguyenak92/rea-video-pro-max/blob/main/docs/VALIDATION.md) from a checkout;
the repository copy is the authoritative record for packaged-skill users.

## Apparent image-space motion

`analyze --motion-profile affine` (default) fits small global similarity/affine
transforms from hash-checked sampled frames. `coarse` retains lower-cost phase
translation; `off` skips motion fitting. Actual source PTS and coverage remain.

The affine lane uses tile phase matches, robust fits and regional rejection.
Residual pixels are held out **from direct photometric refinement**; phase-match
initialization uses overlapping regions, so these are not fully independent
end-to-end validation pixels. Temporal constant/linear/ease-in-out candidates
use held-out trajectory samples and complexity penalties. Rejected pairs break
the trajectory; cuts reset it. Weak texture, repetition, occlusion, nonrigid
motion and unsupported jumps can yield unknown instead of a guessed transform.

192 pair fits are distributed across the observed shots. Inspect omitted pairs,
sample gaps and unsupported regions before making a full-video claim. Sampled
global transforms do not separate camera, foreground, parallax or hidden masks.

The native B renderer reuses a supported signed scale component and supported
curve as a bounded crop approximation. Zoom-out stays zoom-out. Unknown motion
is not promoted to an estimated effect. Rotation/shear/translation observations
remain in the analysis when the native render primitive cannot preserve them.
Use the editable JSON for an explicitly supported external adapter rather than
advertising an arbitrary effect as recovered.
