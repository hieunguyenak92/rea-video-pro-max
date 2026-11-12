# Contributing

Start with a reproducible task: reference → expected observation, or template +
new content → expected render. Use owned/permitted media and provide a small
sanitized fixture. Preserve measured, model-derived, inferred and unknown fields.
Do not turn a successful tool call into an accuracy or compatibility claim.

```sh
python -m pip install -e '.[test,mcp,interop]'
python -m pytest -q
ruff check .
python tools/check_repository.py
```

System FFmpeg/FFprobe and Tesseract with English data are needed for the complete
acceptance suite. Optional dependency tests may skip when unavailable; release
validation records all skips and does not count them as passed lanes.

Keep changes focused. Add behavioral tests for new algorithms, media support or
exports; retain loss receipts and uncertainty. A new provider needs provenance,
license, version/language/device boundaries and an actually executed fixture.
Keep nine README introductions, quickstarts and important limits consistent.

The examples are not a universal benchmark. Broader style, genre and language
claims require independent annotated media and published failure cases.
