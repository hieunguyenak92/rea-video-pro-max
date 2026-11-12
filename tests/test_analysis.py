"""Behavioral analysis checks using owned pixels/audio, never upstream footage."""
from fractions import Fraction
import hashlib
import json
import shutil
import subprocess
import wave
from pathlib import Path

import av
import numpy as np
import pytest
from jsonschema import Draft202012Validator
from PIL import Image, ImageDraw, ImageFont

from rea_video_pro_max.analysis import analyze
from rea_video_pro_max.audio import analyze_audio
from rea_video_pro_max.core import validate
from rea_video_pro_max.perception import TextTracker, bbox_iou, detect_text, phase_translation, measure_text_style, font_candidates


ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "skills/rea-video-pro-max/assets/fonts/BeVietnamPro-Bold.ttf"


def _caption_image(color=(28, 70, 120), text="BUILD A NEW STORY"):
    image = Image.new("RGB", (640, 360), color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 32)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    draw.text(((640-(box[2]-box[0]))/2, 280), text, font=font, fill="white", stroke_width=2, stroke_fill="black")
    return image


@pytest.fixture
def reference(tmp_path):
    path = tmp_path / "owned-reference.mp4"
    with av.open(str(path), "w") as output:
        stream = output.add_stream("libx264", rate=10)
        stream.width, stream.height = 640, 360
        stream.pix_fmt = "yuv420p"
        stream.options = {"crf": "16", "preset": "ultrafast"}
        for i in range(30):
            color = [(28, 70, 120), (130, 25, 40), (30, 130, 55)][i//10]
            frame = av.VideoFrame.from_image(_caption_image(color))
            frame.pts, frame.time_base = i, Fraction(1, 10)
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    return path


def test_cut_map_uses_decoded_pts_and_preserves_source(reference, tmp_path):
    before = hashlib.sha256(reference.read_bytes()).hexdigest()
    result = analyze(reference, tmp_path / "analysis", ocr="off")
    assert validate(result, "rea-video-analysis") is result
    schema = json.loads((ROOT / "skills/rea-video-pro-max/lib/rea_video_pro_max/schemas/analysis.json").read_text())
    Draft202012Validator(schema).validate(result)
    assert [row["start"] for row in result["shots"]] == pytest.approx([0, 1, 2])
    assert result["shots"][-1]["end"] == pytest.approx(3)
    assert result["coverage"]["decoded_frames"] == 30
    assert result["coverage"]["complete"]
    assert result["source"]["sha256"] == before == hashlib.sha256(reference.read_bytes()).hexdigest()
    assert result["source"]["presentation_clock"]["variable_intervals"] is False
    assert result["source"]["presentation_clock"]["observed_intervals"] == [{"num": 1, "den": 10, "seconds": .1, "count": 29}]
    assert result["audio"]["status"] == "absent"
    assert result["coverage"]["motion"]["profile"] == "affine"
    assert result["coverage"]["motion"]["selected_pairs"] <= 192
    frame_index = json.loads((tmp_path / "analysis/evidence/frame-index.json").read_text())
    assert len(frame_index["frames"]) == 30
    for row in frame_index["frames"]:
        assert row["pts"] is not None
        assert row["time_base"]["den"] > 0
        assert row["timestamp_status"] == "measured"
    for sample in result["evidence"]:
        evidence = tmp_path / "analysis" / sample["path"]
        assert sample["sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
        assert sample["source_sha256"] == before
        assert sample["id"] in {row["id"] for row in frame_index["frames"]}
    # Strict JSON encoding rejects accidental NaN/Infinity estimates at the
    # boundary; every generated analysis file must remain independently parseable.
    json.dumps(result, allow_nan=False)
    for filename in ["timeline.json", "captions.json", "subtitle-styles.json", "audio-cues.json", "motion.json", "composition.json", "uncertainties.json", "shots.csv"]:
        assert (tmp_path / "analysis" / filename).is_file()


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_actual_ocr_recovers_caption_style_and_splits_repeated_text(reference, tmp_path):
    result = analyze(reference, tmp_path / "ocr", ocr="required", sample_fps=4)
    captions = [row for row in result["captions"] if "BUILD" in row["text"] and "STORY" in row["text"]]
    assert len(captions) == 3
    assert len({row["shot_id"] for row in captions}) == 3
    assert all(row["source_origin"] == "pixel_derived" for row in captions)
    assert all(row["timing"]["status"] == "model-derived" for row in captions)
    assert [row["start"] for row in captions] == pytest.approx([0, 1, 2])
    assert all(row["font_candidates"][0]["status"] == "candidate" for row in captions)
    assert all(len(row["font_candidates"][0]["font_sha256"]) == 64 for row in captions)
    assert all(0 <= coordinate <= 1 for row in captions for coordinate in row["bbox"])
    assert result["style"]["anchor"] == "bottom"
    assert min(result["style"]["fill"]) > 200
    assert result["style"]["font_family"] == "unknown"
    assert result["coverage"]["ocr"]["calls"] >= 3
    assert result["coverage"]["ocr"]["reused"] > 0


def test_analysis_range_and_supplied_text_are_distinct(reference, tmp_path):
    supplied = tmp_path / "transcript.txt"
    supplied.write_text("USER TEXT IS NOT OBSERVED", encoding="utf-8")
    result = analyze(reference, tmp_path / "partial", ocr="off", max_seconds=1.5, transcript=supplied)
    assert result["coverage"]["decoded_range"] == pytest.approx([0, 1.5])
    assert result["coverage"]["outside_requested_range"] == pytest.approx([1.5, 3])
    assert result["captions"] == []
    assert result["supplied_transcript"]["origin"] == "user_supplied"
    assert "USER TEXT" in result["supplied_transcript"]["text"]


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_single_image_has_no_invented_timeline(tmp_path):
    path = tmp_path / "image.png"
    _caption_image().save(path)
    result = analyze(path, tmp_path / "image-analysis", ocr="required")
    validate(result, "rea-video-analysis")
    schema = json.loads((ROOT / "skills/rea-video-pro-max/lib/rea_video_pro_max/schemas/analysis.json").read_text())
    Draft202012Validator(schema).validate(result)
    assert result["source"]["duration"] == 0
    assert result["shots"] == []
    assert result["captions"]
    assert all(row["start"] == row["end"] == 0 for row in result["captions"])
    assert all(row["timing"]["status"] == "not-applicable" for row in result["captions"])


def test_analysis_rejects_invalid_bounds_and_source_overwrite(reference, tmp_path):
    with pytest.raises(ValueError, match="sample_fps"):
        analyze(reference, tmp_path / "invalid", sample_fps=float("nan"))
    with pytest.raises(ValueError, match="max_seconds"):
        analyze(reference, tmp_path / "invalid", max_seconds=0)
    with pytest.raises(ValueError, match="overwrite"):
        analyze(reference, reference, ocr="off")
    destination = tmp_path / "symlinked-output"
    destination.mkdir()
    external = tmp_path / "preserve.csv"
    external.write_text("preserve me")
    (destination / "shots.csv").symlink_to(external)
    with pytest.raises(ValueError, match="symlink"):
        analyze(reference, destination, ocr="off")
    assert external.read_text() == "preserve me"


def test_motion_translation_and_texture_abstention():
    rng = np.random.default_rng(7)
    previous = rng.uniform(0, 255, (54, 96))
    current = np.roll(np.roll(previous, 3, axis=1), -2, axis=0)
    result = phase_translation(previous, current)
    assert result["status"] == "estimated"
    assert result["dx"] == pytest.approx(3/96, abs=1e-5)
    assert result["dy"] == pytest.approx(-2/54, abs=1e-5)
    assert phase_translation(np.zeros((54, 96)), np.zeros((54, 96)))["status"] == "unknown"
    assert bbox_iou([0, 0, 1, 1], [0, 0, .5, .5]) == .25


def test_text_tracker_does_not_merge_across_shots():
    obs = {"text": "SAME WORDS", "bbox": [.1, .8, .7, .1], "style": {"fill": [255, 255, 255]}, "words": []}
    tracker = TextTracker(.25)
    tracker.update([obs], 0, "frame0", shot_id="shot1")
    tracker.update([obs], .25, "frame1", shot_id="shot2")
    assert len(tracker.finish(1)) == 2


def test_text_tracker_does_not_bridge_observed_absence():
    obs = {"text": "SAME WORDS", "bbox": [.1, .8, .7, .1], "style": {"fill": [255, 255, 255]}, "words": []}
    tracker = TextTracker(.5)
    tracker.update([obs], 0, "frame0")
    tracker.update([], .5, "frame1")
    tracker.update([obs], 1, "frame2")
    assert len(tracker.finish(2)) == 2


def test_single_frame_flash_is_one_transition_not_two_cuts(tmp_path):
    path = tmp_path / "owned-flash.mp4"
    with av.open(str(path), "w") as output:
        stream = output.add_stream("libx264", rate=10)
        stream.width, stream.height, stream.pix_fmt = 320, 180, "yuv420p"
        for i in range(20):
            image = Image.new("RGB", (320, 180), "white" if i == 10 else (30, 60, 90))
            frame = av.VideoFrame.from_image(image)
            frame.pts, frame.time_base = i, Fraction(1, 10)
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    result = analyze(path, tmp_path / "flash", ocr="off")
    assert len(result["shots"]) == 1
    assert len(result["transitions"]) == 1
    assert result["transitions"][0]["type"] == "flash_candidate"
    assert result["transitions"][0]["start"] == pytest.approx(1)


def test_audio_uses_real_signal_onsets_and_silence(tmp_path):
    rate = 16000
    data = np.zeros(rate*3, dtype=np.float32)
    for start in [.5, 1, 1.5, 2, 2.5]:
        tone = .7*np.sin(2*np.pi*600*np.arange(int(rate*.1))/rate)
        index = int(rate*start)
        data[index:index+len(tone)] = tone
    path = tmp_path / "pulse.wav"
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(rate)
        file.writeframes((data*32767).astype("<i2").tobytes())
    result = analyze_audio(path, duration=3)
    assert result["status"] == "measured"
    assert result["source_time_base"] == {"num": 1, "den": 16000}
    assert any(abs(row["time"]-.5) < .04 for row in result["onsets"])
    assert len(result["onsets"]) >= 4
    assert result["silences"][0]["start"] == 0
    assert result["silences"][0]["end"] > .4
    assert result["tempo"]["bpm"] == pytest.approx(120, abs=2)
    assert "ASR not run" in result["unknowns"][0]


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_detect_text_is_pixel_derived():
    found = detect_text(_caption_image())
    assert any("BUILD A NEW STORY" == row["text"] for row in found)
    assert all("not calibrated probability" in row["score_semantics"] for row in found)


def _write_video(path, images, fps):
    with av.open(str(path), "w") as output:
        stream = output.add_stream("libx264", rate=fps)
        stream.width, stream.height, stream.pix_fmt = images[0].width, images[0].height, "yuv420p"
        stream.options = {"crf": "14", "preset": "ultrafast"}
        for i, image in enumerate(images):
            frame = av.VideoFrame.from_image(image)
            frame.pts, frame.time_base = i, Fraction(1, fps)
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_dense_caption_edges_match_non_sample_aligned_ground_truth(tmp_path):
    path = tmp_path / "owned-edge-cue.mp4"
    images = [_caption_image() if 7 <= index < 33 else Image.new("RGB", (640, 360), (28, 70, 120)) for index in range(40)]
    _write_video(path, images, 20)
    result = analyze(path, tmp_path / "edge-analysis", ocr="required", sample_fps=4)
    cue = next(cue for cue in result["captions"] if cue["text"] == "BUILD A NEW STORY")
    assert cue["start"] == pytest.approx(.35, abs=.05)
    assert cue["end"] == pytest.approx(1.65, abs=.05)
    assert cue["timing"]["method"] == "decoded-PTS-local-ROI-OCR"
    assert cue["timing"]["onset_interval"][1]-cue["timing"]["onset_interval"][0] <= .050001
    assert cue["timing"]["offset_interval"][1]-cue["timing"]["offset_interval"][0] <= .050001
    assert result["coverage"]["cue_boundary_refinement"]["fully_refined_cues"] == 1


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_word_color_observations_survive_same_text_cache(tmp_path):
    images = []
    words = ["BUILD", "A", "NEW", "STORY"]
    font = ImageFont.truetype(str(FONT), 32)
    total_width = sum(font.getlength(word+" ") for word in words)
    for index in range(20):
        image = Image.new("RGB", (640, 360), (28, 70, 120))
        draw = ImageDraw.Draw(image)
        x = (640-total_width)/2
        for word_index, word in enumerate(words):
            highlight = (5 <= index < 10 and word_index == 0) or (10 <= index < 15 and word_index == 2)
            draw.text((x, 280), word, font=font, fill=(255, 220, 0) if highlight else "white", stroke_width=2, stroke_fill="black")
            x += font.getlength(word+" ")
        images.append(image)
    path = tmp_path / "owned-highlight.mp4"
    _write_video(path, images, 10)
    result = analyze(path, tmp_path / "highlight-analysis", ocr="required", sample_fps=5)
    events = [event for cue in result["captions"] for event in cue.get("word_highlights", [])]
    assert events
    assert {event["word_index"] for event in events} >= {0, 2}
    assert any(event["fill"][2] < 80 and event["fill"][0] > 200 for event in events)
    assert all("not a verified speech-aligned" in event["limits"] for event in events)


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_titles_and_large_graphic_readings_remain_outside_subtitle_lane(tmp_path):
    image = Image.new("RGB", (640, 360), (28, 70, 120))
    draw = ImageDraw.Draw(image)
    draw.text((150, 15), "PROJECT MAP", font=ImageFont.truetype(str(FONT), 30), fill="white")
    draw.text((240, 70), "TT", font=ImageFont.truetype(str(FONT), 150), fill=(255, 160, 106))
    path = tmp_path / "title.png"
    image.save(path)
    result = analyze(path, tmp_path / "titles", ocr="required")
    assert result["captions"] == []
    assert any("PROJECT MAP" in cue["text"] for cue in result["text_regions"])
    assert all(cue["role"] == "title_or_scene_text" for cue in result["text_regions"])


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg required to author embedded-text fixture")
def test_embedded_stream_is_not_promoted_to_visible_ocr(reference, tmp_path):
    subtitle = tmp_path / "independent-stream.srt"
    subtitle.write_text("1\n00:00:00,400 --> 00:00:01,600\nSTREAM TEXT DISTINCT\n\n", encoding="utf-8")
    path = tmp_path / "with-subtitle.mkv"
    subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-i", str(reference), "-i", str(subtitle), "-c:v", "copy", "-c:s", "srt", str(path)], check=True)
    result = analyze(path, tmp_path / "embedded", ocr="off")
    assert result["captions"] == []
    event = result["embedded_subtitles"]["events"][0]
    assert event["text"] == "STREAM TEXT DISTINCT"
    assert event["start"] == pytest.approx(.4)
    assert event["end"] == pytest.approx(1.6)
    assert event["origin"] == "embedded_subtitle_stream"
    assert event["pts"] is not None
    assert event["time_base"]["den"] > 0


def test_disguised_hls_playlist_is_rejected_before_demux(tmp_path):
    playlist = tmp_path / "disguised.mp4"
    playlist.write_text("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\nhttps://127.0.0.1:1/segment.ts\n#EXT-X-ENDLIST\n")
    with pytest.raises(ValueError, match="probe failed"):
        analyze(playlist, tmp_path / "hls", ocr="off")
    with pytest.raises((av.error.FFmpegError, ValueError)):
        analyze_audio(playlist, duration=2)


def test_multiframe_image_is_rejected_instead_of_silently_reading_first_frame(tmp_path):
    path = tmp_path / "animated.png"
    first = Image.new("RGB", (64, 64), "red")
    first.save(path, save_all=True, append_images=[Image.new("RGB", (64, 64), "blue")], duration=100, loop=0)
    with pytest.raises(ValueError, match="multi-frame"):
        analyze(path, tmp_path / "animated-analysis", ocr="off")


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_same_text_scale_change_is_observed_from_owned_pixels(tmp_path):
    images = []
    for index in range(20):
        image = Image.new("RGB", (640, 360), (28, 70, 120))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(str(FONT), 28 if index < 10 else 42)
        text = "MOVING WORDS"
        draw.text(((640-font.getlength(text))/2, 280), text, font=font, fill="white", stroke_width=2, stroke_fill="black")
        images.append(image)
    path = tmp_path / "owned-scale.mp4"
    _write_video(path, images, 10)
    result = analyze(path, tmp_path / "scale-analysis", ocr="required", sample_fps=5)
    cues = [cue for cue in result["captions"] if cue["text"] == "MOVING WORDS"]
    assert len(cues) == 1
    assert cues[0]["style"]["animation"] == "scale_candidate"
    assert cues[0]["geometry_change"]["height_ratio_range"][1] > 1.3


def test_tracker_reports_budget_omissions_instead_of_unbounded_growth():
    obs = {"text": "TEXT", "bbox": [.1, .8, .7, .1], "style": {"fill": [255, 255, 255]}, "words": []}
    tracker = TextTracker(.25, max_tracks=1)
    tracker.update([obs], 0, "frame0", shot_id="shot1")
    tracker.update([obs], .25, "frame1", shot_id="shot2")
    assert len(tracker.finish(1)) == 1
    assert tracker.omitted_observations == 1


def test_variable_decoded_clock_is_detected_from_pts(tmp_path):
    path = tmp_path / "owned-vfr.mp4"
    timestamps = [0, 1, 2, 4, 5, 8]
    with av.open(str(path), "w") as output:
        stream = output.add_stream("libx264", rate=10)
        stream.width, stream.height, stream.pix_fmt = 320, 180, "yuv420p"
        for pts in timestamps:
            frame = av.VideoFrame.from_image(Image.new("RGB", (320, 180), (25, 50, 75)))
            frame.pts, frame.time_base = pts, Fraction(1, 10)
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    result = analyze(path, tmp_path / "vfr", ocr="off")
    clock = result["source"]["presentation_clock"]
    assert clock["status"] == "measured"
    assert clock["variable_intervals"] is True
    assert {row["seconds"] for row in clock["observed_intervals"]} == {.1, .2, .3}
    assert clock["observed_interval_count"] == 5


def test_audio_pts_gap_is_not_reported_as_observed_silence(tmp_path):
    path = tmp_path / "owned-audio-gap.mka"
    rate = 16000
    with av.open(str(path), "w") as output:
        stream = output.add_stream("pcm_s16le", rate=rate)
        stream.layout = "mono"
        for pts, data in [(0, np.zeros(rate, np.int16)), (2*rate, (10000*np.sin(2*np.pi*600*np.arange(rate)/rate)).astype(np.int16))]:
            frame = av.AudioFrame.from_ndarray(data.reshape(1, -1), format="s16", layout="mono")
            frame.sample_rate, frame.pts, frame.time_base = rate, pts, Fraction(1, rate)
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    result = analyze_audio(path, duration=3)
    assert result["coverage"]["discontinuities"]
    assert result["coverage"]["discontinuities"][0]["gap_seconds"] == pytest.approx(1, abs=.002)
    assert all(not (region["start"] < 1.5 < region["end"]) for region in result["silences"])
    assert result["coverage"]["decoded_end"] == pytest.approx(3, abs=.002)
    assert 2.96 <= result["coverage"]["end"] <= 3


@pytest.mark.parametrize("outline", [0, 1, 2, 4])
def test_raster_outline_fit_uses_visible_band_width(outline):
    image = Image.new("RGB", (640, 360), (28, 70, 120))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 40)
    text = "BUILD A NEW STORY"
    draw.text((70, 200), text, font=font, fill="white", stroke_width=outline, stroke_fill="black")
    x, y, right, bottom = draw.textbbox((70, 200), text, font=font)
    style = measure_text_style(image, (x, y, right-x, bottom-y))
    assert min(style["fill"]) > 240
    assert style["stroke_width_ratio"]*360 == pytest.approx(outline, abs=.5)


def test_dark_palette_cuts_and_two_frame_insert_survive_low_mean_difference(tmp_path):
    images = []
    for index in range(90):
        color = (15, 25, 45) if index < 30 else (35, 27, 23) if index < 60 else (22, 45, 28)
        if 42 <= index < 44:
            color = (110, 28, 42)
        image = Image.new("RGB", (320, 180), color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 40, 240, 110), outline=(180, 185, 190), width=2)
        images.append(image)
    path = tmp_path / "owned-dark-palette.mp4"
    _write_video(path, images, 30)
    result = analyze(path, tmp_path / "dark-palette", ocr="off", motion_profile="off")
    assert [shot["start"] for shot in result["shots"]] == pytest.approx([0, 1, 1.4, 44/30, 2], abs=1e-8)


