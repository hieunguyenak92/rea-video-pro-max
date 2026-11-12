# Support

REA-Video-Pro-Max is an independent project. Start with the [support matrix](docs/SUPPORT-MATRIX.md), [measured validation](docs/VALIDATION.md) and the relevant command's `--help`.

Before filing an issue, run:

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

Include the version, operating system, exact command, relevant error/check result and the smallest reproducible input you may share. For OCR, include the requested language and whether its Tesseract language data is installed. For rendering, include the content bindings/project settings and whether the failure is composition, font coverage, encoding, verification or playback. A short owned synthetic clip is preferable to a private production reference.

The local report can contain full reference media, OCR text, evidence crops and local paths. `report --no-media` removes the full media copy only. Redact confidential information before posting an issue or sending a project bundle. See [privacy](docs/PRIVACY.md).

Use the issue templates for a bug or capability request. Do not post secrets or private media in public security reports. If the hosting platform offers private vulnerability reporting, use that facility for a vulnerability; otherwise disclose only the minimal non-sensitive description until a private channel is agreed.

Maintainers can assess reproducible behavior, supported primitives and documented limits. There is no promised response time, guaranteed font identification, arbitrary effect recovery or universal editor import support. Translation feedback is welcome; the nine README versions have not been claimed as professionally reviewed by native speakers.
