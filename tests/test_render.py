"""Behavioral contracts for style binding, playback, portability and fail-closed inputs."""

import hashlib
import json
import shutil
import subprocess
import wave

import av
import numpy as np
import pytest
from PIL import Image, ImageChops, features

from rea_video_pro_max.render import render, render_still
from rea_video_pro_max.template import compose, extract_template


@pytest.fixture
def analysis():
    return {
        "schema_version": 1, "kind": "rea-video-analysis",
        "source": {"path": "/private/reference-that-must-not-be-read.mp4", "sha256": "a" * 64,
                   "width": 640, "height": 360, "duration": 6.0},
        "captions": [{"id": "caption-a", "start": 1, "end": 3, "text": "OLD REFERENCE WORDS",
                      "bbox": [.2, .7, .6, .1], "evidence": [{"pts": 90000, "time_base": "1/90000"}],
                      "style": {"font_size_ratio": .08, "fill": [240, 245, 250], "stroke": [2, 3, 4],
                                "stroke_width_ratio": .004, "position": [.45, .75], "line_height_ratio": .096,
                                "animation": "static", "shadow": {"status": "unknown"}, "box_color": None}}],
        "shots": [{"start": 0, "end": 2}, {"start": 2, "end": 6}],
        "unknowns": [{"field": "original.font", "status": "unknown"}],
    }


@pytest.fixture
def template(analysis):
    return extract_template(analysis)


def content(**updates):
    result = {"schema_version": 1, "kind": "rea-video-content", "width": 320, "height": 180,
              "fps": 10, "scenes": [{"id": "fresh", "text": "NEW CONTENT FOR TOMORROW", "duration": 1.0,
                                      "background": [20, 40, 80]}]}
    result.update(updates)
    return result


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def require_encoder():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg and ffprobe required for playback acceptance")


def decoded(path):
    with av.open(str(path)) as media:
        return [frame.to_image() for frame in media.decode(video=0)]


def test_template_preserves_observed_parameters_and_uncertainty(analysis, tmp_path):
    result = extract_template(analysis, tmp_path)
    assert result["style"]["font_size_ratio"] == .08
    assert result["style"]["fill"] == [240, 245, 250]
    assert result["style"]["stroke"] == [2, 3, 4]
    assert result["style"]["anchor_x"] == .45
    assert result["style"]["anchor_y"] == .75
    assert result["style"]["line_height"] == pytest.approx(1.2)
    assert result["style"]["entry"] == "static"
    assert result["style"]["shadow"] == [0, 0, 0, 0]
    assert result["style"]["box_color"] == [0, 0, 0, 0]
    assert result["style"]["highlight"] == result["style"]["fill"]
    assert result["rhythm"]["median_shot_duration"] == 3
    assert result["evidence"][0]["evidence"][0]["pts"] == 90000
    assert result["unknowns"] == analysis["unknowns"]
    assert any(choice["field"] == "font" for choice in result["implementation_choices"])
    assert "reference-that-must-not-be-read" not in json.dumps(result)
    assert (tmp_path / "style-template.json").is_file()


def test_inferred_animation_is_explicit_approximation(analysis):
    analysis["captions"][0]["style"]["animation"] = "scale_candidate"
    result = extract_template(analysis)
    assert result["style"]["entry"] == "pop"
    assert any("original easing" in choice["reason"] for choice in result["implementation_choices"])


def test_fade_candidates_are_mapped_but_unsupported_candidates_remain_uncertain(analysis):
    analysis["transitions"] = [{"type": "fade_candidate", "start": 1.8, "end": 2.2, "status": "inferred"},
                               {"type": "flash_candidate", "start": 4, "end": 4.1, "status": "inferred"}]
    result = extract_template(analysis)
    assert result["rhythm"]["transition"]["family"] == "fade"
    assert result["rhythm"]["transition"]["duration"] == pytest.approx(.4)
    assert any(item.get("observed") == "flash_candidate" for item in result["unknowns"])
    assert result["parameter_provenance"]["fill"]["source_value"] == [240, 245, 250]