def test_gradual_palette_change_is_not_promoted_to_a_hard_cut(tmp_path):
    images = [Image.new("RGB", (160, 90), (20+index, 25+index//2, 45)) for index in range(60)]
    path = tmp_path / "owned-gradual-grade.mp4"
    _write_video(path, images, 30)
    result = analyze(path, tmp_path / "grade", ocr="off", motion_profile="off")
    assert len(result["shots"]) == 1


def test_short_monotone_fade_does_not_become_many_palette_cuts(tmp_path):
    images = []
    for index in range(40):
        level = 120 if index < 12 else round(120*(20-index)/8) if index < 20 else 0
        images.append(Image.new("RGB", (160, 90), (level, level, level)))
    path = tmp_path / "owned-short-fade.mp4"
    _write_video(path, images, 30)
    result = analyze(path, tmp_path / "short-fade", ocr="off", motion_profile="off")
    assert len(result["shots"]) == 1
    assert any(event["type"] == "fade_candidate" for event in result["transitions"])


@pytest.mark.parametrize("text", ["BUILD A NEW STORY", "Mở cửa xưởng mới", "Ghi lại điều quan trọng", "Bắt đầu bằng hôm nay"])
def test_catalog_geometry_size_survives_accents_and_colored_words(text):
    image = Image.new("RGB", (640, 360), (8, 12, 20))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 32)
    x = (640-font.getlength(text))/2
    boxes, words = [], []
    for index, word in enumerate(text.split()):
        fill = [255, 214, 67] if index == 0 else [246, 247, 249]
        draw.text((x, 275), word, font=font, fill=tuple(fill), stroke_width=2, stroke_fill="black")
        left, top, right, bottom = draw.textbbox((x, 275), word, font=font)
        boxes.append((left, top, right, bottom))
        words.append({"text": word, "fill": fill, "bbox": [left/640, top/360, (right-left)/640, (bottom-top)/360]})
        x += font.getlength(word+" ")
    left, top = min(box[0] for box in boxes), min(box[1] for box in boxes)
    right, bottom = max(box[2] for box in boxes), max(box[3] for box in boxes)
    bbox = [left/640, top/360, (right-left)/640, (bottom-top)/360]
    candidates = font_candidates(image, bbox, text, FONT.parent, words=words)
    assert candidates[0]["font_file"] == FONT.name
    assert candidates[0]["size_px"] == pytest.approx(32, abs=1)
    assert "not the unknown original" in candidates[0]["size_semantics"]
    appearance = measure_text_style(image, (left, top, right-left, bottom-top))
    assert appearance["stroke_width_ratio"]*360 == pytest.approx(2, abs=.5)


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_sequential_highlight_palette_switch_is_retained_as_two_regimes(tmp_path):
    font = ImageFont.truetype(str(FONT), 32)
    words = ["BRING", "NEW", "IDEAS"]
    images = []
    for index in range(40):
        image = Image.new("RGB", (640, 360), (8, 12, 20))
        draw = ImageDraw.Draw(image)
        x = (640-font.getlength(" ".join(words)))/2
        active = (index % 20)//7
        for word_index, word in enumerate(words):
            color = (255, 214, 67) if index < 20 else (80, 223, 230)
            draw.text((x, 275), word, font=font, fill=color if word_index == active else (246, 247, 249), stroke_width=2, stroke_fill="black")
            x += font.getlength(word+" ")
        images.append(image)
    path = tmp_path / "owned-highlight-regimes.mp4"
    _write_video(path, images, 10)
    result = analyze(path, tmp_path / "highlight-regimes", ocr="required", sample_fps=5, motion_profile="off")
    palette = result["style"]["highlight_palette"]
    assert len(palette) == 2
    assert palette[0]["fill"][0] > 220 and palette[0]["fill"][2] < 100
    assert palette[1]["fill"][0] < 120 and palette[1]["fill"][2] > 200
    assert result["style"]["font_size_ratio"]*360 == pytest.approx(32, abs=2)
    assert result["style"]["stroke_width_ratio"]*360 == pytest.approx(2, abs=1)


def test_asr_import_preserves_model_and_external_source_provenance(reference, tmp_path):
    artifact = tmp_path / "synthetic-asr-import.json"
    source_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
    artifact.write_text(json.dumps({"schema_version": 1, "kind": "rea-video-transcript", "channel": "audio-speech-asr",
                                   "source": {"sha256": source_hash}, "provider": {"name": "fixture-asr", "version": "test"},
                                   "text": "SYNTHETIC IMPORT CONTRACT", "segments": [{"start": .2, "end": .8, "text": "SYNTHETIC IMPORT CONTRACT", "status": "model-derived"}],
                                   "words": [{"start": .2, "end": .4, "text": "SYNTHETIC", "status": "model-derived"}]}))
    result = analyze(reference, tmp_path / "asr-import", ocr="off", transcript=artifact, motion_profile="off")
    imported = result["supplied_transcript"]
    assert imported["origin"] == "imported_model_derived_asr"
    assert imported["provider"]["name"] == "fixture-asr"
    assert imported["source_media"]["sha256"] == source_hash
    assert imported["source_matches_analysis"] is True
    assert imported["cues"][0]["status"] == "model-derived"
    assert result["captions"] == []
    assert result["motion"] == result["coarse_motion"] == []


@pytest.mark.skipif(not shutil.which("tesseract"), reason="optional local OCR not installed")
def test_ring_graphic_ocr_never_admitted_to_reusable_style(tmp_path):
    images = []
    colors = [(15, 30, 48), (18, 36, 56), (20, 40, 62)]
    for index in range(18):
        image = Image.new("RGB", (640, 360), colors[index//6])
        draw = ImageDraw.Draw(image)
        for x in range(50, 620, 90):
            draw.ellipse((x, 60+(index*5)%100, x+44, 104+(index*5)%100), outline=(130, 160, 190), width=2)
            draw.line((x+12, 82+(index*5)%100, x+32, 82+(index*5)%100), fill=(230, 75, 140), width=2)
        images.append(image)
    path = tmp_path / "owned-ring-graphic.mp4"
    _write_video(path, images, 12)
    result = analyze(path, tmp_path / "ring-analysis", ocr="required", sample_fps=6, motion_profile="off")
    assert result["captions"] == []
    assert result["style"]["status"] == "unknown"
    assert result["style"].get("reason") == "no readable text detected"
    # OCR may correctly return no text, or retain raw scene/suspect readings.
    # OCR engine builds can return coherent scene-label candidates as well as
    # suspect readings. Neither category is an admitted subtitle/style source.
    assert all(region["quality"]["status"] == "suspect" or region.get("role") != "caption_candidate"
               for region in result["text_regions"])


def test_scene_candidate_is_preserved_without_becoming_subtitle_style():
    from rea_video_pro_max.analysis import _classify_text_regions
    def region(role, y):
        return {"text": "READ THIS LABEL", "role": role, "bbox": [.1, y, .6, .08],
                "engine_score": 96, "style": {"position": [.4, y+.04]},
                "observations": [{"word_appearances": []}, {"word_appearances": []}],
                "font_candidates": [{"glyph_iou": .8}]}
    scene = region("title_or_scene_text", .1)
    caption = region("caption_candidate", .78)
    selected = _classify_text_regions([scene, caption])
    assert selected == [caption]
    assert scene["quality"]["status"] == "candidate"
    assert caption["quality"]["status"] == "candidate"


@pytest.mark.parametrize("case,reason", [
    ("single-observation", "single_temporal_observation"),
    ("incoherent-height", "word_height_incoherent"),
    ("weak-glyph-fit", "weak_closed_catalog_geometry_fit"),
])
def test_unreliable_caption_evidence_is_retained_but_not_reused(case, reason):
    from rea_video_pro_max.analysis import _classify_text_regions
    region = {"text": "SAMPLE TEXT", "role": "caption_candidate", "bbox": [.1, .76, .6, .12],
              "engine_score": 96, "style": {"position": [.4, .82]},
              "observations": [{"word_appearances": []}, {"word_appearances": []}],
              "font_candidates": [{"glyph_iou": .8}]}
    if case == "single-observation":
        region["observations"] = region["observations"][:1]
    elif case == "weak-glyph-fit":
        region["font_candidates"][0]["glyph_iou"] = .02
    else:
        for observation in region["observations"]:
            observation["word_appearances"] = [{"bbox": [.1, .76, .2, .03]},
                                               {"bbox": [.4, .76, .2, .12]}]
    regions = [region]
    assert _classify_text_regions(regions) == []
    assert regions == [region]  # raw observation is still available for analysis files
    assert region["quality"]["status"] == "suspect"
    assert reason in region["quality"]["reasons"]
