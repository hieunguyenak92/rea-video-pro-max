# Public URL ingestion

URL ingestion is a separate acquisition step before REA analysis. The core analyzer still reads a local media path and does not upload content.

## Supported request

For a user-authorized, publicly accessible single video page on YouTube, Facebook or TikTok, install the optional `yt-dlp` extra and run:

```sh
python -m pip install 'rea-video-pro-max[url]'
rea-video-pro-max analyze-url 'https://www.youtube.com/shorts/VIDEO_ID' --out work/url-analysis --ocr required --ocr-lang eng
```

The command creates:

- `source/reference.<ext>` — the downloaded local media file;
- `source/url-source.json` — requested/resolved URL, extractor, video ID, duration, byte count, SHA-256, downloader version and policy;
- `analysis/analysis.json` plus the normal timeline, evidence and report artifacts.

The same acquisition can be split into two steps with `fetch-url` followed by `analyze`. Use a fresh output directory. The manifest is provenance, not proof that a platform owns or licenses the media.

## Boundaries

- Only `http`/`https` URLs on supported public platform hosts are accepted. Credentials and local/private network targets are rejected; URL fragments are discarded; playlists and live streams are rejected or reported by the extractor.
- A single download is bounded by 1 GiB, 900 seconds and a 15-minute default network deadline. Override limits only within the command's documented ranges.
- The optional dependency is not installed or invoked by the normal local pipeline. No cookies, account tokens, DRM bypass, scraping of private media or model weights are used.
- Platform availability, age/region restrictions, copyright, terms and the user's authorization remain separate from technical download success.
- The downloaded file is then processed locally by the same PTS, shot, OCR, motion and audio analysis used for a local file. URL ingestion does not change what the analyzer can infer from a flattened video.

If acquisition fails, save or export the video through an authorized method and give REA the resulting local MP4/MOV/WebM file. Do not paste a page URL into the ordinary `analyze` command; it expects a local path.