def test_new_content_gets_fresh_timing_and_no_reference_media(template, tmp_path):
    result = compose(template, content(), tmp_path)
    assert result["scenes"][0]["text"] == "NEW CONTENT FOR TOMORROW"
    assert result["captions"][0]["start"] == 0
    assert result["captions"][-1]["end"] == 1
    assert result["captions"][0]["words"][0]["text"] == "NEW"
    assert result["captions"][0]["words"][0]["end"] < 1
    assert all(cue["timing"] == "estimated-from-new-text" for cue in result["captions"])
    assert result["scenes"][0]["asset"] is None and result["audio"] is None
    assert [a["role"] for a in result["assets"]] == ["font"]
    assert result["provenance"]["reference_media_reused"] is False
    assert all((tmp_path / name).is_file() for name in ["project.json", "style-template.json", "content-bindings.json", "timeline.json"])
    assert result["font"]["path"].startswith("assets/")


def test_new_text_grouping_changes_with_longer_script(template, tmp_path):
    bindings = content(scenes=[{"text": "one two three four five six seven eight nine ten", "duration": 3}])
    result = compose(template, bindings, tmp_path)
    groups = result["scenes"][0]["captions"]
    assert len(groups) == 4  # Three words in the observed A group; ten new words need four groups.
    assert [w["text"] for g in groups for w in g["words"]] == bindings["scenes"][0]["text"].split()
    assert groups[-1]["end"] == 3


def test_implicit_durations_reuse_relative_edit_rhythm(template, tmp_path):
    scenes = [{"text": "new short content"}, {"text": "another short scene"}]
    result = compose(template, content(scenes=scenes), tmp_path / "original-rhythm")
    assert [scene["duration"] for scene in result["scenes"]] == [2, 4]
    scenes[0]["text"] = " ".join(["longer"] * 28)
    result = compose(template, content(scenes=scenes), tmp_path / "stretched-rhythm")
    assert [scene["duration"] for scene in result["scenes"]] == [10, 20]


def test_fixed_and_audio_clocks_preserve_supplied_windows(template, tmp_path):
    template["rhythm"]["transition"] = {"family": "dissolve", "duration": .2}
    scenes = [{"text": "alpha beta", "duration": 1, "words": [
        {"text": "alpha", "start": .1, "end": .3}, {"text": "beta", "start": .5, "end": .9}]}] * 2
    for policy in ("fixed", "audio-anchored"):
        result = compose(template, content(scenes=scenes, timing_policy=policy), tmp_path / policy)
        assert result["render"]["duration"] == 2
        assert result["scenes"][1]["start"] == 1
        assert result["scenes"][1]["transition"] == {"family": "cut", "duration": 0}
        assert result["scenes"][0]["captions"][0]["words"][0]["start"] == .1
        assert result["captions"][-1]["words"][-1]["end"] == 1.9
    with pytest.raises(ValueError, match="scene.words"):
        compose(template, content(timing_policy="audio-anchored"), tmp_path / "missing-alignment")


@pytest.mark.parametrize("words", [
    [{"text": "wrong", "start": 0, "end": .5}],
    [{"text": "a", "start": .4, "end": .8}, {"text": "b", "start": .7, "end": .9}],
    [{"text": "a", "start": 0, "end": 0}, {"text": "b", "start": .2, "end": .9}],
    [{"text": "a", "start": 0, "end": .5}, {"text": "b", "start": .6, "end": 1.1}],
])
def test_invalid_supplied_word_timings_fail(template, tmp_path, words):
    with pytest.raises(ValueError):
        compose(template, content(scenes=[{"text": "a b", "duration": 1, "words": words}]), tmp_path)
    assert not (tmp_path / "project.json").exists()


def test_reference_asset_reuse_requires_explicit_binding_and_permission(template, tmp_path):
    image = tmp_path / "reference.png"
    Image.new("RGB", (64, 64), "red").save(image)
    template["reference"]["sha256"] = hashlib.sha256(image.read_bytes()).hexdigest()
    bindings = content(scenes=[{"text": "new words", "duration": 1, "asset": str(image)}])
    with pytest.raises(ValueError, match="reference media"):
        compose(template, bindings, tmp_path / "forbidden")
    result = compose(template, {**bindings, "allow_reference_reuse": True}, tmp_path / "authorized")
    assert result["provenance"]["reference_media_reused"] is True
    assert result["provenance"]["reference_reuse_authorized"] is True


