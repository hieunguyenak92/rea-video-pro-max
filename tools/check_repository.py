"""Release-facing links, schema examples and bundled-license integrity."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = [
    "README.md",
    "README.vi.md",
    "README.ko.md",
    "README.ja.md",
    "README.es.md",
    "README.pt-BR.md",
    "README.zh-CN.md",
    "README.th.md",
    "README.fr.md",
]


def check():
    failures = []
    checked = 0
    for path in [
        *map(lambda x: ROOT / x, LANGUAGES),
        *ROOT.glob("docs/*.md"),
        *ROOT.glob("skills/rea-video-pro-max/**/*.md"),
    ]:
        if not path.is_file():
            failures.append(f"Missing {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if path.name in LANGUAGES:
            for language in LANGUAGES:
                if f"]({language})" not in text:
                    failures.append(f"{path.name} missing language selector {language}")
            if len(text) < 3000:
                failures.append(f"{path.name} not substantive")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("https:", "http:", "mailto:", "#")):
                continue
            target = unquote(target.split("#")[0])
            if not (path.parent / target).exists():
                failures.append(f"{path.relative_to(ROOT)} broken target {target}")
            checked += 1
    lib = ROOT / "skills/rea-video-pro-max/lib/rea_video_pro_max"
    examples = [
        ("analysis", ROOT / "examples/analysis/analysis.json"),
        ("style-template", ROOT / "examples/style-template.json"),
        ("content", ROOT / "examples/content.json"),
        ("project", ROOT / "examples/project/project.json"),
    ]
    for name, path in examples:
        try:
            jsonschema.validate(
                json.loads(path.read_text()), json.loads((lib / "schemas" / f"{name}.json").read_text())
            )
        except Exception as error:
            failures.append(f"{name} schema: {error}")
    for font in (ROOT / "skills/rea-video-pro-max/assets/fonts").iterdir():
        if font.read_bytes() != (lib / "resources/fonts" / font.name).read_bytes():
            failures.append(f"Wheel/skill font mismatch {font.name}")
    for name in ["LICENSE", "NOTICE"]:
        if (ROOT / name).read_bytes() != (ROOT / "skills/rea-video-pro-max" / name).read_bytes():
            failures.append(f"Skill {name} differs")
    print(
        json.dumps(
            {
                "status": "failed" if failures else "passed",
                "local_links_checked": checked,
                "schemas_checked": len(examples),
                "readme_languages": len(LANGUAGES),
                "failures": failures,
            },
            indent=2,
        )
    )
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(check())
