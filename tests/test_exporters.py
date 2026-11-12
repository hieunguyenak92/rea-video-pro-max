"""Interchange output must preserve declared subset, identity and loss metadata."""

import json
from pathlib import Path

import pytest

from rea_video_pro_max.core import sha256
from rea_video_pro_max.exporters import export_analysis
from rea_video_pro_max.verification import verify


@pytest.fixture
def analysis(tmp_path):
    source = tmp_path / "reference.mp4"
    source.write_bytes(b"owned-source-identity")
    return {
        "schema_version": 1,
        "kind": "rea-video-analysis",
        "source": {
            "path": str(source),
            "sha256": sha256(source),
            "width": 640,
            "height": 360,
            "duration": 3,
            "fps": 24,
            "presentation_clock": {"status": "measured", "variable_intervals": False},
        },
        "shots": [{"id": "s1", "start": 0, "end": 1}, {"id": "s2", "start": 1, "end": 3}],
        "captions": [
            {
                "id": "c1",
                "start": 0.2,
                "end": 0.8,
                "text": "<b>new</b> {\\pos(0,0)}",
                "bbox": [0.1, 0.7, 0.8, 0.1],
            }
        ],
        "style": {},
        "unknowns": [{"field": "original-layers", "status": "unknown"}],
    }


@pytest.mark.parametrize("format", ["native", "csv", "srt", "vtt", "ass", "edl"])
def test_actual_exports_have_loss_receipts_and_verified_bytes(analysis, tmp_path, format):
    receipt = export_analysis(analysis, tmp_path / format, format)
    assert receipt["shot_count"] == 2
    result = verify(tmp_path / format / f"{format}-receipt.json", mode="export")
    assert result["status"] == "passed"
    target = tmp_path / format / receipt["file"]
    target.write_bytes(target.read_bytes() + b"tampered")
    assert verify(tmp_path / format / f"{format}-receipt.json", mode="export")["status"] == "failed"


def test_vtt_and_ass_treat_untrusted_text_as_data(analysis, tmp_path):
    export_analysis(analysis, tmp_path / "vtt", "vtt")
    assert "&lt;b&gt;new&lt;/b&gt;" in (tmp_path / "vtt/subtitles.vtt").read_text()
    export_analysis(analysis, tmp_path / "ass", "ass")
    assert r"\{\\pos(0,0)\}" in (tmp_path / "ass/overlays.ass").read_text()


@pytest.mark.parametrize("clock", [{"status": "unknown"}, {"status": "measured", "variable_intervals": True}])
def test_edl_rejects_unknown_or_variable_presentation_clock(analysis, tmp_path, clock):
    analysis["source"]["presentation_clock"] = clock
    with pytest.raises(ValueError, match="CFR"):
        export_analysis(analysis, tmp_path / "edl", "edl")


def test_otio_actual_parser_round_trip(analysis, tmp_path):
    otio = pytest.importorskip("opentimelineio")
    receipt = export_analysis(analysis, tmp_path / "otio", "otio")
    timeline = otio.adapters.read_from_file(str(tmp_path / "otio" / receipt["file"]))
    clips = list(timeline.find_clips())
    assert len(clips) == 2
    assert timeline.duration().to_seconds() == pytest.approx(3)
    assert [c.source_range.start_time.to_seconds() for c in clips] == [0, 1]
    assert json.loads(timeline.metadata["rea_video"]["unknowns"])[0]["status"] == "unknown"
    assert Path(analysis["source"]["path"]).resolve().as_uri() == clips[0].media_reference.target_url