@pytest.mark.parametrize("updates", [{"width": 319}, {"width": 320.5}, {"fps": float("nan")},
                                      {"font": "missing.ttf"}, {"scenes": []},
                                      {"scenes": [{"asset": "missing.png", "duration": 1}]}])
def test_invalid_bindings_fail_without_a_project(template, tmp_path, updates):
    with pytest.raises(ValueError):
        compose(template, content(**updates), tmp_path)
    assert not (tmp_path / "project.json").exists()


def test_missing_glyphs_and_unsupported_shaping_fail(template, tmp_path):
    with pytest.raises(ValueError, match="glyphs"):
        compose(template, content(scenes=[{"text": "\U0001f9d1", "duration": 1}]), tmp_path / "emoji")
    with pytest.raises(ValueError, match="bidirectional"):
        compose(template, content(scenes=[{"text": "مرحبا", "duration": 1}]), tmp_path / "arabic")
    if not features.check_feature("raqm"):
        with pytest.raises(ValueError, match="RAQM"):
            compose(template, content(scenes=[{"text": "สวัสดี", "duration": 1}]), tmp_path / "thai")


def test_real_video_render_and_project_portability(template, tmp_path):
    require_encoder()
    source = tmp_path / "original-image.png"
    Image.new("RGB", (240, 160), (10, 90, 140)).save(source)
    template["style"].update({"entry": "static", "font_size_ratio": .1})
    folder = tmp_path / "project"
    compose(template, content(scenes=[{"text": "Xin chào video mới", "duration": 1, "asset": str(source)}]), folder)
    receipt = render(folder)
    frames = decoded(folder / "render.mp4")
    assert len(frames) == 10 and frames[0].size == (320, 180)
    assert receipt["duration"] == pytest.approx(1, abs=.01)
    assert receipt["audio_present"] is False
    assert receipt["checks"]["full_video_decode"]
    assert receipt["reference_sha256"] == template["reference"]["sha256"]
    assert np.max(np.abs(np.asarray(frames[5])[5, 5].astype(int) - [10, 90, 140])) <= 5
    checkpoint = render_still(folder, .5, tmp_path / "before.png")
    source.unlink()
    moved = tmp_path / "portable"
    shutil.move(str(folder), moved)
    after = render_still(moved, .5, tmp_path / "after.png")
    assert after["sha256"] == checkpoint["sha256"]
    second = render(moved)
    assert second["frame_count"] == 10
    assert second["sha256"] == receipt["sha256"]


def test_rendered_text_is_new_content(template, tmp_path):
    require_encoder()
    if not shutil.which("tesseract"):
        pytest.skip("Tesseract required for independent rendered-text acceptance")
    template["style"].update({"entry": "static", "font_size_ratio": .1, "fill": [255, 255, 255],
                              "highlight": [255, 255, 255], "anchor_x": .5, "anchor_y": .7})
    compose(template, content(width=640, height=360, scenes=[{"text": "FRESH CONTENT", "duration": 1,
                                                            "background": [5, 10, 15]}]), tmp_path / "project")
    checkpoint = tmp_path / "new-text.png"
    render_still(tmp_path / "project", .5, checkpoint)
    ocr = subprocess.run(["tesseract", str(checkpoint), "stdout", "--psm", "6", "-l", "eng"],
                         text=True, capture_output=True, timeout=20, check=True).stdout.upper()
    assert "FRESH CONTENT" in ocr
    assert "REFERENCE" not in ocr


