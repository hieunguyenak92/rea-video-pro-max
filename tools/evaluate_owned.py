"""Evaluate decoded analysis against independent authoring truth, after analysis."""

from __future__ import annotations

import argparse
import json
import statistics
import unicodedata
from pathlib import Path


def distance(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        next_row = [i]
        for j, y in enumerate(b, 1):
            next_row.append(min(row[j] + 1, next_row[-1] + 1, row[j - 1] + (x != y)))
        row = next_row
    return row[-1]


def evaluate(analysis, gold):
    thresholds = gold["thresholds"]
    expected = gold["cuts"]
    observed = [s["start"] for s in analysis["shots"][1:]]
    remaining = list(observed)
    errors = []
    for boundary in expected:
        if remaining:
            nearest = min(remaining, key=lambda x: abs(x - boundary))
            if abs(nearest - boundary) <= thresholds["cut_tolerance_seconds"] + 1e-8:
                errors.append(abs(nearest - boundary))
                remaining.remove(nearest)
    precision = len(errors) / len(observed) if observed else float(not expected)
    recall = len(errors) / len(expected) if expected else float(not observed)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    captions = analysis.get("captions", [])
    actual_text = unicodedata.normalize("NFC", " ".join(c["text"] for c in captions)).casefold()
    expected_text = unicodedata.normalize("NFC", " ".join(c["text"] for c in gold["captions"])).casefold()
    cer = distance(actual_text, expected_text) / max(1, len(expected_text))
    cue_errors = []
    for cue in gold["captions"]:
        match = next((c for c in captions if c["text"].casefold() == cue["text"].casefold()), None)
        if match:
            cue_errors.extend([abs(match["start"] - cue["start"]), abs(match["end"] - cue["end"])])
    anchor_error = abs(analysis.get("style", {}).get("position", [0, 0])[1] - gold["style"]["anchor_y"])
    gates = [
        {
            "name": "hard-cut-F1",
            "value": f1,
            "minimum": thresholds["cut_f1"],
            "passed": f1 >= thresholds["cut_f1"],
        },
        {
            "name": "clean-caption-CER",
            "value": cer,
            "maximum": thresholds["clean_caption_cer"],
            "passed": cer <= thresholds["clean_caption_cer"],
        },
        {
            "name": "cue-boundary-max-seconds",
            "value": max(cue_errors) if cue_errors else None,
            "maximum": thresholds["cue_boundary_seconds"],
            "passed": len(cue_errors) == 2 * len(gold["captions"])
            and max(cue_errors) <= thresholds["cue_boundary_seconds"] + 1e-8,
        },
        {
            "name": "caption-anchor-y-error",
            "value": anchor_error,
            "maximum": thresholds["anchor_y_absolute_error"],
            "passed": anchor_error <= thresholds["anchor_y_absolute_error"],
        },
        {"name": "requested-signal-coverage", "passed": analysis["coverage"]["complete"]},
    ]
    return {
        "schema_version": 1,
        "kind": "rea-video-owned-evaluation",
        "status": "passed" if all(x["passed"] for x in gates) else "failed",
        "source_sha256": analysis["source"]["sha256"],
        "gates": gates,
        "details": {
            "cut_errors_seconds": errors,
            "cut_precision": precision,
            "cut_recall": recall,
            "cue_boundary_errors_seconds": cue_errors,
            "cue_boundary_median_seconds": statistics.median(cue_errors) if cue_errors else None,
            "actual_caption_text": actual_text,
            "expected_caption_text": expected_text,
        },
        "limits": [
            gold["limits"],
            "Thresholds were authored in the fixture generator before the analysis run. This small corpus cannot substantiate broad genre/language or market superiority claims.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", type=Path)
    parser.add_argument("gold", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(json.loads(args.analysis.read_text()), json.loads(args.gold.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result))
    raise SystemExit(0 if result["status"] == "passed" else 1)
