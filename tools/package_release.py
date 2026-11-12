"""Deterministic source/skill ZIPs and byte-level checksums. No network actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist", ".rea-video-jobs"}


def files(root):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(x in IGNORE or x.endswith(".egg-info") or x.startswith(".venv") for x in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing release symlink: {relative}")
        if path.is_file() and path.name != ".DS_Store" and path.suffix not in {".pyc", ".pyo"}:
            yield path, relative


def archive(path, source, prefix):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for file, relative in files(source):
            info = zipfile.ZipInfo(f"{prefix}/{relative.as_posix()}", date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, file.read_bytes(), compresslevel=9)


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    archive(
        out / "rea-video-pro-max-v0.1.0-skill.zip", ROOT / "skills/rea-video-pro-max", "rea-video-pro-max"
    )
    archive(out / "rea-video-pro-max-v0.1.0-source.zip", ROOT, "rea-video-pro-max")
    records = [
        {"file": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(out.glob("*"))
        if p.suffix in {".zip", ".whl", ".gz"}
    ]
    (out / "SHA256SUMS").write_text("".join(f"{p['sha256']}  {p['file']}\n" for p in records))
    (out / "release-manifest.json").write_text(
        json.dumps({"schema_version": 1, "version": "0.1.0", "artifacts": records}, indent=2) + "\n"
    )
    print(json.dumps(records))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    main(parser.parse_args().out.resolve())
