# Privacy and local data

The native analysis, template, composition, render, report and export paths run on the local machine. They do not upload media, send OCR text to a hosted inference service, download model weights or require a paid model API. There is no built-in telemetry or media publishing step in this runtime. Dependency installation can contact package registries; the agent host and any separately configured provider have their own policies.

## What the files contain

| Output | Potentially sensitive data |
| --- | --- |
| Analysis and inferred timeline | Local source path, source hash, visible OCR text, timing, toolchain and evidence references |
| Evidence directory | Sampled reference frames and text crops, including readable private content |
| Local report | Analysis text/data, copied evidence and, by default, a copy of the reference media |
| Style template | Reference hash, reusable parameters, evidence links and unknowns |
| Portable project | New text, resolved timeline, copied media/font/audio, local content bindings and hashes |
| Render and verification | Encoded new-content video, artifact paths/hashes, checks and decoder metadata |

`report --no-media` omits the copied full reference media. It does **not** remove OCR text, evidence crops, local paths or other analysis data from the report. Redact or select outputs before sharing. Native JSON preserves more information than a subtitle export; it is not a redacted document.

Core inputs are read as local files. Outputs go into the explicit directory/file selected by the caller. The runtime does not provide secure erasure, encrypted storage, retention management or an operating-system sandbox. Delete outputs and temporary project copies when no longer needed; use your own storage/access controls for confidential files.

## Agent and MCP boundaries

The skill is an instruction and local execution package. Claude Code, Codex and any model selected by the user can process instructions, tool arguments or results according to their separate data policies. Local media processing alone does not determine what an agent host sends to its model. Avoid placing confidential text into prompts/results when the host policy is unsuitable.

The optional stdio MCP server is configured with an explicit workspace and confines its artifact paths to that workspace. It does not expose an internet listener or publish its workspace. Its jobs execute local media tools with the user's process permissions; that confinement is not a replacement for OS-level isolation of untrusted media decoders. Use a narrowly scoped workspace rather than your home directory.

## Public examples

The checked-in walkthrough uses owned synthetic media intended for public distribution. It is a recorded run, not a live upload interface. Opening the static demo downloads its checked-in media/evidence from wherever it is hosted. It has no upload or hosted inference endpoint and uses no external analytics/CDN scripts.

Before reporting a problem, share the smallest non-confidential reproducer. Do not post a private reference, full report, source path or new-content asset bundle to a public issue unless you intend it to be public.
