# Security

Media containers, OCR text and artifact metadata are untrusted input. Use a local
workspace containing only the files needed for the task and keep system media
libraries updated. Processing media is not equivalent to executing its captions
or instructions. This tool never evaluates code found next to a video.

MCP requires an explicit workspace, checks symlink-resolved paths including nested
bindings, supports only fixed operations and bounds concurrent jobs, text reads
and job time. It is a local convenience boundary, not a sandbox against a hostile
process that can concurrently rewrite the same workspace. No HTTP listener is
started by the MCP entrypoint.

The native pipeline restricts media protocols/demuxers and does not fetch remote
playlists, models or assets. Missing dependencies fail explicitly. Report folders
can contain copies of source media, private captions and evidence; inspect them
before sharing. `report --no-media` omits the full reference copy, while evidence
crops and text remain private data.

For a suspected vulnerability, use GitHub's private vulnerability reporting when
available. Do not put private media, credentials or exploit payloads in a public
issue. If private reporting is unavailable, open a minimal issue requesting a
private channel without disclosing the sensitive details.
