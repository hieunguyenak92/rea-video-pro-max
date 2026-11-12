"""Bounded, image-space motion fitting from actual flattened reference pixels.

Tile phase matches initialize robust similarity/affine fits. Residual regions
are held out from direct photometric refinement; overlapping phase patches can
use their pixels during initialization. Distributed residual support can reject
the fit. These are apparent transforms, never identification of a camera,
object, historical editor operation or original animation keys.
"""
from __future__ import annotations

import hashlib
import itertools
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image


MAX_SIDE = 384
MAX_INPUT_PIXELS = 16_000_000
MAX_PAIRS = 192
METHOD = "tiled-phase-robust-affine-held-out-photometric-v1"
LIMITS = [
    "sampled flattened-image apparent motion; camera versus foreground remains unknown",
    "small inter-sample transforms only: scale 0.85..1.18, rotation +/-12 degrees, center translation <=18% per axis",
    "perspective, parallax, nonrigid motion, hidden layers and original keyframes are not recovered",
    "global support and held-out thresholds are rejection rules, not calibrated confidence probabilities",
    "residual regions are held out from direct photometric refinement, not from overlapping phase initialization",
]


def _unknown(reason, **evidence):
    return {"status": "unknown", "method": METHOD, "reason": reason, **evidence, "limits": list(LIMITS)}


def _gray(image, size):
    return np.asarray(image.convert("L").resize(size, Image.Resampling.BILINEAR), dtype=float) / 255


def _sample(array, x, y):
    """Bilinear sample, with explicit validity rather than circular wraparound."""
    height, width = array.shape
    valid = (x >= 0) & (y >= 0) & (x < width - 1) & (y < height - 1)
    x = np.clip(x, 0, width - 1.000001)
    y = np.clip(y, 0, height - 1.000001)
    ix, iy = x.astype(int), y.astype(int)
    fx, fy = x - ix, y - iy
    values = ((1-fx)*(1-fy)*array[iy, ix] + fx*(1-fy)*array[iy, ix+1]
              + (1-fx)*fy*array[iy+1, ix] + fx*fy*array[iy+1, ix+1])
    return values, valid


def _correlation(a, b):
    a, b = a - a.mean(), b - b.mean()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.sum(a*b) / denom) if denom > 1e-10 else None