def test_explicit_audio_is_muxed_with_offset(template, tmp_path):
    require_encoder()
    audio = tmp_path / "voice.wav"
    rate = 24000
    samples = (np.sin(np.arange(rate // 2) * (2 * np.pi * 440 / rate)) * 16000).astype("<i2")
    with wave.open(str(audio), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(samples.tobytes())
    compose(template, content(audio=str(audio), audio_offset=.2), tmp_path / "project")
    receipt = render(tmp_path / "project")
    assert receipt["audio_present"] is True
    with av.open(receipt["path"]) as media:
        stream = media.streams.audio[0]
        rate = stream.codec_context.sample_rate
        values = np.concatenate([frame.to_ndarray().reshape(-1) for frame in media.decode(stream)])
    before = np.sqrt(np.mean(values[:int(rate * .1)] ** 2))
    tone = np.sqrt(np.mean(values[int(rate * .3):int(rate * .5)] ** 2))
    assert tone > .1 and before < tone * .01


@pytest.mark.parametrize("transition", ["cut", "dissolve", "fade", "wipe"])
def test_transition_playback_and_relative_overlap(template, tmp_path, transition):
    require_encoder()
    template["rhythm"]["transition"] = {"family": transition, "duration": .2}
    scenes = [{"duration": 1, "background": [220, 10, 10]}, {"duration": 1, "background": [10, 10, 220]}]
    project = compose(template, content(scenes=scenes), tmp_path / "project")
    expected = 2 if transition == "cut" else 1.8
    assert project["render"]["duration"] == pytest.approx(expected)
    if transition != "cut":
        assert project["scenes"][1]["start"] == .8
    receipt = render(tmp_path / "project")
    frames = decoded(receipt["path"])
    assert len(frames) == round(expected * 10)
    assert np.asarray(frames[0])[0, 0, 0] > 180
    assert np.asarray(frames[-1])[0, 0, 2] > 180


@pytest.mark.parametrize("entry", ["static", "fade", "pop", "slide"])
def test_caption_entry_has_real_motion(template, tmp_path, entry):
    template["style"].update({"entry": entry, "entry_duration": .3})
    project = tmp_path / "project"
    compose(template, content(), project)
    render_still(project, 0, tmp_path / "start.png")
    render_still(project, .12, tmp_path / "later.png")
    difference = ImageChops.difference(Image.open(tmp_path / "start.png"), Image.open(tmp_path / "later.png"))
    assert (difference.getbbox() is None) == (entry == "static")


def test_bound_video_uses_pts_and_holds_last_frame(template, tmp_path):
    require_encoder()
    clip = tmp_path / "new-footage.mp4"
    with av.open(str(clip), "w") as container:
        stream = container.add_stream("libx264", rate=4)
        stream.width, stream.height, stream.pix_fmt = 96, 64, "yuv420p"
        for color in [(230, 20, 20), (20, 220, 20)]:
            frame = av.VideoFrame.from_image(Image.new("RGB", (96, 64), color))
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    compose(template, content(scenes=[{"asset": str(clip), "duration": 1}]), tmp_path / "project")
    receipt = render(tmp_path / "project")
    frames = decoded(receipt["path"])
    assert np.asarray(frames[0])[0, 0, 0] > 180
    assert np.asarray(frames[5])[0, 0, 1] > 180
    assert np.asarray(frames[-1])[0, 0, 1] > 180
    assert receipt["audio_present"] is False


def test_playlist_disguised_as_video_is_rejected(template, tmp_path):
    playlist = tmp_path / "playlist.mp4"
    playlist.write_text("#EXTM3U\n#EXT-X-TARGETDURATION:1\n#EXTINF:1,\noutside-secret.ts\n#EXT-X-ENDLIST\n")
    compose(template, content(scenes=[{"asset": str(playlist), "duration": 1}]), tmp_path / "project")
    with pytest.raises(ValueError, match="demuxer"):
        render_still(tmp_path / "project", .5, tmp_path / "forbidden.png")


@pytest.mark.parametrize("mutation,reason", [
    (lambda p: p["font"].update(path="../outside.ttf"), "manifest"),
    (lambda p: p["assets"][0].update(path="../outside.ttf"), "escapes"),
    (lambda p: p["scenes"][0].update(start=.1), "interval"),
    (lambda p: p["scenes"][0]["captions"][0]["words"][0].update(end=3), "word end"),
    (lambda p: p["scenes"][0]["captions"][0].update(text="unbound substitution"), "differs"),
])
def test_edited_projects_fail_closed(template, tmp_path, mutation, reason):
    folder = tmp_path / "project"
    compose(template, content(), folder)
    outside = tmp_path / "outside.ttf"
    shutil.copyfile(folder / json.loads((folder / "project.json").read_text())["font"]["path"], outside)
    project = json.loads((folder / "project.json").read_text())
    mutation(project)
    write_json(folder / "project.json", project)
    with pytest.raises(ValueError, match=reason):
        render_still(folder, .5, tmp_path / "bad.png")
    assert not (tmp_path / "bad.png").exists()


def test_mutated_asset_and_output_collision_rejected(template, tmp_path):
    folder = tmp_path / "project"
    source = tmp_path / "new-image.png"
    Image.new("RGB", (96, 64), "navy").save(source)
    project = compose(template, content(scenes=[{"asset": str(source), "duration": 1}]), folder)
    font = folder / project["font"]["path"]
    with pytest.raises(ValueError, match="cannot overwrite"):
        render_still(folder, .5, folder / project["scenes"][0]["asset"]["path"])
    font.write_bytes(font.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="asset changed"):
        render_still(folder, .5, tmp_path / "bad.png")


def test_deadline_cleans_partial_output(template, tmp_path):
    require_encoder()
    compose(template, content(width=1280, height=720), tmp_path / "project")
    output = tmp_path / "deadline.mp4"
    output.write_bytes(b"existing-output-is-preserved")
    with pytest.raises(RuntimeError, match="deadline"):
        render(tmp_path / "project", output, timeout_seconds=.01)
    assert output.read_bytes() == b"existing-output-is-preserved"
    assert not list(tmp_path.glob(".rvpm-render-*"))


def palette_reference():
    yellow, cyan = [254, 214, 67], [80, 223, 230]
    captions = []
    for index, (start, end, size, fill, stroke, color, position) in enumerate([
        (.5, 4.5, .08, [245, 245, 245], [0, 0, 0], yellow, [.45, .72]),
        (5.5, 9.5, .12, [170, 190, 210], [60, 20, 30], cyan, [.6, .65]),
    ]):
        identity, frame = f"old-caption-{index+1}", f"old-frame-{index+1}"
        captions.append({"id": identity, "shot_id": f"shot-{index+1}", "start": start, "end": end,
                         "text": "REFERENCE ORIGINAL", "evidence": [frame],
                         "word_highlights": [{"text": "REFERENCE", "start": start+.2, "end": start+.7, "fill": color}],
                         "style": {"status": "estimated", "font_size_ratio": size, "font_size_ratio_status": "candidate",
                                   "fill": fill, "stroke": stroke, "stroke_width_ratio": .003 if not index else .006,
                                   "stroke_width_status": "estimated", "position": position, "animation": "static",
                                   "highlight": color, "highlight_status": "inferred",
                                   "highlight_palette": [{"fill": color, "observed_range": [start, end], "evidence": [frame]}]}})
    return {"schema_version": 1, "kind": "rea-video-analysis", "source": {"width": 640, "height": 360,
            "duration": 10, "sha256": "c"*64}, "captions": captions,
            "shots": [{"id": "shot-1", "start": 0, "end": 5}, {"id": "shot-2", "start": 5, "end": 10}],
            "style": {"highlight": [167, 218, 148], "highlight_status": "inferred",  # Deliberately averaged aggregate.
                      "highlight_palette": [{"fill": color, "status": "inferred", "source_caption_ids": [caption["id"]],
                                             "evidence": caption["evidence"]} for caption, color in zip(captions, [yellow, cyan])]},
            "unknowns": []}


def palette_bindings():
    return content(width=640, height=360, scenes=[{"text": "BRAND NEW", "duration": 2, "background": [5, 10, 15]},
                                                 {"text": "FUTURE STORY", "duration": 2, "background": [5, 10, 15]}])


def count_color(image, color, tolerance=12):
    pixels = np.asarray(image).astype(int)
    mask = np.max(np.abs(pixels[:, :, :3] - color), axis=2) <= tolerance
    ys, _ = np.where(mask)
    return int(np.count_nonzero(mask)), int(ys.max()-ys.min()+1) if len(ys) else 0


def test_discrete_palette_and_typography_reach_actual_new_video(tmp_path):
    require_encoder()
    reference = palette_reference()
    template = extract_template(reference)
    colors = [entry["fill"] for entry in template["highlight_palette"]["colors"]]
    assert colors == [[254, 214, 67], [80, 223, 230]]
    assert template["style"]["highlight"] == colors[0]  # The deliberately averaged aggregate is not used.
    assert [regime["relative_start"] for regime in template["highlight_palette"]["regimes"]] == [0, .5]
    assert len(template["style_variants"]) == 2
    project = compose(template, palette_bindings(), tmp_path / "project")
    assert [cue["start"] for cue in project["captions"]] == [0, 2]
    assert [word["text"] for cue in project["captions"] for word in cue["words"]] == ["BRAND", "NEW", "FUTURE", "STORY"]
    assert all(word["timing"] == "estimated-from-new-text" for cue in project["captions"] for word in cue["words"])
    assert project["captions"][0]["words"][0]["start"] == 0
    assert project["captions"][1]["style"]["font_size_ratio"] == .12
    assert project["captions"][1]["style"]["fill"] == [170, 190, 210]
    assert project["captions"][1]["style"]["stroke"] == [60, 20, 30]
    receipt = render(tmp_path / "project")
    frames = decoded(receipt["path"])
    early, late = frames[15], frames[35]
    yellow_count, yellow_height = count_color(early, colors[0], tolerance=20)
    cyan_count, cyan_height = count_color(late, colors[1], tolerance=20)
    assert yellow_count > 30 and cyan_count > 30
    assert count_color(early, colors[1], tolerance=20)[0] == 0
    assert count_color(late, colors[0], tolerance=20)[0] == 0
    assert cyan_height > yellow_height * 1.2
    assert count_color(early, [245, 245, 245], tolerance=20)[0] > 20
    assert count_color(late, [170, 190, 210], tolerance=20)[0] > 20
    assert count_color(late, [60, 20, 30], tolerance=15)[0] > 20


def test_explicit_scene_accent_overrides_automatic_palette(tmp_path):
    template = extract_template(palette_reference())
    bindings = palette_bindings()
    for scene in bindings["scenes"]:
        scene["accent"] = [245, 70, 210]
    project = compose(template, bindings, tmp_path / "project")
    assert all(word["highlight"] == [245, 70, 210] and word["highlight_source"] == "explicit-content-accent"
               for cue in project["captions"] for word in cue["words"])
    render_still(tmp_path / "project", 3.5, tmp_path / "accent.png")
    image = Image.open(tmp_path / "accent.png")
    assert count_color(image, [245, 70, 210])[0] > 30
    assert count_color(image, [80, 223, 230])[0] == 0


def test_palette_schedule_preserves_new_asr_word_timings(tmp_path):
    template = extract_template(palette_reference())
    words = [{"text": "BRAND", "start": .1, "end": .8, "timing": "model-derived-asr"},
             {"text": "NEW", "start": 1.1, "end": 1.7, "timing": "model-derived-asr"}]
    bindings = content(width=640, height=360, timing_policy="audio-anchored", scenes=[{"text": "BRAND NEW", "duration": 2, "words": words}])
    project = compose(template, bindings, tmp_path / "project")
    actual = project["scenes"][0]["captions"][0]["words"]
    assert [(word["start"], word["end"], word["timing"]) for word in actual] == [(.1, .8, "model-derived-asr"), (1.1, 1.7, "model-derived-asr")]
    assert actual[0]["highlight"] == [254, 214, 67] and actual[1]["highlight"] == [80, 223, 230]


def test_unknown_palette_and_type_values_do_not_become_observed_variants(tmp_path):
    reference = palette_reference()
    reference["style"]["highlight_palette"] = []
    for caption in reference["captions"]:
        caption["style"]["highlight_status"] = "unknown"
        caption["style"]["font_size_ratio_status"] = "unknown"
    template = extract_template(reference)
    assert template["highlight_palette"]["status"] == "unknown"
    assert template["highlight_palette"]["colors"] == []
    assert all("font_size_ratio" not in variant["style"] for variant in template["style_variants"])
    project = compose(template, palette_bindings(), tmp_path / "project")
    assert all("highlight_regime_id" not in word for cue in project["captions"] for word in cue["words"])


def test_unsafe_cue_style_override_rejected_on_render(tmp_path):
    project = compose(extract_template(palette_reference()), palette_bindings(), tmp_path / "project")
    project["scenes"][0]["captions"][0]["style"]["font_size_ratio"] = 1000000
    write_json(tmp_path / "project" / "project.json", project)
    with pytest.raises(ValueError, match="font_size_ratio"):
        render_still(tmp_path / "project", .5, tmp_path / "bad.png")


@pytest.mark.parametrize("bad", [["untyped"], [{"fill": [255, 0, 0], "status": "inferred", "evidence": "frame-1"}]])
def test_malformed_highlight_palette_fails_before_project_creation(bad):
    reference = palette_reference()
    reference["captions"][0]["style"]["highlight_palette"] = bad
    with pytest.raises(ValueError, match="palette|evidence"):
        extract_template(reference)
