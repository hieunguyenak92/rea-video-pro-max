# Changelog

## Unreleased

- Add opt-in public URL ingestion for supported YouTube, Facebook and TikTok page URLs through the optional `url` extra. `fetch-url` records a provenance manifest; `analyze-url` downloads one bounded local video and runs the existing analysis kernel.
- Reject credentials, unsupported hosts, private-network resolution, playlists and live streams; preserve local-only behavior when the optional downloader is not installed.

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
