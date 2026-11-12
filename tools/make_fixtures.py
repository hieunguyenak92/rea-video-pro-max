"""Owned independent media authoring: does NOT import the product renderer/analyzer.

Use --out /tmp/rea-fixtures. The gold file is only consumed by the evaluator,
never supplied to the analyzer. All illustrations/audio are synthesized here.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "skills/rea-video-pro-max/assets/fonts/BeVietnamPro-Bold.ttf"
WIDTH, HEIGHT, FPS = 640, 360, 24


def illustration(index, t=0, *, new=False):
    palettes = (
        [(19, 40, 72), (68, 25, 52), (23, 61, 47)] if not new else [(31, 40, 101), (96, 43, 20), (11, 65, 83)]
    )
    accent = [(110, 230, 242), (255, 160, 106), (179, 241, 129)][index]
    base = np.asarray(palettes[index], dtype=float)
    y, x = np.mgrid[0:HEIGHT, 0:WIDTH]
    light = (1 - ((x - WIDTH * 0.65) ** 2 + (y - HEIGHT * 0.25) ** 2) / (WIDTH**2)) * 0.27
    rgb = np.clip(base[None, None, :] * (1 + light[:, :, None]), 0, 255).astype("uint8")
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    # Lines and diagrams deliberately contain no words; OCR gold is only captions.
    for gx in range(20, WIDTH, 40):
        draw.line((gx, 0, gx, HEIGHT), fill=tuple(int(c * 1.2) for c in base), width=1)
    for gy in range(20, HEIGHT, 40):
        draw.line((0, gy, WIDTH, gy), fill=tuple(int(c * 1.2) for c in base), width=1)
    shift = round(22 * math.sin(t * 0.8))
    if index == 0:
        for radius in (85, 60, 35):
            draw.ellipse(
                (320 - radius + shift, 125 - radius, 320 + radius + shift, 125 + radius),
                outline=accent,
                width=3,
            )
        draw.line((170, 125, 470, 125), fill=accent, width=2)
    elif index == 1:
        for i in range(5):
            top = 185 - int(30 + 100 * (0.3 + 0.7 * abs(math.sin(i * 0.9 + t * 0.2))))
            draw.rounded_rectangle(
                (180 + i * 61 + shift, top, 214 + i * 61 + shift, 200), radius=8, fill=accent
            )
    else:
        nodes = [
            (180 + shift, 90),
            (320 + shift, 65),
            (460 + shift, 125),
            (320 + shift, 195),
            (180 + shift, 190),
        ]
        for a, b in zip(nodes, nodes[1:] + nodes[:1]):
            draw.line((*a, *b), fill=accent, width=3)
        for cx, cy in nodes:
            draw.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=accent)
    draw.line((35, 235, 605, 235), fill=accent, width=2)
    # Graphic progress bars are known illustration primitives, not subtitle layers.
    draw.rounded_rectangle((35, 22, 115 + index * 70, 27), radius=2, fill=accent)
    return image


def encode_frames(frames, path, fps=FPS):
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(path),
        ],
        stdin=subprocess.PIPE,
    )
    try:
        for frame in frames:
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        if process.wait(timeout=30):
            raise RuntimeError("Fixture encoding failed")
    finally:
        if process.poll() is None:
            process.kill()


def tone(path, duration, onsets):
    rate = 48000
    data = np.zeros(round(duration * rate), dtype=float)
    for i, start in enumerate(onsets):
        ticks = np.arange(round(0.12 * rate)) / rate
        sound = 0.28 * np.sin(2 * np.pi * (520 + i * 170) * ticks) * np.sin(np.pi * ticks / 0.12) ** 2
        offset = round(start * rate)
        data[offset : offset + len(sound)] += sound[: len(data) - offset]
    with wave.open(str(path), "wb") as audio:
        audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        audio.writeframes((data * 32767).astype("<i2").tobytes())


def make(out):
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(FONT), 32)
    captions = ["WATCH THE RHYTHM", "READ THE MOMENT", "MAKE SOMETHING NEW"]
    cuts = [0, 2.5, 5.5, 9.0]
    cues = [(cuts[i] + 0.25, cuts[i + 1] - 0.25) for i in range(3)]

    def frames():
        for f in range(9 * FPS):
            t = f / FPS
            scene = next(i for i in range(3) if cuts[i] <= t < cuts[i + 1])
            image = illustration(scene, t)
            draw = ImageDraw.Draw(image)
            if cues[scene][0] <= t < cues[scene][1]:
                draw.text(
                    (WIDTH / 2, HEIGHT * 0.80),
                    captions[scene],
                    font=font,
                    anchor="mm",
                    fill="white",
                    stroke_width=2,
                    stroke_fill=(3, 5, 10),
                )
            yield image

    encode_frames(frames(), out / "reference-silent.mp4")
    tone(out / "reference-audio.wav", 9, [0, 2.5, 5.5, 8.5])
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(out / "reference-silent.mp4"),
            "-i",
            str(out / "reference-audio.wav"),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out / "reference.mp4"),
        ],
        check=True,
        timeout=30,
    )
    for i in (0, 2):
        illustration(i, new=True).save(out / f"new-{i}.png")
    encode_frames((illustration(1, f / FPS, new=True) for f in range(4 * FPS)), out / "new-footage.mp4")
    tone(out / "new-audio.wav", 10.8, [0, 3, 6.6, 10.4])
    content = {
        "schema_version": 1,
        "kind": "rea-video-content",
        "width": 640,
        "height": 360,
        "fps": 24,
        "audio": "new-audio.wav",
        "scenes": [
            {"id": "idea", "text": "BUILD A FRESH IDEA", "asset": "new-0.png", "duration": 3},
            {"id": "craft", "text": "EDIT WITH CLEAR INTENT", "asset": "new-footage.mp4", "duration": 3.6},
            {"id": "publish", "text": "CREATE YOUR OWN STORY", "asset": "new-2.png", "duration": 4.2},
        ],
    }
    (out / "content.json").write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    gold = {
        "kind": "owned-independent-fixture-gold",
        "generator": "tools/make_fixtures.py",
        "duration": 9,
        "fps": 24,
        "cuts": cuts[1:-1],
        "captions": [{"text": text, "start": span[0], "end": span[1]} for text, span in zip(captions, cues)],
        "style": {"font_size": 32, "anchor_y": 0.80, "fill": [255, 255, 255], "stroke_width": 2},
        "audio_onsets": [0, 2.5, 5.5, 8.5],
        "thresholds": {
            "cut_tolerance_seconds": 1 / 24,
            "cut_f1": 0.95,
            "clean_caption_cer": 0.05,
            "cue_boundary_seconds": 1 / 24,
            "anchor_y_absolute_error": 0.04,
        },
        "limits": "Three owned clean caption/graphic scenes. Does not represent natural footage or broad genre accuracy.",
    }
    (out / "hidden-gold.json").write_text(json.dumps(gold, indent=2) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    print(make(parser.parse_args().out))
