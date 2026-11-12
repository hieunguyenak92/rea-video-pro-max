"""Owned motion A2/B2 fixture and independent decoded-output evaluator.

No product analyzer/template/renderer is imported. Gold is evaluator-only.
Make: python tools/make_motion_fixture.py --out /private/tmp/rvpm-motion-demo/fixtures
Evaluate: python tools/make_motion_fixture.py --evaluate /private/tmp/rvpm-motion-demo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


WIDTH, HEIGHT, FPS, SHOT_SECONDS = 640, 360, 24, 3
SHOT_FRAMES = FPS*SHOT_SECONDS


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_chart(seed, palette):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[:HEIGHT, :WIDTH]
    gradient = 12*np.sin(xx/157)+10*yy/HEIGHT
    pixels = np.asarray(palette)[None, None, :]+gradient[:, :, None]+rng.normal(0, 17, (HEIGHT, WIDTH, 3))
    image = Image.fromarray(np.clip(pixels, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(.55))
    draw = ImageDraw.Draw(image)
    # Nonrepeating centers, radii, spokes and marks constrain both spatial axes.
    for _ in range(185):
        x, y = int(rng.integers(WIDTH)), int(rng.integers(HEIGHT))
        radius = int(rng.integers(4, 23))
        color = tuple(int(c) for c in rng.integers(35, 250, 3))
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=color, width=2)
        draw.line((x-radius, y, x+radius//2, y+radius//3), fill=color, width=2)
        draw.rectangle((x-2, y-2, x+2, y+2), fill=color)
    return image


def new_chart(index):
    image = Image.new("RGB", (WIDTH, HEIGHT), [(12, 44, 67), (38, 25, 79)][index])
    draw = ImageDraw.Draw(image)
    color = [(255, 210, 90), (80, 222, 225)][index]
    for x, y, radius in [(90, 80, 28), (530, 95, 45), (120, 255, 40), (520, 265, 24)]:
        if index == 0:
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=color, width=7)
        else:
            draw.polygon([(x, y-radius), (x+radius, y), (x, y+radius), (x-radius, y)], outline=color, width=6)
    draw.line((155, 180, 485, 180), fill=color, width=3)
    # A unique red central marker gives a decoded pixel measurement of B motion.
    draw.rounded_rectangle((288, 155, 352, 205), radius=9, fill=(240, 25, 35))
    draw.line((307, 180, 333, 180), fill="white", width=3)
    draw.line((320, 167, 320, 193), fill="white", width=3)
    return image


def zoom(image, scale, fill):
    cx, cy = WIDTH/2, HEIGHT/2
    # Independently authored inverse mapping, without product crop/warp helpers.
    inverse = (1/scale, 0, cx-cx/scale, 0, 1/scale, cy-cy/scale)
    return image.transform(image.size, Image.Transform.AFFINE, inverse, Image.Resampling.BICUBIC, fillcolor=fill)


def source_scale(shot, seconds):
    local_frame = (seconds-shot*SHOT_SECONDS)*FPS
    u = min(1., max(0., local_frame/(SHOT_FRAMES-1)))
    return 1+.15*u if shot == 0 else 1-.12*u*u*(3-2*u)


def make(out):
    if out.exists():
        raise ValueError("fixture destination already exists; preserve prior evidence")
    out.mkdir(parents=True)
    palettes = [(22, 47, 89), (137, 49, 30)]
    charts = [reference_chart(531, palettes[0]), reference_chart(973, palettes[1])]
    for index, chart in enumerate(charts):
        chart.save(out/f"reference-chart-{index+1}.png")
        new_chart(index).save(out/f"new-content-{index+1}.png")
    command = ["ffmpeg", "-v", "error", "-nostdin", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
               "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               str(out/"reference-a2.mp4")]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for number in range(SHOT_FRAMES*2):
            shot = number//SHOT_FRAMES
            frame = zoom(charts[shot], source_scale(shot, number/FPS), tuple(palettes[shot]))
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        errors = encoder.stderr.read().decode(errors="replace")
        if encoder.wait(timeout=60):
            raise RuntimeError("owned reference encode failed: "+errors[-2000:])
    finally:
        if encoder.poll() is None:
            encoder.kill()
            encoder.wait()
    content = {"schema_version": 1, "kind": "rea-video-content", "width": WIDTH, "height": HEIGHT,
               "fps": FPS, "scenes": [
                   {"id": "new-growth", "asset": "new-content-1.png", "duration": 3, "text": "NEW SIGNAL GROWS"},
                   {"id": "new-breath", "asset": "new-content-2.png", "duration": 3, "text": "NEW STORY BREATHES"}]}
    write(out/"content-b2.json", content)
    gold = {"kind": "owned-motion-evaluator-only-gold", "schema_version": 1,
            "authoring": "Independent Pillow inverse image sampling and FFmpeg H.264 encoding; no product renderer imports",
            "input": {"path": "reference-a2.mp4", "sha256": digest(out/"reference-a2.mp4"),
                      "width": WIDTH, "height": HEIGHT, "fps": FPS, "frames": SHOT_FRAMES*2, "duration": 6},
            "shots": [{"start": 0, "end": 3, "scale_start": 1, "scale_end": 1.15, "curve": "linear"},
                      {"start": 3, "end": 6, "scale_start": 1, "scale_end": .88, "curve": "ease-in-out"}],
            "scale_time_definition": "u=clamp((time-shot_start)*24/71,0,1); first=1+.15*u; second=1-.12*u*u*(3-2*u)",
            "new_content_sha256": {f"new-content-{i+1}.png": digest(out/f"new-content-{i+1}.png") for i in range(2)},
            "caption_scope": "A has no captions; B text is new user-supplied content using the template's declared fallback caption styling",
            "thresholds": {"observed_scale_absolute_error": .012, "b_scale_absolute_error": .025,
                           "cut_time_error_seconds": 1/FPS, "minimum_direction_area_change": .03}}
    write(out/"hidden-motion-gold.json", gold)
    return {"status": "created", "fixtures": str(out), "reference": str(out/"reference-a2.mp4")}


def decoded_checkpoints(path, scene_starts, destination):
    destination.mkdir(exist_ok=True)
    records = [[] for _ in scene_starts]
    with av.open(str(path)) as container:
        origin = None
        for frame in container.decode(video=0):
            if frame.pts is None or frame.time_base is None:
                raise ValueError("decoded demo frame has no actual PTS")
            stamp = float(frame.pts*frame.time_base)
            if origin is None:
                origin = stamp
            time = stamp-origin
            index = max(i for i, start in enumerate(scene_starts) if time >= start-1e-8)
            image = frame.to_image().convert("RGB")
            pixels = np.asarray(image, dtype=int)
            red = (pixels[:, :, 0] > 180) & (pixels[:, :, 1] < 70) & (pixels[:, :, 2] < 80)
            records[index].append({"time": time, "pts": frame.pts, "time_base": str(frame.time_base),
                                   "marker_area": int(np.count_nonzero(red)), "_image": image})
    output = []
    for index, frames in enumerate(records):
        if not frames:
            raise ValueError("rendered motion scene has no decoded frames")
        first, last = frames[0], frames[-1]
        for label, record in (("start", first), ("end", last)):
            path = destination/f"scene-{index+1}-{label}.png"
            record["_image"].save(path)
            record["checkpoint"] = str(path)
        output.append({"first": {k: v for k, v in first.items() if k != "_image"},
                       "last": {k: v for k, v in last.items() if k != "_image"},
                       "decoded_frames": len(frames),
                       "marker_area_trajectory": [{k: v for k, v in row.items() if k not in {"_image", "checkpoint"}} for row in frames]})
    return output


def evaluate(work):
    gold = json.loads((work/"fixtures/hidden-motion-gold.json").read_text())
    analysis = json.loads((work/"analysis/analysis.json").read_text())
    template = json.loads((work/"style-template.json").read_text())
    project = json.loads((work/"project/project.json").read_text())
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("source-integrity", analysis["source"]["sha256"] == gold["input"]["sha256"], analysis["source"]["sha256"])
    check("two-observed-shots", len(analysis["shots"]) == 2, analysis["shots"])
    check("two-source-motion-records", len(analysis["motion"]) == 2, len(analysis["motion"]))
    check("owned-cut-time", len(analysis["shots"]) == 2 and abs(analysis["shots"][1]["start"]-3) <= 1/FPS,
          [shot["start"] for shot in analysis["shots"]])
    check("no-spurious-source-captions", not analysis.get("captions"),
          [{key: caption.get(key) for key in ("id", "text", "start", "end", "bbox", "engine_score")}
           for caption in analysis.get("captions", [])])
    motion_results = []
    for index, motion in enumerate(analysis["motion"]):
        expected = gold["shots"][min(index, 1)]
        if "scale_end" not in motion:
            check(f"source-shot-{index+1}-continuous-trajectory", False, motion.get("coverage"))
            continue
        trajectory = motion["trajectories"][0]["points"]
        start, end = trajectory[0]["time"], trajectory[-1]["time"]
        expected_ratio = source_scale(index, end)/source_scale(index, start)
        observed_ratio = motion["scale_end"]/motion["scale_start"]
        curve = motion.get("curve", {})
        error = abs(expected_ratio-observed_ratio)
        check(f"source-shot-{index+1}-observed-signed-scale", error <= .012,
              {"expected_over_observed_interval": expected_ratio, "measured": observed_ratio, "absolute_error": error,
               "observed_interval": [start, end], "authored_full_shot_end_scale": expected["scale_end"]})
        check(f"source-shot-{index+1}-curve-family", curve.get("status") == "model-derived" and curve.get("family") == expected["curve"],
              {key: curve.get(key) for key in ("status", "family", "held_out_samples", "held_out_rmse_normalized", "candidates")})
        motion_results.append({"shot": index+1, "expected_observed_scale_ratio": expected_ratio,
                               "measured_scale_ratio": observed_ratio, "scale_absolute_error": error,
                               "curve": curve.get("family"), "coverage": motion["coverage"]})
    check("two-new-scenes", len(project["scenes"]) == 2, [scene["id"] for scene in project["scenes"]])
    media = [asset for asset in project["assets"] if asset["role"] == "media"]
    check("explicit-different-image-bindings", len(media) == 2 and {item["sha256"] for item in media} == set(gold["new_content_sha256"].values()), media)
    decoded = decoded_checkpoints(work/"video-b2.mp4", [scene["start"] for scene in project["scenes"]], work/"playback-evidence")
    for index, (scene, observed) in enumerate(zip(project["scenes"], decoded)):
        first, last = observed["first"]["marker_area"], observed["last"]["marker_area"]
        area_ratio = last/max(1, first)
        measured_scale = math.sqrt(area_ratio)
        ratio = scene.get("motion", {}).get("scale_ratio", 1)
        direction_ok = area_ratio > 1.03 if index == 0 else area_ratio < .97
        check(f"b-shot-{index+1}-actual-marker-direction", direction_ok,
              {"first_area": first, "last_area": last, "area_ratio": area_ratio, "scale_from_decoded_marker": measured_scale,
               "bound_motion": scene.get("motion")})
        check(f"b-shot-{index+1}-approximate-marker-scale", abs(measured_scale-ratio) <= .025,
              {"marker_scale": measured_scale, "transferred_sampled_scale_ratio": ratio})
        observed["area_ratio"] = area_ratio
        observed["scale_from_marker_area"] = measured_scale
    check("actual-b-complete-decode", sum(row["decoded_frames"] for row in decoded) == gold["input"]["frames"],
          sum(row["decoded_frames"] for row in decoded))
    native_verification = work/"b2-verification.json"
    if native_verification.is_file():
        verification = json.loads(native_verification.read_text())
        check("native-style-transfer-verification", verification.get("status") == "passed",
              {"path": str(native_verification), "status": verification.get("status"),
               "failed_checks": [row["name"] for row in verification.get("checks", []) if not row["passed"]]})
    else:
        check("native-style-transfer-verification", False, "run native style-transfer verify with --ocr-lang eng")
    motion_checks = [row for row in checks if row["name"].startswith(("source-shot-", "b-shot-"))
                     or row["name"] in {"two-observed-shots", "two-source-motion-records", "owned-cut-time"}]
    result = {"kind": "owned-motion-pipeline-evaluation", "schema_version": 1,
              "status": "passed" if all(row["passed"] for row in checks) else "failed", "checks": checks,
              "motion_only_status": "passed" if all(row["passed"] for row in motion_checks) else "failed",
              "source_motion": motion_results, "b_playback": decoded, "template_motion": template["motion"],
              "inputs": {"reference_sha256": digest(work/"fixtures/reference-a2.mp4"),
                         "video_b_sha256": digest(work/"video-b2.mp4"), "gold": str(work/"fixtures/hidden-motion-gold.json")},
              "limits": ["Owned synthetic two-shot zoom fixture; not a general footage benchmark",
                         "A full authored endpoints differ from sampled observed interval endpoints; both are reported",
                         "B uses independently supplied media and bounded center crops; no original source layers or camera identified",
                         "Marker area verifies signed B scale from decoded pixels; finite rasterization/encoding affects the estimate",
                         "A contains no authored captions; B subtitle appearance cannot be credited as recovered A treatment"]}
    write(work/"motion-evaluation.json", result)
    return {"status": result["status"], "evaluation": str(work/"motion-evaluation.json"),
            "checks": len(checks), "failed": [row["name"] for row in checks if not row["passed"]]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--out", type=Path)
    modes.add_argument("--evaluate", type=Path)
    arguments = parser.parse_args()
    result = evaluate(arguments.evaluate.resolve()) if arguments.evaluate else make(arguments.out.resolve())
    print(json.dumps(result))
    raise SystemExit(1 if result["status"] == "failed" else 0)
