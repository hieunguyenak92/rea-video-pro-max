"""Independent motion review: novel owned patterns, signed geometry and clock integrity."""
import hashlib
import math

import numpy as np
import pytest
from PIL import Image, ImageDraw

from rea_video_pro_max.motion import analyze_motion, estimate_pair
from rea_video_pro_max.render import render_still
from rea_video_pro_max.template import compose, extract_template


def rings(seed=531, size=(320, 224)):
    """An owned chart, authored without either the product renderer or fit algorithm."""
    generator = np.random.default_rng(seed)
    width, height = size
    yy, xx = np.mgrid[:height, :width]
    base = 35 + 55 * xx / width + 35 * yy / height
    pixels = np.repeat(base[:, :, None], 3, axis=2) + generator.normal(0, 9, (height, width, 3))
    image = Image.fromarray(np.clip(pixels, 0, 255).astype("uint8"))
    draw = ImageDraw.Draw(image)
    for _ in range(100):
        cx, cy = int(generator.integers(width)), int(generator.integers(height))
        radius = int(generator.integers(3, 18))
        color = tuple(int(v) for v in generator.integers(5, 250, 3))
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=color, width=2)
        draw.line((cx-radius, cy, cx+radius, cy), fill=color)
    return image


def observed_transform(image, scale, rotation, offset):
    """Pillow inverse sampling, with independently specified forward chart geometry."""
    theta = math.radians(rotation)
    cosine, sine = math.cos(theta), math.sin(theta)
    affine = scale * np.array([[cosine, -sine], [sine, cosine]])
    center = np.asarray(image.size) / 2
    forward = np.eye(3)
    forward[:2, :2] = affine
    forward[:2, 2] = center - affine @ center + offset
    inverse = np.linalg.inv(forward)
    current = image.transform(image.size, Image.Transform.AFFINE, inverse[:2].reshape(-1),
                              Image.Resampling.BICUBIC, fillcolor=(0, 0, 0))
    return current, forward


@pytest.mark.parametrize("scale,rotation,offset", [(.94, 0, (0, 0)), (1, -4, (-7, 6)),
                                                  (1.04, 3, (4, -3)), (1, 0, (-11, 7))])
def test_novel_owned_chart_forward_transform_and_signed_direction(scale, rotation, offset):
    previous = rings()
    current, actual = observed_transform(previous, scale, rotation, offset)
    fit = estimate_pair(previous, current)
    assert fit["status"] == "model-derived", fit
    assert fit["scale"] == pytest.approx(scale, abs=.004)
    assert fit["rotation_degrees"] == pytest.approx(rotation, abs=.2)
    assert fit["center_displacement"] == pytest.approx(np.asarray(offset) / previous.size, abs=.002)
    normalization = np.diag([*previous.size, 1])
    fitted_pixels = normalization @ np.asarray(fit["matrix"]) @ np.linalg.inv(normalization)
    anchors = np.array([[40, 40, 1], [160, 112, 1], [280, 190, 1]])
    error = np.linalg.norm((fitted_pixels @ anchors.T - actual @ anchors.T)[:2], axis=0)
    assert np.max(error) < .6


def evidence_analysis(root):
    folder = root / "evidence"
    folder.mkdir()
    previous = rings()
    current, _ = observed_transform(previous, 1, 0, (4, 0))
    evidence = []
    for index, image in enumerate([previous, current]):
        path = folder / f"frame-{index}.png"
        image.save(path)
        evidence.append({"id": f"frame-{index}", "time": float(index), "pts": index * 1000,
                         "time_base": {"num": 1, "den": 1000}, "timestamp_status": "measured",
                         "path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "source_sha256": "b" * 64})
    return {"source": {"sha256": "b" * 64}, "evidence": evidence,
            "shots": [{"id": "shot-1", "start": 0, "end": 2}]}


def test_rational_pts_and_public_time_cannot_disagree(tmp_path):
    analysis = evidence_analysis(tmp_path)
    analysis["evidence"][1]["time"] = .25  # PTS says 1 second, public clock says 0.25 seconds.
    result = analyze_motion(analysis, tmp_path)[0]
    assert result["coverage"]["accepted_pairs"] == 0, result
    assert result["points"][0]["status"] == "unknown"


def test_hash_checked_motion_requires_an_actual_evidence_hash(tmp_path):
    analysis = evidence_analysis(tmp_path)
    analysis["evidence"][1].pop("sha256")
    with pytest.raises(ValueError, match="hash|digest"):
        analyze_motion(analysis, tmp_path)


def motion_analysis(record):
    return {"kind": "rea-video-analysis", "schema_version": 1,
            "source": {"width": 320, "height": 224, "duration": 1, "sha256": "b" * 64},
            "shots": [{"start": 0, "end": 1}], "captions": [], "motion": [record]}


def test_unknown_motion_parameters_do_not_become_estimated_panzoom():
    template = extract_template(motion_analysis({"scale_start": 1, "scale_end": 1.1, "status": "unknown",
        "family": "affine", "curve": {"status": "unknown"}}))
    assert template["motion"]["family"] == "static", template["motion"]
    assert template["motion"]["status"] == "implementation_choice"


def test_zoom_out_reference_never_silently_becomes_zoom_in(tmp_path):
    record = {"scale_start": 1, "scale_end": .92, "status": "model-derived",
              "family": "linear_apparent_transform_candidate", "curve": {"status": "model-derived", "family": "linear"}}
    template = extract_template(motion_analysis(record))
    image = Image.new("RGB", (320, 224), (5, 15, 25))
    ImageDraw.Draw(image).rectangle((139, 91, 180, 132), fill=(230, 20, 20))
    source = tmp_path / "new-owned-chart.png"
    image.save(source)
    compose(template, {"kind": "rea-video-content", "schema_version": 1, "width": 320, "height": 224, "fps": 10,
                       "scenes": [{"asset": str(source), "duration": 1}]}, tmp_path / "project")
    render_still(tmp_path / "project", 0, tmp_path / "start.png")
    render_still(tmp_path / "project", .99, tmp_path / "end.png")
    def red_area(path):
        pixels = np.asarray(Image.open(path)).astype(int)
        return np.count_nonzero((pixels[:, :, 0] > 180) & (pixels[:, :, 1] < 60))
    # Explicit static abstention is valid; silent direction reversal is not.
    assert red_area(tmp_path / "end.png") <= red_area(tmp_path / "start.png"), template["motion"]
    if template["motion"]["family"] == "static":
        assert template["motion"]["status"] == "implementation_choice"
