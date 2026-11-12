# Release record — v0.1.0

Prepared locally on 2026-11-13 (Asia/Ho_Chi_Minh) after the measured gates in
`VALIDATION.md` passed. `tools/package_release.py` creates deterministic ZIPs in
`dist/` (ignored from source control) and writes `SHA256SUMS` plus a manifest.

Current local artifact hashes:

```text
1ce96bbb9be9f70a2289aeb60f86a416b822e7d6d86cd4f325bf07878ff91565  rea-video-pro-max-v0.1.0-skill.zip
```

The source ZIP hash is intentionally read from `dist/release-manifest.json` because that manifest includes this release record and a self-referential source hash would be unstable.

The extracted skill ZIP was tested with `doctor` and a real local OCR analysis;
the isolated Python environment passed the complete test suite with the optional
MCP, OTIO and local ASR dependencies installed. The source remains independent
of the upstream `JuneYaooo/rea-video` runtime.

The public GitHub repository, release record and Pages deployment are **not
claimed here**. A browser attempt to create a new public repository was stopped
by the host's safety review because the repository instructions still contain a
conflicting research-only publication rule. No public resource, upload or
external message was created. A maintainer can publish the prepared checkout and
verify the public bytes after resolving that authorization conflict.