def _repetitive_texture(array):
    """Reject strong repeated motifs whose displacement is not identifiable."""
    centered = array-array.mean()
    spectrum = np.fft.rfft2(centered)
    autocorrelation = np.fft.irfft2(spectrum*spectrum.conj(), s=array.shape)
    autocorrelation /= max(float(autocorrelation[0, 0]), 1e-10)
    yy, xx = np.indices(array.shape)
    dx, dy = np.minimum(xx, array.shape[1]-xx), np.minimum(yy, array.shape[0]-yy)
    search = (dx*dx+dy*dy >= 36) & (dx <= array.shape[1]//4) & (dy <= array.shape[0]//4)
    return bool(np.max(autocorrelation[search]) > .90)


def _phase(a, b):
    if min(a.std(), b.std()) < .025:
        return None
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    fa, fb = np.fft.rfft2((a-a.mean())*window), np.fft.rfft2((b-b.mean())*window)
    spectrum = fb * fa.conj()
    spectrum /= np.maximum(np.abs(spectrum), 1e-10)
    corr = np.fft.irfft2(spectrum, s=a.shape)
    iy, ix = np.unravel_index(np.argmax(corr), corr.shape)
    peak = float(corr[iy, ix])
    yy, xx = np.indices(corr.shape)
    dx = np.minimum(abs(xx-ix), corr.shape[1]-abs(xx-ix))
    dy = np.minimum(abs(yy-iy), corr.shape[0]-abs(yy-iy))
    second = float(np.max(corr[(dx > 3) | (dy > 3)]))
    ratio = peak / max(second, 1e-8)
    if peak < .055 or ratio < 1.35:
        return None

    def subpixel(before, center, after):
        divisor = before - 2*center + after
        return float(np.clip(.5*(before-after)/divisor, -.5, .5)) if divisor < -1e-8 else 0.

    sx = ix + subpixel(corr[iy, (ix-1) % a.shape[1]], peak, corr[iy, (ix+1) % a.shape[1]])
    sy = iy + subpixel(corr[(iy-1) % a.shape[0], ix], peak, corr[(iy+1) % a.shape[0], ix])
    sx = sx-a.shape[1] if sx > a.shape[1]/2 else sx
    sy = sy-a.shape[0] if sy > a.shape[0]/2 else sy
    # Large circular peak shifts are outside the local matching contract.
    if abs(sx) > a.shape[1]*.35 or abs(sy) > a.shape[0]*.35:
        return None
    yy, xx = np.indices(a.shape, dtype=float)
    warped, valid = _sample(b, xx+sx, yy+sy)
    ncc = _correlation(a[valid], warped[valid])
    if ncc is None or ncc < .35:
        return None
    return sx, sy, peak, ratio


def _tiles(a, b):
    height, width = a.shape
    side = min(96, max(32, min(width, height)//3))
    side += side % 2
    half = side//2
    points, quality = [], []
    for row, cy in enumerate(np.linspace(half+1, height-half-2, 5).astype(int)):
        for col, cx in enumerate(np.linspace(half+1, width-half-2, 6).astype(int)):
            region = np.s_[cy-half:cy+half, cx-half:cx+half]
            shift = _phase(a[region], b[region])
            if shift is not None:
                sx, sy, peak, ratio = shift
                points.append([cx, cy, cx+sx, cy+sy, row, col])
                quality.append({"center": [int(cx), int(cy)], "peak": round(peak, 5), "peak_ratio": round(ratio, 4)})
    return np.asarray(points, dtype=float).reshape(-1, 6), quality


def _fit(points, family):
    source, target = points[:, :2], points[:, 2:4]
    if family == "affine":
        design = np.column_stack((source, np.ones(len(points))))
        if np.linalg.matrix_rank(design) < 3:
            return None
        solution = np.linalg.lstsq(design, target, rcond=None)[0].T
    else:
        x, y = source.T
        design = np.zeros((len(points)*2, 4))
        design[::2] = np.column_stack((x, -y, np.ones(len(points)), np.zeros(len(points))))
        design[1::2] = np.column_stack((y, x, np.zeros(len(points)), np.ones(len(points))))
        if np.linalg.matrix_rank(design) < 4:
            return None
        aa, bb, tx, ty = np.linalg.lstsq(design, target.reshape(-1), rcond=None)[0]
        solution = np.array([[aa, -bb, tx], [bb, aa, ty]])
    return np.vstack((solution, [0, 0, 1]))


def _point_errors(matrix, points):
    predicted = np.column_stack((points[:, :2], np.ones(len(points)))) @ matrix[:2].T
    return np.linalg.norm(predicted-points[:, 2:4], axis=1)


def _robust_fit(points, family):
    required = 3 if family == "affine" else 2
    if len(points) < required+3:
        return None
    combinations = list(itertools.combinations(range(len(points)), required))
    if len(combinations) > 256:
        indices = np.random.default_rng(20261112).choice(len(combinations), 256, replace=False)
        combinations = [combinations[index] for index in indices]
    best, best_score = None, None
    for chosen in combinations:
        matrix = _fit(points[list(chosen)], family)
        if matrix is None:
            continue
        errors = _point_errors(matrix, points)
        score = (int(np.count_nonzero(errors < 2.75)), -float(np.median(errors)))
        if best_score is None or score > best_score:
            best, best_score = matrix, score
    if best is None:
        return None
    for _ in range(3):
        inliers = _point_errors(best, points) < 2.75
        if np.count_nonzero(inliers) < required+2:
            return None
        fitted = _fit(points[inliers], family)
        if fitted is None:
            return None
        best = fitted
    return best


def _refine(a, b, matrix, family):
    """Robust direct alignment excludes residual cells; phase initialization overlaps them."""
    height, width = a.shape
    yy, xx = np.mgrid[3:height-3:3, 3:width-3:3].astype(float)
    train = ((xx*8//width + yy*6//height) % 3) != 0
    x, y, target = xx[train], yy[train], a[yy[train].astype(int), xx[train].astype(int)]
    norm = float(max(width, height))
    xn, yn = (x-width/2)/norm, (y-height/2)/norm
    gy, gx = np.gradient(b)
    for _ in range(18):
        u = matrix[0, 0]*x + matrix[0, 1]*y + matrix[0, 2]
        v = matrix[1, 0]*x + matrix[1, 1]*y + matrix[1, 2]
        observed, valid = _sample(b, u, v)
        if np.count_nonzero(valid) < 200:
            break
        # Independent gain/offset fit avoids confusing uniform lighting with motion.
        ov, tv = observed[valid], target[valid]
        gain = float(np.dot(ov-ov.mean(), tv-tv.mean()) / max(np.sum((ov-ov.mean())**2), 1e-8))
        gain = float(np.clip(gain, .5, 2))
        offset = float(np.mean(tv)-gain*np.mean(ov))
        residual = gain*ov+offset-tv
        gradx = gain*_sample(gx, u, v)[0][valid]
        grady = gain*_sample(gy, u, v)[0][valid]
        if family == "similarity":
            design = np.column_stack((gradx*xn[valid]+grady*yn[valid],
                                      -gradx*yn[valid]+grady*xn[valid], gradx, grady))
        else:
            design = np.column_stack((gradx*xn[valid], gradx*yn[valid], grady*xn[valid],
                                      grady*yn[valid], gradx, grady))
        sigma = max(.015, float(np.median(abs(residual-np.median(residual))))*1.4826)
        weights = np.sqrt(np.minimum(1, 1.5*sigma / np.maximum(abs(residual), 1e-8)))
        step = np.linalg.lstsq(design*weights[:, None], -residual*weights, rcond=None)[0]
        if not np.all(np.isfinite(step)):
            break
        step *= min(1., 2.5/max(np.max(abs(step)), 1e-8))
        if family == "similarity":
            da = np.array([[step[0], -step[1]], [step[1], step[0]]])/norm
            translation = step[2:]
        else:
            da = step[:4].reshape(2, 2)/norm
            translation = step[4:]
        matrix = matrix.copy()
        matrix[:2, :2] += da
        matrix[:2, 2] += translation-da@np.array([width/2, height/2])
        if np.max(abs(step)) < .005:
            break
    return matrix


def _validate_pixels(a, b, matrix):
    height, width = a.shape
    regions, train_errors, held_errors = [], [], []
    for row in range(6):
        for col in range(8):
            # ceil boundaries are exactly the cells selected by floor(y*6/h)
            # and floor(x*8/w) in _refine, including nondivisible dimensions.
            yy, xx = np.mgrid[max(2, (row*height+5)//6):min(height-2, ((row+1)*height+5)//6):2,
                              max(2, (col*width+7)//8):min(width-2, ((col+1)*width+7)//8):2].astype(float)
            u = matrix[0, 0]*xx+matrix[0, 1]*yy+matrix[0, 2]
            v = matrix[1, 0]*xx+matrix[1, 1]*yy+matrix[1, 2]
            warped, valid = _sample(b, u, v)
            if np.mean(valid) < .65:
                continue
            ref, obs = a[yy[valid].astype(int), xx[valid].astype(int)], warped[valid]
            if ref.std() < .025:
                continue
            ncc = _correlation(ref, obs)
            if ncc is None:
                ncc = 0.
            # Z-normalized error permits gain/offset, while penalizing changed content.
            error = float(np.sqrt(np.mean(((ref-ref.mean())/ref.std()
                                          - (obs-obs.mean())/max(obs.std(), 1e-6))**2)))
            held_out = (row+col) % 3 == 0
            (held_errors if held_out else train_errors).append(error)
            regions.append({"row": row, "column": col, "held_out": held_out,
                            "ncc": round(ncc, 5), "normalized_rmse": round(error, 5),
                            "supported": bool(ncc >= .74)})
    supported = [record for record in regions if record["supported"]]
    span_x = (max(record["column"] for record in supported)-min(record["column"] for record in supported))/7 if supported else 0.
    span_y = (max(record["row"] for record in supported)-min(record["row"] for record in supported))/5 if supported else 0.
    return {"regions": regions,
            "held_out_scope": "excluded from direct photometric refinement; overlapping phase initialization can use these pixels",
            "observable_area_fraction": round(len(regions)/48, 5),
            "supported_region_fraction": round(len(supported)/max(1, len(regions)), 5),
            "held_out_regions": len(held_errors), "training_regions": len(train_errors),
            "held_out_normalized_rmse": round(float(np.mean(held_errors)), 6) if held_errors else None,
            "training_normalized_rmse": round(float(np.mean(train_errors)), 6) if train_errors else None,
            "support_span": [round(span_x, 5), round(span_y, 5)]}


def _properties(matrix, size):
    width, height = size
    affine = matrix[:2, :2]
    singular = np.linalg.svd(affine, compute_uv=False)
    center = np.array([width/2, height/2, 1.])
    displacement = (matrix@center-center)[:2]/[width, height]
    return {"scale": float(math.sqrt(max(0, np.linalg.det(affine)))),
            "rotation_degrees": float(math.degrees(math.atan2(affine[1, 0]-affine[0, 1],
                                                                          affine[0, 0]+affine[1, 1]))),
            "axis_scales": singular.tolist(), "center_displacement": displacement.tolist()}


def _bounded(props):
    return (.85 <= props["scale"] <= 1.18 and min(props["axis_scales"]) >= .82
            and max(props["axis_scales"]) <= 1.22 and abs(props["rotation_degrees"]) <= 12
            and max(abs(value) for value in props["center_displacement"]) <= .18)


def estimate_pair(previous: Image.Image, current: Image.Image) -> dict:
    """Estimate a forward normalized-coordinate transform, or explicitly abstain.

    The matrix maps [x/width, y/height, 1] in ``previous`` to ``current``.
    Local matches and pixel residuals refer to a <=384px working raster. The
    Residual regions are held out from direct photometric refinement only;
    overlapping phase initialization can use those pixels.
    """
    if not isinstance(previous, Image.Image) or not isinstance(current, Image.Image):
        raise ValueError("motion inputs must be Pillow images")
    if previous.size != current.size:
        return _unknown("frame dimensions differ")
    width, height = previous.size
    if width*height > MAX_INPUT_PIXELS:
        raise ValueError("motion image exceeds 16,000,000 input pixel budget")
    if min(width, height) < 64:
        return _unknown("frame is too small for distributed motion validation")
    ratio = min(1., MAX_SIDE/max(width, height))
    size = max(64, round(width*ratio)), max(64, round(height*ratio))
    # Preserve aspect: narrow extreme panoramas cannot provide the required support.
    if min(width*ratio, height*ratio) < 64:
        return _unknown("extreme frame aspect leaves insufficient spatial support")
    a, b = _gray(previous, size), _gray(current, size)
    if min(a.std(), b.std()) < .025:
        return _unknown("insufficient image texture", working_size=list(size))
    # One-directional texture cannot identify all affine degrees of freedom.
    gy, gx = np.gradient(a)
    eigen = np.linalg.eigvalsh(np.cov(np.stack((gx.ravel(), gy.ravel()))))
    if eigen[0] < 1e-6 or eigen[0] < eigen[-1]*.015:
        return _unknown("aperture ambiguity: texture does not constrain both axes", working_size=list(size))
    if _repetitive_texture(a):
        return _unknown("repeated-texture ambiguity: multiple displacements produce the same appearance", working_size=list(size))
    points, tile_quality = _tiles(a, b)
    held = ((points[:, 4]+points[:, 5]) % 3 == 0) if len(points) else np.array([], bool)
    train, test = points[~held], points[held]
    matching = {"attempted_tiles": 30, "matched_tiles": len(points), "training_tiles": len(train),
                "held_out_tiles": len(test), "tile_quality": tile_quality}
    if len(train) < 8 or len(test) < 3:
        return _unknown("insufficient unambiguous distributed tile matches", matching=matching, working_size=list(size))
    candidates = []
    for family in ("similarity", "affine"):
        matrix = _robust_fit(train, family)
        if matrix is None:
            continue
        matrix = _refine(a, b, matrix, family)
        props = _properties(matrix, size)
        pixels = _validate_pixels(a, b, matrix)
        errors = _point_errors(matrix, test)
        inlier_fraction = float(np.mean(_point_errors(matrix, points) < 3.5))
        held_error = float(np.median(errors))
        accepted = (_bounded(props) and pixels["observable_area_fraction"] >= .35
                    and pixels["supported_region_fraction"] >= .80 and min(pixels["support_span"]) >= .6
                    and pixels["held_out_regions"] >= 5 and pixels["held_out_normalized_rmse"] < .65
                    and held_error < 3.5 and inlier_fraction >= .70)
        error = pixels["held_out_normalized_rmse"]
        score = (error if error is not None else 10) + (.025 if family == "affine" else 0)
        candidates.append({"family": family, "accepted": bool(accepted), "score": round(score, 6),
                           "held_out_tile_median_error_pixels": round(held_error, 5),
                           "tile_inlier_fraction": round(inlier_fraction, 5), "properties": props,
                           "validation": pixels, "_matrix": matrix})
    public_candidates = [{key: value for key, value in record.items() if key != "_matrix"} for record in candidates]
    accepted = [candidate for candidate in candidates if candidate["accepted"]]
    if not accepted:
        return _unknown("global transform rejected: unsupported, ambiguous, occluded or non-coherent regions",
                        matching=matching, candidates=public_candidates, working_size=list(size))
    best = min(accepted, key=lambda record: record["score"])
    normalizer = np.diag([size[0], size[1], 1.])
    normalized = np.linalg.inv(normalizer)@best["_matrix"]@normalizer
    return {"status": "model-derived", "method": METHOD, "family": best["family"],
            "matrix": np.round(normalized, 9).tolist(), "matrix_coordinates": "normalized-forward-previous-to-current",
            **{key: value for key, value in best["properties"].items()}, "working_size": list(size),
            "matching": matching, "validation": best["validation"], "candidates": public_candidates,
            "model_selection": "residual held out from direct photometric refinement plus 0.025 affine complexity penalty; phase initialization overlaps residual regions",
            "limits": list(LIMITS)}


def _curve(points):
    if len(points) < 6:
        return {"status": "unknown", "reason": "at least six contiguous trajectory samples required for temporal held-out selection"}
    times = np.asarray([point["time"] for point in points], float)
    if times[-1] <= times[0]:
        return {"status": "unknown", "reason": "trajectory has no positive time extent"}
    t = (times-times[0])/(times[-1]-times[0])
    values = np.asarray([point["matrix"] for point in points])[:, :2].reshape(len(points), 6)
    held = np.zeros(len(points), bool)
    held[1:-1:3] = True
    anchors = np.array([[.15, .15, 1], [.85, .15, 1], [.5, .5, 1], [.15, .85, 1], [.85, .85, 1]])
    candidates = []
    for family in ("constant", "linear", "ease-in-out"):
        basis = np.ones((len(t), 1)) if family == "constant" else np.column_stack((np.ones(len(t)), t if family == "linear" else t*t*(3-2*t)))
        coefficients = np.linalg.lstsq(basis[~held], values[~held], rcond=None)[0]
        prediction = (basis@coefficients).reshape(-1, 2, 3)
        discrepancy = (prediction-values.reshape(-1, 2, 3))@anchors.T
        error = float(np.sqrt(np.mean(np.sum(discrepancy[held]**2, axis=1))))
        penalty = .00025*len(coefficients)
        candidates.append({"family": family, "held_out_rmse_normalized": round(error, 8),
                           "complexity_penalty": penalty, "selection_score": round(error+penalty, 8),
                           "coefficients": np.round(coefficients, 9).tolist()})
    best = min(candidates, key=lambda item: item["selection_score"])
    if best["held_out_rmse_normalized"] > .006:
        return {"status": "unknown", "reason": "none of the bounded temporal families explains held-out trajectory samples", "candidates": candidates}
    return {"status": "model-derived", **best, "candidates": candidates, "training_samples": int(np.count_nonzero(~held)),
            "held_out_samples": int(np.count_nonzero(held)), "observed_range": [times[0], times[-1]],
            "basis": "constant: [1]; linear: [1,u]; ease-in-out: [1,u*u*(3-2*u)]; u=(t-start)/(end-start)",
            "value_coordinates": "row-major first two rows of normalized forward cumulative transform",
            "limits": "curve family describes observed image-space trajectory; original animation keys and easing remain unknown"}


def _clock(row):
    pts, base = row.get("pts"), row.get("time_base")
    if not isinstance(pts, int) or isinstance(pts, bool) or not isinstance(base, dict):
        return None
    num, den = base.get("num"), base.get("den")
    if (not isinstance(num, int) or not isinstance(den, int) or isinstance(num, bool)
            or isinstance(den, bool) or num <= 0 or den <= 0):
        return None
    return pts*Fraction(num, den)


def _fraction_record(value):
    return {"num": value.numerator, "den": value.denominator}


def _pair_clock(previous, current, source):
    """Check public seconds against exact source-clock deltas and known origin."""
    first, last = _clock(previous), _clock(current)
    measured = all(row.get("timestamp_status", "measured") == "measured" for row in (previous, current))
    if first is None or last is None or last <= first or not measured:
        return {"status": "unknown", "reason": "missing or non-increasing measured rational PTS"}
    public = []
    ticks = []
    for row in (previous, current):
        seconds = row.get("time")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
            return {"status": "unknown", "reason": "invalid public presentation time"}
        public.append(Fraction(str(seconds)))
        ticks.append(Fraction(row["time_base"]["num"], row["time_base"]["den"]))
    delta, tolerance = last-first, max(ticks)
    result = {"status": "consistent", "duration_rational": _fraction_record(delta),
              "public_duration_rational": _fraction_record(public[1]-public[0]),
              "tolerance_rational": _fraction_record(tolerance), "source_origin_checked": False}
    if abs(public[1]-public[0]-delta) > tolerance:
        return {**result, "status": "unknown", "reason": "public time delta disagrees with rational PTS by more than one source tick"}
    origin = None
    origin_tick = Fraction(0)
    if source.get("start_pts") is not None:
        origin = _clock({"pts": source["start_pts"], "time_base": source.get("time_base")})
        if origin is None:
            return {**result, "status": "unknown", "reason": "source presentation origin has no valid rational clock"}
        origin_tick = Fraction(source["time_base"]["num"], source["time_base"]["den"])
    if source.get("presentation_origin_seconds") is not None:
        seconds = source["presentation_origin_seconds"]
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
            return {**result, "status": "unknown", "reason": "source presentation origin seconds are invalid"}
        reported_origin = Fraction(str(seconds))
        if origin is not None and abs(reported_origin-origin) > max(origin_tick, tolerance):
            return {**result, "status": "unknown", "reason": "source presentation origin seconds disagree with source rational PTS"}
        if origin is None:
            origin = reported_origin
    if origin is not None:
        result.update({"source_origin_checked": True, "source_origin_rational": _fraction_record(origin)})
        for exact, declared, tick in zip((first, last), public, ticks):
            if abs(exact-origin-declared) > max(tick, origin_tick):
                return {**result, "status": "unknown", "reason": "public presentation time disagrees with rational PTS and source origin"}
    return result


def _evidence_image(row, root, source_hash):
    relative = row.get("path")
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("motion evidence path must be relative to the analysis directory")
    path = root/relative
    if not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError("motion evidence must remain inside analysis directory without symlinks")
    if any(parent.is_symlink() for parent in path.parents if parent != root and parent.is_relative_to(root)):
        raise ValueError("motion evidence parent directory must not be a symlink")
    if source_hash and row.get("source_sha256") != source_hash:
        raise ValueError("motion evidence source hash differs from analysis source")
    expected_hash = row.get("sha256")
    if (not isinstance(expected_hash, str) or len(expected_hash) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in expected_hash)):
        raise ValueError("motion evidence requires a valid SHA256 hash")
    try:
        if path.stat().st_size > 32*1024*1024:
            raise ValueError("motion evidence exceeds 32 MiB encoded file budget")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_hash.lower():
            raise ValueError("motion evidence hash mismatch")
        with Image.open(path) as opened:
            if opened.width*opened.height > MAX_INPUT_PIXELS:
                raise ValueError("motion evidence exceeds decoded input pixel budget")
            return opened.convert("RGB")
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError(f"motion evidence could not be read: {exc}") from exc


def _trajectory_point(row, matrix, size):
    # Convert normalized matrix back to square pixel coordinates to measure rotation.
    scale = np.diag([*size, 1.])
    properties = _properties(scale@matrix@np.linalg.inv(scale), size)
    return {"time": row["time"], "pts": row["pts"], "time_base": row["time_base"], "evidence": row["id"],
            "matrix": np.round(matrix, 9).tolist(), **properties}


def analyze_motion(analysis: dict, analysis_dir: Path, *, max_pairs: int = MAX_PAIRS) -> list[dict]:
    """Read hash-checked evidence JPEGs and return cut-reset shot trajectories.

    Does not mutate/write analysis. A rejected pair breaks accumulation: no
    invented transform bridges an occlusion, missing PTS, unsupported jump or cut.
    At most ``max_pairs`` pairs are processed, distributed across shots.
    """
    if isinstance(max_pairs, bool) or not isinstance(max_pairs, int) or not 1 <= max_pairs <= MAX_PAIRS:
        raise ValueError(f"motion max_pairs must be an integer in 1..{MAX_PAIRS}")
    root = Path(analysis_dir).resolve()
    evidence = analysis.get("evidence", [])
    if len(evidence) > 2000:
        raise ValueError("motion evidence list exceeds 2,000 sample budget")
    source = analysis.get("source", {})
    groups = []
    shots = analysis.get("shots", [])
    if len(shots) > 2000:
        raise ValueError("motion shot list exceeds 2,000 shot budget")
    for shot in shots:
        rows = [row for row in evidence if isinstance(row.get("time"), (int, float))
                and math.isfinite(row["time"]) and shot["start"] <= row["time"] < shot["end"]]
        rows.sort(key=lambda row: row["time"])
        # Duplicate PTS cannot add motion evidence.
        rows = [row for index, row in enumerate(rows) if index == 0 or row["time"] > rows[index-1]["time"]]
        groups.append((shot, rows))
    capacities = [max(0, len(rows)-1) for _, rows in groups]
    quotas = [0]*len(groups)
    for _ in range(max_pairs):
        available = [i for i, capacity in enumerate(capacities) if quotas[i] < capacity]
        if not available:
            break
        # Fair coverage first; then reduce the largest remaining sampling gap.
        selected = max(available, key=lambda i: (quotas[i] == 0, capacities[i]/(quotas[i]+1), -i))
        quotas[selected] += 1
    output = []
    for (shot, rows), quota in zip(groups, quotas):
        record = {"id": f"motion-{shot['id']}", "shot_id": shot["id"], "start": shot["start"], "end": shot["end"],
                  "status": "unknown", "method": METHOD, "points": [], "trajectories": [],
                  "evidence": [], "unknowns": ["camera vs object motion", "original keys/easing", "perspective and hidden masks"],
                  "coverage": {"available_samples": len(rows), "selected_pairs": quota,
                               "pairs_omitted_by_budget": max(0, len(rows)-1-quota), "accepted_pairs": 0,
                               "rejected_pairs": 0, "pair_budget": max_pairs}, "limits": list(LIMITS)}
        output.append(record)
        if not quota:
            record["reason"] = "insufficient evidence samples or pair budget exhausted"
            continue
        selected = [rows[index] for index in np.linspace(0, len(rows)-1, quota+1).round().astype(int)]
        segment = []
        cumulative = np.eye(3)
        previous_image = _evidence_image(selected[0], root, source.get("sha256"))
        for previous, current in zip(selected, selected[1:]):
            current_image = _evidence_image(current, root, source.get("sha256"))
            clock = _pair_clock(previous, current, source)
            if clock["status"] != "consistent":
                pair = _unknown(clock["reason"])
            else:
                pair = estimate_pair(previous_image, current_image)
                pair["duration_rational"] = clock["duration_rational"]
            pair["clock_validation"] = clock
            pair.update({"start": previous["time"], "end": current["time"], "time": current["time"],
                         "evidence": [previous["id"], current["id"]],
                         "sample_clock": [{"id": row["id"], "pts": row.get("pts"), "time_base": row.get("time_base")} for row in (previous, current)]})
            record["points"].append(pair)
            if pair["status"] == "model-derived":
                record["coverage"]["accepted_pairs"] += 1
                if not segment:
                    cumulative = np.eye(3)
                    segment = [_trajectory_point(previous, cumulative, previous_image.size)]
                cumulative = np.asarray(pair["matrix"])@cumulative
                segment.append(_trajectory_point(current, cumulative, current_image.size))
            else:
                record["coverage"]["rejected_pairs"] += 1
                if segment:
                    record["trajectories"].append({"points": segment, "curve": _curve(segment)})
                    segment = []
            previous_image = current_image
        if segment:
            record["trajectories"].append({"points": segment, "curve": _curve(segment)})
        record["evidence"] = [row["id"] for row in selected]
        record["coverage"]["observed_range"] = [selected[0]["time"], selected[-1]["time"]]
        record["coverage"]["accepted_fraction"] = record["coverage"]["accepted_pairs"]/quota
        if record["coverage"]["accepted_pairs"]:
            record["status"] = "model-derived"
        if len(record["trajectories"]) == 1 and not record["coverage"]["rejected_pairs"]:
            trajectory = record["trajectories"][0]
            points = trajectory["points"]
            record["scale_start"], record["scale_end"] = points[0]["scale"], points[-1]["scale"]
            record["displacement"] = points[-1]["center_displacement"]
            record["curve"] = trajectory["curve"]
            if trajectory["curve"]["status"] == "model-derived":
                record["family"] = trajectory["curve"]["family"]+"_apparent_transform_candidate"
        else:
            record["reason"] = "no continuous full sampled-shot trajectory; rejected pairs are not bridged"
    return output
