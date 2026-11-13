"""Command line entry point. JSON on stdout, actionable errors on stderr."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import doctor
from .operations import execute


def parser():
    root = argparse.ArgumentParser(prog="rea-video-pro-max", description="Reverse-engineer the edit. Create new videos in its style.")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Inspect actual local runtime capabilities")
    for name in ("fetch-url", "analyze-url"):
        command = commands.add_parser(name, help="Download one public platform video, then optionally analyze it")
        command.add_argument("input", help="Public YouTube, Facebook or TikTok video URL")
        command.add_argument("--out", required=True, help="New output directory")
        command.add_argument("--max-download-bytes", type=int, default=1 * 1024 * 1024 * 1024)
        command.add_argument("--max-download-seconds", type=float, default=900)
        command.add_argument("--download-timeout-seconds", type=int, default=900)
        if name == "analyze-url":
            command.add_argument("--ocr", choices=["auto", "off", "required"], default="auto")
            command.add_argument("--ocr-lang", default="eng")
            command.add_argument("--max-seconds", type=float)
            command.add_argument("--sample-fps", type=float, default=4)
            command.add_argument("--transcript")
            command.add_argument("--motion-profile", choices=["affine", "coarse", "off"], default="affine")
    for name in ("analyze", "template", "compose", "render", "report", "timeline", "export", "verify", "transcribe", "bind-speech"):
        command = commands.add_parser(name)
        command.add_argument("input", help="Local media or artifact JSON (analysis directories also accepted)")
        command.add_argument("--out", required=name != "verify")
        if name == "analyze":
            command.add_argument("--ocr", choices=["auto", "off", "required"], default="auto")
            command.add_argument("--ocr-lang", default="eng")
            command.add_argument("--max-seconds", type=float)
            command.add_argument("--sample-fps", type=float, default=4)
            command.add_argument("--transcript", help="Optional supplied transcript; never relabeled as OCR/ASR")
            command.add_argument("--motion-profile", choices=["affine", "coarse", "off"], default="affine")
        if name == "transcribe":
            command.add_argument("--model", required=True, dest="model_dir", help="Complete local CTranslate2 model directory; never downloaded automatically")
            command.add_argument("--language")
            command.add_argument("--max-seconds", type=float, default=600)
            command.add_argument("--timeout-seconds", type=float, default=300)
            command.add_argument("--cpu-threads", type=int, default=2)
            command.add_argument("--compute-type", choices=["int8", "float32"], default="int8")
        if name == "bind-speech":
            command.add_argument("--transcript", required=True)
        if name == "compose":
            command.add_argument("--content", required=True, help="New content bindings JSON; local assets resolve relative to it")
        if name == "render":
            command.add_argument("--timeout-seconds", type=float, default=3600)
        if name == "report":
            command.add_argument("--no-media", action="store_false", dest="include_media")
        if name == "export":
            command.add_argument("--format", choices=["native", "csv", "srt", "vtt", "ass", "otio", "edl", "fcpxml"], default="native")
        if name == "verify":
            command.add_argument("--mode", choices=["analysis", "style-transfer", "export"], default="analysis")
            command.add_argument("--render", dest="render_path")
            command.add_argument("--ocr-lang", help="Independently OCR-check rendered cue interiors with Tesseract")
    return root


def main(argv=None):
    args = vars(parser().parse_args(argv))
    command = args.pop("command")
    try:
        if command == "doctor":
            result = doctor()
        elif command in {"fetch-url", "analyze-url"}:
            from .url_ingest import fetch_url
            source_url = args.pop("input")
            output = Path(args.pop("out")).expanduser().resolve()
            if command == "analyze-url" and output.exists() and any(output.iterdir()):
                raise ValueError("analyze-url output must be a new or empty directory")
            manifest = fetch_url(
                source_url,
                output / "source" if command == "analyze-url" else output,
                max_bytes=args.pop("max_download_bytes"),
                max_seconds=(args.get("max_seconds") or args.pop("max_download_seconds")),
                timeout_seconds=args.pop("download_timeout_seconds"),
            )
            if command == "fetch-url":
                result = manifest
            else:
                from .analysis import analyze
                analysis_dir = output / "analysis"
                media = output / "source" / manifest["downloaded_path"]
                analysis_options = {
                    "ocr": args.pop("ocr"), "ocr_lang": args.pop("ocr_lang"),
                    "max_seconds": args.pop("max_seconds"), "sample_fps": args.pop("sample_fps"),
                    "transcript": args.pop("transcript"), "motion_profile": args.pop("motion_profile"),
                }
                analysis = analyze(media, analysis_dir, **analysis_options)
                analysis_manifest = analysis_dir / "url-source.json"
                analysis_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                result = {
                    "status": "passed",
                    "source_manifest": str((output / "source" / "url-source.json").resolve()),
                    "media": str(media.resolve()),
                    "analysis": str((analysis_dir / "analysis.json").resolve()),
                    "analysis_source_manifest": str(analysis_manifest.resolve()),
                    "source_sha256": manifest["sha256"],
                    "duration_seconds": analysis["source"]["duration"],
                    "shots": len(analysis.get("shots", [])),
                    "captions": len(analysis.get("captions", [])),
                }
        else:
            source = args.pop("input")
            target = args.pop("out")
            if target is None:
                # Verification without --out does not modify the project/source directory.
                from .verification import verify
                result = verify(source, **args)
            else:
                result = execute(command, source, target, args)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 1 if result.get("status") == "failed" else 0
    except (ValueError, KeyError, TypeError, RuntimeError, OSError) as error:
        print(json.dumps({"status": "error", "error": type(error).__name__, "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
