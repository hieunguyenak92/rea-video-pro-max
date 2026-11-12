"""Owned image authoring independent of the product renderer and motion fitter."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter

from rea_video_pro_max import motion
from rea_video_pro_max.motion import analyze_motion, estimate_pair


def _texture(seed=42, size=(384, 256)):
    rng = np.random.default_rng(seed)
    array = rng.integers(15, 240, (size[1], size[0], 3), dtype=np.uint8)
    image = Image.fromarray(array).filter(ImageFilter.GaussianBlur(1.1))
    draw = ImageDraw.Draw(image)
    for _ in range(80):
        x, y = rng.integers(0, size[0]-12), rng.integers(0, size[1]-12)
        color = tuple(int(value) for value in rng.integers(25, 230, 3))
        draw.rectangle((x, y, x+int(rng.integers(3, 16)), y+int(rng.integers(3, 16))), fill=color)
    return image


def _matrix(size, scale=1., degrees=0., dx=0., dy=0., anisotropy=1., shear=0.):
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    affine = np.array([[cosine, -sine], [sine, cosine]])@np.array([[scale*anisotropy, shear], [0, scale/anisotropy]])
    center = np.asarray(size)/2
    matrix = np.eye(3)
    matrix[:2, :2] = affine
    matrix[:2, 2] = center-affine@center+[dx, dy]
    return matrix


def _warp(image, matrix):
    inverse = np.linalg.inv(matrix)
    return image.transform(image.size, Image.Transform.AFFINE, inverse[:2].reshape(-1),
                           Image.Resampling.BICUBIC, fillcolor=(3, 7, 11))


@pytest.mark.parametrize("scale,degrees,dx,dy", [(1., 0., 7., -4.), (1.06, 0., 0., 0.),
                                                (1., 3.5, 0., 0.), (1.035, -2.5, 5., 3.)])
def test_similarity_measures_owned_zoom_rotation_translation(scale, degrees, dx, dy):
    previous = _texture()
    current = _warp(previous, _matrix(previous.size, scale, degrees, dx, dy))
    result = estimate_pair(previous, current)
    assert result["status"] == "model-derived", result
    assert result["family"] == "similarity"
    assert result["scale"] == pytest.approx(scale, abs=.006)
    assert result["rotation_degrees"] == pytest.approx(degrees, abs=.25)
    assert result["center_displacement"] == pytest.approx([dx/previous.width, dy/previous.height], abs=.003)
    assert result["validation"]["held_out_regions"] >= 5
    assert result["validation"]["held_out_normalized_rmse"] < .65
    assert result["validation"]["supported_region_fraction"] >= .8
    json.dumps(result, allow_nan=False)


def test_affine_can_win_when_anisotropy_is_visible_on_held_out_pixels():
    previous = _texture(6)
    current = _warp(previous, _matrix(previous.size, anisotropy=1.035, shear=.025, dx=2))
    result = estimate_pair(previous, current)
    assert result["status"] == "model-derived", result
    assert result["family"] == "affine"
    assert max(result["axis_scales"])-min(result["axis_scales"]) > .05
    affine = next(candidate for candidate in result["candidates"] if candidate["family"] == "affine")
    similarity = next(candidate for candidate in result["candidates"] if candidate["family"] == "similarity")
    assert affine["validation"]["held_out_normalized_rmse"] < similarity["validation"]["held_out_normalized_rmse"]


def test_abstains_on_blank_aperture_ambiguity_cut_and_nonrigid_regions():
    blank = Image.new("RGB", (384, 256), "gray")
    assert estimate_pair(blank, blank)["status"] == "unknown"
    stripes = np.tile(((np.arange(384)//8 % 2)*255).astype(np.uint8), (256, 1))
    striped = Image.fromarray(stripes).convert("RGB")
    assert "aperture" in estimate_pair(striped, _warp(striped, _matrix(striped.size, dx=8)))["reason"]
    yy, xx = np.indices((256, 384))
    checker = Image.fromarray((((xx//8+yy//8) % 2)*255).astype(np.uint8)).convert("RGB")
    # A two-axis repeated motif can have perfect residual under several motions.
    assert "repeated-texture ambiguity" in estimate_pair(checker, checker)["reason"]
    original = _texture()
    assert estimate_pair(original, _texture(121))["status"] == "unknown"
    nonrigid = _warp(original, _matrix(original.size, dx=8))
    opposite = _warp(original, _matrix(original.size, dx=-8))
    nonrigid.paste(opposite.crop((192, 0, 384, 256)), (192, 0))
    assert estimate_pair(original, nonrigid)["status"] == "unknown"
    occluded = _warp(original, _matrix(original.size, dx=5))
    occluded.paste(_texture(12).crop((0, 0, 145, 256)), (0, 0))
    assert estimate_pair(original, occluded)["status"] == "unknown"


def _analysis(tmp_path, frames, times=None, split=None):
    evidence_dir = tmp_path/"evidence"
    evidence_dir.mkdir(exist_ok=True)
    rows = []
    times = list(range(len(frames))) if times is None else times
    for index, (image, time) in enumerate(zip(frames, times)):
        path = evidence_dir/f"frame-{index:08d}.jpg"
        image.save(path, quality=96)
        rows.append({"id": path.stem, "index": index, "time": time, "pts": round(time*1000),
                     "time_base": {"num": 1, "den": 1000}, "timestamp_status": "measured",
                     "path": str(path.relative_to(tmp_path)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "source_sha256": "owned-source"})
    end = times[-1]+1
    shots = [{"id": "shot-1", "start": 0., "end": end}]
    if split is not None:
        shots = [{"id": "shot-1", "start": 0., "end": split}, {"id": "shot-2", "start": split, "end": end}]
    return {"source": {"sha256": "owned-source"}, "evidence": rows, "shots": shots}


@pytest.mark.parametrize("family", ["constant", "linear", "ease-in-out"])
def test_observed_trajectory_curve_uses_held_out_samples_and_rational_pts(tmp_path, family):
    image = _texture(87)
    times = np.linspace(0, 2, 9).tolist()
    frames = []
    for time in times:
        u = time/2
        progress = 0 if family == "constant" else u if family == "linear" else u*u*(3-2*u)
        frames.append(_warp(image, _matrix(image.size, scale=1+.10*progress, dx=12*progress)))
    result = analyze_motion(_analysis(tmp_path, frames, times), tmp_path)[0]
    assert result["status"] == "model-derived", result
    assert result["coverage"]["accepted_pairs"] == 8
    assert result["curve"]["family"] == family
    assert result["curve"]["held_out_samples"] >= 2
    assert result["scale_end"] == pytest.approx(1 if family == "constant" else 1.1, abs=.012)
    assert all(point["duration_rational"] == {"num": 1, "den": 4} for point in result["points"])
    assert result["points"][0]["sample_clock"][0]["pts"] == 0
    assert result["points"][0]["sample_clock"][1]["time_base"] == {"num": 1, "den": 1000}
    json.dumps(result, allow_nan=False)


def test_cut_resets_motion_without_comparing_or_accumulating_across_boundary(tmp_path):
    first, second = _texture(11), _texture(29)
    frames = [_warp(first, _matrix(first.size, dx=3*i)) for i in range(4)]
    frames += [_warp(second, _matrix(second.size, dx=-2*i)) for i in range(4)]
    result = analyze_motion(_analysis(tmp_path, frames, split=4), tmp_path)
    assert len(result) == 2
    assert [record["coverage"]["accepted_pairs"] for record in result] == [3, 3]
    assert result[0]["displacement"][0] == pytest.approx(9/384, abs=.004)
    assert result[1]["displacement"][0] == pytest.approx(-6/384, abs=.004)
    for record in result:
        first_point = record["trajectories"][0]["points"][0]
        assert np.asarray(first_point["matrix"]) == pytest.approx(np.eye(3))
        assert all(point["start"] >= record["start"] and point["end"] < record["end"] for point in record["points"])
    assert result[0]["points"][-1]["evidence"][1] != result[1]["points"][0]["evidence"][0]


def test_rejected_pair_breaks_trajectory_instead_of_bridging_observation_gap(tmp_path):
    first, second = _texture(4), _texture(105)
    frames = [first, _warp(first, _matrix(first.size, dx=3)), second,
              _warp(second, _matrix(second.size, dx=3))]
    result = analyze_motion(_analysis(tmp_path, frames), tmp_path)[0]
    assert result["coverage"]["accepted_pairs"] == 2
    assert result["coverage"]["rejected_pairs"] == 1
    assert len(result["trajectories"]) == 2
    assert "scale_end" not in result
    assert "curve" not in result


def test_evidence_hash_escape_missing_pts_and_budget_are_explicit(tmp_path):
    image = _texture()
    frames = [_warp(image, _matrix(image.size, dx=i)) for i in range(7)]
    analysis = _analysis(tmp_path, frames)
    result = analyze_motion(analysis, tmp_path, max_pairs=3)[0]
    assert result["coverage"]["selected_pairs"] == 3
    assert result["coverage"]["pairs_omitted_by_budget"] == 3
    assert result["coverage"]["observed_range"] == [0, 6]
    analysis["evidence"][2]["pts"] = None
    result = analyze_motion(analysis, tmp_path)[0]
    assert result["coverage"]["rejected_pairs"] == 2
    analysis["evidence"][2]["pts"] = 2000
    analysis["evidence"][2]["timestamp_status"] = "estimated-from-nominal-fps"
    assert analyze_motion(analysis, tmp_path)[0]["coverage"]["rejected_pairs"] == 2
    analysis["evidence"][0]["sha256"] = "0"*64
    with pytest.raises(ValueError, match="hash mismatch"):
        analyze_motion(analysis, tmp_path)
    analysis["evidence"][0]["path"] = "../external.jpg"
    with pytest.raises(ValueError, match="inside"):
        analyze_motion(analysis, tmp_path)


def test_invalid_pair_inputs_and_dimensions_are_bounded():
    image = _texture()
    with pytest.raises(ValueError, match="Pillow"):
        estimate_pair(np.zeros((100, 100)), image)
    assert estimate_pair(image, image.resize((192, 128)))["status"] == "unknown"
    assert estimate_pair(image.resize((32, 32)), image.resize((32, 32)))["status"] == "unknown"
    with pytest.raises(ValueError, match="max_pairs"):
        analyze_motion({}, Path("."), max_pairs=193)


def test_public_clock_delta_and_known_origin_must_match_rational_pts(tmp_path):
    image = _texture()
    frames = [image, _warp(image, _matrix(image.size, dx=3))]
    analysis = _analysis(tmp_path, frames)
    analysis["evidence"][1]["time"] = .25
    result = analyze_motion(analysis, tmp_path)[0]
    assert result["coverage"]["accepted_pairs"] == 0
    assert "public time delta" in result["points"][0]["reason"]
    # A common offset is only identifiable when the source origin is supplied.
    analysis["evidence"][1]["time"] = 1.
    for row in analysis["evidence"]:
        row["pts"] += 7000
    analysis["source"].update({"start_pts": 7000, "time_base": {"num": 1, "den": 1000},
                               "presentation_origin_seconds": 7.})
    result = analyze_motion(analysis, tmp_path)[0]
    assert result["coverage"]["accepted_pairs"] == 1
    assert result["points"][0]["clock_validation"]["source_origin_checked"]
    for row in analysis["evidence"]:
        row["pts"] += 1000
    result = analyze_motion(analysis, tmp_path)[0]
    assert result["coverage"]["accepted_pairs"] == 0
    assert "source origin" in result["points"][0]["reason"]


def test_public_clock_comparison_uses_exact_one_tick_tolerance(tmp_path):
    image = _texture()
    analysis = _analysis(tmp_path, [image, _warp(image, _matrix(image.size, dx=3))])
    analysis["evidence"][1]["time"] = 1.001
    assert analyze_motion(analysis, tmp_path)[0]["coverage"]["accepted_pairs"] == 1
    analysis["evidence"][1]["time"] = 1.001000001
    assert analyze_motion(analysis, tmp_path)[0]["coverage"]["accepted_pairs"] == 0


@pytest.mark.parametrize("missing_hash", [None, "", "a"*63, "z"*64])
def test_evidence_hash_is_mandatory_and_validated(tmp_path, missing_hash):
    image = _texture()
    analysis = _analysis(tmp_path, [image, image])
    if missing_hash is None:
        analysis["evidence"][1].pop("sha256")
    else:
        analysis["evidence"][1]["sha256"] = missing_hash
    with pytest.raises(ValueError, match="hash"):
        analyze_motion(analysis, tmp_path)


def test_direct_fit_and_held_out_residual_pixels_are_disjoint_for_nondivisible_dimensions(monkeypatch):
    # Capture actual sample coordinates, not a copy of the partition formula.
    image = _texture(size=(319, 223)).convert("L")
    pixels = np.asarray(image, dtype=float)/255
    original_sample = motion._sample
    calls = []

    def capture(array, x, y):
        calls.append(set(zip(x.ravel().astype(int), y.ravel().astype(int))))
        return original_sample(array, x, y)

    monkeypatch.setattr(motion, "_sample", capture)
    motion._refine(pixels, pixels, np.eye(3), "similarity")
    direct_fit = calls[0]
    calls.clear()
    validation = motion._validate_pixels(pixels, pixels, np.eye(3))
    assert len(calls) == 48
    assert len(validation["regions"]) == 48
    held_out = set()
    for region, sampled in zip(validation["regions"], calls):
        if region["held_out"]:
            held_out.update(sampled)
    assert len(direct_fit) > 1000 and len(held_out) > 1000
    assert direct_fit.isdisjoint(held_out)
    assert "phase initialization" in validation["held_out_scope"]
