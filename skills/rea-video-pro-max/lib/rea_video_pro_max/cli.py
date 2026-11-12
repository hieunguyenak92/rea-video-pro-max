"""Command line entry point. JSON on stdout, actionable errors on stderr."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import doctor
from .operations import execute


def parser():
    root = argparse.ArgumentParser(prog="rea-video-pro-max", description="Reverse-engineer the edit. Create new videos in its style.")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Inspect actual local runtime capabilities")
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
