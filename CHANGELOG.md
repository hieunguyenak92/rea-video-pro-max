# Changelog

## 0.1.1 — 2026-11-13

- Separate coherent subtitle candidates from scene/suspect OCR in the recorded demo.
- Make the ring-graphic regression assert caption/style exclusion across OCR builds; retain scene-text observations without calling them subtitles.
- Preserve the original v0.1.0 source tag; release artifacts identify the patched source.

## 0.1.0 — 2026-11-12

- Local reference analysis with source hashes, PTS index, coverage, shot candidates,
  OCR text/style evidence, coarse motion and sample-clock audio signals.
- Distinct observed timeline, inferred operations, reusable style and new-content
  bindings. Unsupported history remains unknown.
- Portable projects with fresh caption timing, copied/hashed fonts and media,
  native 2D rendering, explicit audio and full decode/identity verification.
- Offline inspector; native, CSV, subtitle and bounded OTIO/EDL interchange.
- CLI, workspace-bound cancellable stdio MCP jobs, Claude/Codex skill, owned A/B
  walkthrough and nine README languages.

See [validation](docs/VALIDATION.md) and [support matrix](docs/SUPPORT-MATRIX.md)
for measured coverage and unsupported capabilities. This version does not claim
unique original-project recovery or market superiority.
