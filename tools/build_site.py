"""Build the recorded public walkthrough; exclude private analysis/workspace data."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/hieunguyenak92/rea-video-pro-max"


def build(out):
    if out.exists():
        raise ValueError("Site output must be a new directory")
    shutil.copytree(ROOT / "docs", out, ignore=shutil.ignore_patterns("IMPLEMENTATION-CONTRACT.md"))
    path = out / "index.html"
    text = path.read_text().replace('href="../README.md"', f'href="{REPOSITORY}#readme"')
    text = text.replace(
        'href="../examples/content.json"', f'href="{REPOSITORY}/blob/main/examples/content.json"'
    )
    for name in ["VALIDATION.md", "SUPPORT-MATRIX.md", "PRIVACY.md"]:
        text = text.replace(f'href="{name}"', f'href="{REPOSITORY}/blob/main/docs/{name}"')
    path.write_text(text)
    (out / ".nojekyll").write_text("")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    print(build(parser.parse_args().out.resolve()))
