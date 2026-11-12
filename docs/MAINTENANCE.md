# Maintenance and release discipline

The native schema and artifact provenance are the compatibility boundary. Preserve the distinction between reference observation, inferred operation, reusable style and new-content project when extending the runtime.

## Change acceptance

- Add behavior through the shared local kernel so CLI, skill and MCP agree. Keep unsupported optional providers explicit.
- For analysis changes, use owned fixtures with known event timing and separate decoded vs sampled coverage. Test partial/missing OCR, missing PTS and malformed input where relevant.
- For style/renderer changes, verify new-content bindings, font/asset hashes, caption fit/timing, transitions and decoded output. Keep synthetic A and B content different.
- For exporters, preserve a loss receipt. Add external-editor certification only after an actual named editor/version import and behavior check.
- Treat capabilities, availability and measured cases separately. Do not convert a successful module import or modeled result into a real-player/platform/language claim.

## Before a release

Run the meaningful test/lint suite and the owned reference-to-B flow. Inspect the recorded media, evidence and verification output. Extract the distributable ZIP into a fresh directory and execute its scripts; validate skill metadata and reference links. Confirm that fonts and other redistributed assets include their actual licenses.

Update [validation](VALIDATION.md) with dated environment, commands, actual results and unresolved gaps. Synchronize the English and eight localized READMEs, support/privacy/skill references and the recorded walkthrough. Commands, exports and limits must agree across languages. The demo must display recorded local artifacts rather than invented fallback analysis.

Archive a source/ZIP checksum manifest and release notes. A prepared local release is different from a published GitHub release; publication, adoption and star measurements are reported separately. No star-growth promise or superiority claim follows from passing technical checks.

## Compatibility and dependencies

Use an explicit `schema_version` and `kind`; document migrations before changing stored semantics. Refuse incompatible input rather than silently treating old timestamps or style fields as new meaning. Keep new effects bounded and validate them at composition/render time.

Dependency updates need regression evidence for decoding, typography, encoding and optional MCP/OTIO behavior affected by the change. Avoid adding a model/API/runtime merely to increase a feature list. New language support needs glyph, shaping, grouping and playback evidence, separate from OCR-language installation and README translation.

## Ongoing product evidence

Expand real tasks in two branches: substantive analysis-only handoffs and create-from-style renders from independent new content. Review reported failures for repeatable root causes. Maintain a small diverse owned fixture set before expanding claims to new platforms, scripts, codecs or editing primitives. Keep unsupported behavior and unresolved evidence gaps visible until reproduced and verified.
