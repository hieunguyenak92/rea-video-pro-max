"""Reproduce owned A → actual REA → template → independent content → B."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills/rea-video-pro-max/scripts/rea-video-pro-max.py"


def replay(work):
    if work.exists():
        raise ValueError("Use a new work directory; replay never overwrites prior evidence")
    work.mkdir(parents=True)
    subprocess.run(
        [sys.executable, str(ROOT / "tools/make_fixtures.py"), "--out", str(work / "fixtures")], check=True
    )
    steps = [
        [
            "analyze",
            str(work / "fixtures/reference.mp4"),
            "--out",
            str(work / "analysis"),
            "--ocr",
            "required",
            "--ocr-lang",
            "eng",
        ],
        ["template", str(work / "analysis/analysis.json"), "--out", str(work / "style-template.json")],
        [
            "compose",
            str(work / "style-template.json"),
            "--content",
            str(work / "fixtures/content.json"),
            "--out",
            str(work / "project"),
        ],
        ["render", str(work / "project/project.json"), "--out", str(work / "video-b.mp4")],
        [
            "verify",
            str(work / "analysis/analysis.json"),
            "--mode",
            "analysis",
            "--out",
            str(work / "analysis-verification.json"),
        ],
        [
            "verify",
            str(work / "project/project.json"),
            "--mode",
            "style-transfer",
            "--render",
            str(work / "video-b.mp4"),
            "--ocr-lang",
            "eng",
            "--out",
            str(work / "verification.json"),
        ],
        ["report", str(work / "analysis/analysis.json"), "--out", str(work / "report")],
    ]
    for i, command in enumerate(steps):
        result = subprocess.run(
            [sys.executable, str(CLI), *command], capture_output=True, text=True, check=False, timeout=900
        )
        (work / f"step-{i + 1}.stdout.json").write_text(result.stdout)
        (work / f"step-{i + 1}.stderr.txt").write_text(result.stderr)
        if result.returncode:
            raise RuntimeError(f"{command[0]} failed; see {work}/step-{i + 1} logs")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/evaluate_owned.py"),
            str(work / "analysis/analysis.json"),
            str(work / "fixtures/hidden-gold.json"),
            "--out",
            str(work / "owned-evaluation.json"),
        ],
        check=True,
    )
    print(json.dumps({"status": "passed", "work": str(work)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    replay(parser.parse_args().work.resolve())
