"""Independent boundary/CLI/MCP acceptance for the root-owned orchestration modules."""

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

from rea_video_pro_max.core import confined, read_json, sha256, write_json
from rea_video_pro_max.jobs import Jobs
from rea_video_pro_max.operations import execute
from rea_video_pro_max.template import compose, extract_template
from rea_video_pro_max.verification import verify

PACKAGE_LIB = Path(__file__).resolve().parents[1] / "skills/rea-video-pro-max/lib"


def environment():
    result = dict(os.environ)
    result["PYTHONPATH"] = str(PACKAGE_LIB) + os.pathsep + result.get("PYTHONPATH", "")
    return result


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def seed_analysis(workspace):
    media = workspace / "reference.mp4"
    media.write_bytes(b"owned synthetic source identity")
    analysis = {"schema_version": 1, "kind": "rea-video-analysis",
                "source": {"path": str(media), "sha256": sha256(media), "width": 320, "height": 180,
                           "duration": 2.0, "fps": 10},
                "shots": [{"id": "shot-1", "start": 0, "end": 2}],
                "captions": [{"id": "caption-1", "start": 0, "end": 2, "text": "original content",
                              "bbox": [.1, .7, .8, .15], "style": {"animation": "static"}}],
                "coverage": {"decoded_frames": 20, "sampled_frames": 8}, "evidence": [], "unknowns": []}
    directory = workspace / "analysis"
    directory.mkdir()
    write_json(directory / "analysis.json", analysis)
    return analysis, directory


def seed_project(workspace, *, long=False):
    analysis, _ = seed_analysis(workspace)
    template = extract_template(analysis)
    content = {"kind": "rea-video-content", "schema_version": 1, "width": 1280 if long else 160,
               "height": 720 if long else 90, "fps": 10,
               "scenes": [{"text": "new independent content", "duration": 30 if long else .5}]}
    directory = workspace / "project"
    compose(template, content, directory)
    return directory


def wait_terminal(jobs, job_id, *, deadline=10):
    until = time.monotonic() + deadline
    while time.monotonic() < until:
        status = jobs.status(job_id)
        if status["status"] != "running":
            return status
        time.sleep(.025)
    pytest.fail("job did not reach a terminal state")


def test_core_rejects_parent_and_symlink_escapes(workspace, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("outside workspace")
    (workspace / "link.txt").symlink_to(secret)
    for path in ("../secret.txt", "link.txt", str(secret)):
        with pytest.raises(ValueError, match="outside"):
            confined(workspace, path, must_exist=True)


def test_operation_directory_render_matches_cli_documentation(workspace):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required")
    project = seed_project(workspace)
    result = execute("render", project, workspace / "result.mp4", workspace=workspace)
    assert result["frame_count"] == 5
    assert (workspace / "result.mp4").is_file()


def test_directory_artifact_symlink_cannot_escape(workspace, tmp_path):
    analysis, folder = seed_analysis(workspace)
    outside = tmp_path / "external-analysis.json"
    write_json(outside, analysis)
    (folder / "analysis.json").unlink()
    (folder / "analysis.json").symlink_to(outside)
    with pytest.raises(ValueError, match="outside"):
        execute("template", folder, workspace / "leak.json", workspace=workspace)
    assert not (workspace / "leak.json").exists()


@pytest.mark.parametrize("binding", ["asset", "font", "audio"])
def test_nested_content_bindings_confined_before_access(workspace, tmp_path, binding):
    analysis, _ = seed_analysis(workspace)
    write_json(workspace / "style.json", extract_template(analysis))
    outside = tmp_path / "outside.png"
    Image.new("RGB", (64, 64), "red").save(outside)
    (workspace / "linked.png").symlink_to(outside)
    value = {"kind": "rea-video-content", "schema_version": 1,
             "scenes": [{"text": "new text", "duration": 1}]}
    if binding == "asset":
        value["scenes"][0]["asset"] = "linked.png"
    else:
        value[binding] = "linked.png"
    write_json(workspace / "bindings.json", value)
    with pytest.raises(ValueError, match="outside"):
        execute("compose", workspace / "style.json", workspace / "new-project",
                {"content": "bindings.json"}, workspace=workspace)
    assert not (workspace / "new-project" / "project.json").exists()


def test_report_rejects_symlinked_evidence(workspace, tmp_path):
    _, folder = seed_analysis(workspace)
    evidence = folder / "evidence"
    evidence.mkdir()
    secret = tmp_path / "private.txt"
    secret.write_text("private data")
    (evidence / "frame.txt").symlink_to(secret)
    with pytest.raises(ValueError, match="symlink"):
        execute("report", folder, workspace / "report", workspace=workspace)
    assert not (workspace / "report" / "evidence" / "frame.txt").exists()


def test_export_verification_cannot_stat_outside_workspace(workspace, tmp_path):
    outside = tmp_path / "secret.txt"
    outside.write_text("private")
    write_json(workspace / "receipt.json", {"kind": "rea-video-export-receipt", "schema_version": 1,
                                           "file": "../secret.txt", "losses": []})
    with pytest.raises(ValueError):
        execute("verify", workspace / "receipt.json", workspace / "verification.json",
                {"mode": "export"}, workspace=workspace)


def test_render_receipt_symlink_cannot_escape(workspace, tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required")
    project = seed_project(workspace)
    execute("render", project, workspace / "render.mp4", workspace=workspace)
    receipt = workspace / "render.receipt.json"
    outside = tmp_path / "outside-receipt.json"
    shutil.move(str(receipt), outside)
    receipt.symlink_to(outside)
    with pytest.raises(ValueError):
        execute("verify", project / "project.json", workspace / "verdict.json",
                {"mode": "style-transfer", "render_path": "render.mp4"}, workspace=workspace)


def test_cli_malformed_nested_artifact_has_structured_error(workspace):
    write_json(workspace / "invalid.json", {"schema_version": 1, "kind": "rea-video-analysis",
                                           "source": {"duration": 1}, "shots": [1]})
    result = subprocess.run([sys.executable, "-m", "rea_video_pro_max.cli", "template",
                             str(workspace / "invalid.json"), "--out", str(workspace / "style.json")],
                            env=environment(), text=True, capture_output=True, timeout=10)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["status"] == "error"
    assert not (workspace / "style.json").exists()


def test_cli_malformed_caption_has_structured_error(workspace):
    analysis, folder = seed_analysis(workspace)
    analysis["captions"] = [1]
    write_json(folder / "analysis.json", analysis)
    result = subprocess.run([sys.executable, "-m", "rea_video_pro_max.cli", "template", str(folder),
                             "--out", str(workspace / "bad-style.json")], env=environment(),
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["status"] == "error"


def test_cli_replay_compose_render_verify(workspace):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required")
    analysis, folder = seed_analysis(workspace)
    style = workspace / "style.json"
    bindings = workspace / "bindings.json"
    write_json(bindings, {"kind": "rea-video-content", "schema_version": 1, "width": 640, "height": 360,
                          "fps": 10, "scenes": [{"text": "FRESH WORDS", "duration": .5}]})
    commands = [
        ["template", str(folder), "--out", str(style)],
        ["compose", str(style), "--content", str(bindings), "--out", str(workspace / "project")],
        ["render", str(workspace / "project"), "--out", str(workspace / "video-b.mp4")],
        ["verify", str(workspace / "project" / "project.json"), "--mode", "style-transfer", "--render", str(workspace / "video-b.mp4"), "--ocr-lang", "eng"],
    ]
    for command in commands:
        result = subprocess.run([sys.executable, "-m", "rea_video_pro_max.cli", *command], env=environment(),
                                text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr or result.stdout
        output = json.loads(result.stdout)
        assert output.get("status") not in {"failed", "error"}
    assert output["status"] == "passed"
    assert read_json(workspace / "project" / "project.json")["reference"]["sha256"] == analysis["source"]["sha256"]


def test_jobs_cancel_process_tree_and_deadline(workspace):
    project = seed_project(workspace, long=True)
    jobs = Jobs(workspace, timeout=10)
    try:
        job = jobs.start("render", project / "project.json", "cancelled.mp4")
        status = jobs.cancel(job["job_id"])
        assert status["status"] == "cancelled"
        assert jobs.processes[job["job_id"]].poll() is not None
        assert jobs.status(job["job_id"])["status"] == "cancelled"
    finally:
        jobs.close()
    deadline_jobs = Jobs(workspace, timeout=.03)
    try:
        job = deadline_jobs.start("render", project / "project.json", "deadline.mp4")
        status = wait_terminal(deadline_jobs, job["job_id"])
        assert status["status"] == "timed-out", status
        assert deadline_jobs.processes[job["job_id"]].poll() is not None
        assert not (workspace / "deadline.mp4").exists()
    finally:
        deadline_jobs.close()


def test_jobs_reserve_overlapping_output_paths(workspace):
    project = seed_project(workspace, long=True)
    jobs = Jobs(workspace, timeout=10)
    try:
        jobs.start("render", project / "project.json", "collision.mp4")
        with pytest.raises(ValueError):
            jobs.start("render", project / "project.json", "collision.mp4")
    finally:
        jobs.close()


def test_revision_checked_in_parent_and_worker(workspace):
    _, folder = seed_analysis(workspace)
    source = folder / "analysis.json"
    jobs = Jobs(workspace)
    try:
        with pytest.raises(ValueError, match="revision"):
            jobs.start("template", source, "stale.json", expected_sha256="0" * 64)
    finally:
        jobs.close()
    request = workspace / "worker-case"
    request.mkdir()
    write_json(request / "status.json", {"job_id": "a" * 32, "status": "running"})
    write_json(request / "request.json", {"operation": "template", "input_path": str(source),
                                          "out_path": str(workspace / "worker-style.json"), "options": {},
                                          "workspace": str(workspace), "expected_sha256": "0" * 64})
    result = subprocess.run([sys.executable, "-m", "rea_video_pro_max.worker", str(request / "request.json")],
                            env=environment(), capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    status = read_json(request / "status.json")
    assert status["status"] == "failed" and "revision" in status["reason"]
    assert not (workspace / "worker-style.json").exists()


def test_project_directory_revision_checked_before_render(workspace):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required")
    project = seed_project(workspace)
    jobs = Jobs(workspace, timeout=10)
    try:
        job = jobs.start("render", project, "revision-bound.mp4", expected_sha256=sha256(project / "project.json"))
        assert wait_terminal(jobs, job["job_id"])["status"] == "completed"
    finally:
        jobs.close()


def test_report_markup_is_escaped(workspace):
    analysis, folder = seed_analysis(workspace)
    payload = "</script><script>alert('untrusted')</script>"
    analysis["captions"][0]["text"] = payload
    write_json(folder / "analysis.json", analysis)
    execute("report", folder, workspace / "report", {"include_media": False}, workspace=workspace)
    html = (workspace / "report" / "timeline.html").read_text()
    assert payload not in html and "\\u003c/script>" in html
    assert "textContent=item.text" in html


def test_csv_all_untrusted_text_columns_neutralized(workspace):
    import csv
    analysis, folder = seed_analysis(workspace)
    analysis["shots"][0]["id"] = "=1+1"
    analysis["shots"][0]["type"] = "=1+2"
    write_json(folder / "analysis.json", analysis)
    try:
        execute("export", folder, workspace / "csv", {"format": "csv"}, workspace=workspace)
    except ValueError:
        return  # Rejecting invalid input is also an acceptable boundary.
    with (workspace / "csv" / "shots.csv").open(newline="") as stream:
        fields = next(iter(list(csv.reader(stream))[1:]))
    assert all(not field.startswith(("=", "+", "-", "@")) for field in fields), fields


def test_wrong_content_video_does_not_pass_style_transfer(workspace):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg required")
    project = seed_project(workspace)
    unrelated = workspace / "wrong.mp4"
    command = ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=black:s=160x90:r=10:d=0.5",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", str(unrelated)]
    subprocess.run(command, capture_output=True, timeout=10, check=True)
    result = verify(project / "project.json", mode="style-transfer", render_path=unrelated)
    assert result["status"] != "passed", result


@pytest.mark.parametrize("actual,expected", [("SAFE NOT", "NOT SAFE"), ("VERY GOOD", "VERY VERY GOOD")])
def test_caption_observation_checks_word_order_and_multiplicity(workspace, actual, expected):
    if not shutil.which("ffmpeg") or not shutil.which("tesseract"):
        pytest.skip("FFmpeg and Tesseract required for independent content observation")
    from rea_video_pro_max.verification import _ocr_cues
    analysis, _ = seed_analysis(workspace)
    template = extract_template(analysis)
    template["style"]["words_per_group"] = 5
    project = compose(template, {"kind": "rea-video-content", "schema_version": 1,
        "width": 640, "height": 360, "fps": 10, "scenes": [{"text": actual, "duration": .5}]}, workspace / "project")
    execute("render", workspace / "project", workspace / "observed.mp4", workspace=workspace)
    project["captions"][0]["text"] = expected
    result = _ocr_cues(project, workspace / "observed.mp4", "eng")
    assert result["status"] == "failed", result


def test_official_mcp_stdio_client_task_lifecycle(workspace, tmp_path):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _, analysis_dir = seed_analysis(workspace)
    outside = tmp_path / "secret.txt"
    outside.write_text("must not be paged")

    async def run():
        parameters = StdioServerParameters(command=sys.executable,
            args=["-m", "rea_video_pro_max.mcp_server", "--workspace", str(workspace), "--job-timeout", "10"],
            env=environment())
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert init.serverInfo.name == "REA Video Pro Max"
                listed = await session.list_tools()
                assert {t.name for t in listed.tools} == {"capabilities", "start_job", "job_status", "cancel_job", "read_artifact"}
                async def call(name, arguments):
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, result
                    return result.structuredContent or json.loads(result.content[0].text)
                async def finish(job):
                    until = time.monotonic() + 10
                    while True:
                        status = await call("job_status", {"job_id": job["job_id"]})
                        if status["status"] != "running":
                            break
                        assert time.monotonic() < until
                        await asyncio.sleep(.05)
                    assert status["status"] == "completed", status
                    page = await call("read_artifact", {"path": status["result_path"], "limit": 64000})
                    return json.loads(page["text"])
                capability = await call("capabilities", {})
                assert capability["kind"] == "rea-video-capabilities"
                escaped = await session.call_tool("read_artifact", {"path": str(outside)})
                assert escaped.isError
                request = {"operation": "template", "input_path": str(analysis_dir), "out_path": "mcp-style.json",
                           "expected_sha256": hashlib.sha256((analysis_dir / "analysis.json").read_bytes()).hexdigest()}
                job = await call("start_job", request)
                result = await finish(job)
                assert result["kind"] == "rea-video-style-template"
                page = await call("read_artifact", {"path": "mcp-style.json", "offset": 0, "limit": 7})
                assert page["next_offset_bytes"] == 7 and page["untrusted_content"] is True
                conflict = await session.call_tool("start_job", {**request, "out_path": "conflict.json", "expected_sha256": "0" * 64})
                assert conflict.isError
                cancel = await call("cancel_job", {"job_id": job["job_id"]})
                assert cancel["status"] == "completed"
                if shutil.which("ffmpeg") and shutil.which("tesseract"):
                    write_json(workspace / "mcp-bindings.json", {"kind": "rea-video-content", "schema_version": 1,
                        "width": 640, "height": 360, "fps": 10,
                        "scenes": [{"text": "BRAND NEW", "duration": .5}]})
                    composed = await call("start_job", {"operation": "compose", "input_path": "mcp-style.json",
                        "out_path": "mcp-project", "options": {"content": "mcp-bindings.json"}})
                    assert (await finish(composed))["kind"] == "rea-video-project"
                    rendered = await call("start_job", {"operation": "render", "input_path": "mcp-project",
                        "out_path": "mcp-video.mp4", "expected_sha256": sha256(workspace / "mcp-project" / "project.json")})
                    assert (await finish(rendered))["frame_count"] == 5
                    verification = await call("start_job", {"operation": "verify", "input_path": "mcp-project",
                        "out_path": "mcp-verdict.json", "options": {"mode": "style-transfer",
                            "render_path": "mcp-video.mp4", "ocr_lang": "eng"}})
                    assert (await finish(verification))["status"] == "passed"
    asyncio.run(run())


def test_shipped_skill_wrapper_propagates_failure_exit_code(workspace):
    write_json(workspace / 'bad.json', {'schema_version': 1, 'kind': 'unknown-artifact'})
    script = PACKAGE_LIB.parent / 'scripts' / 'rea-video-pro-max.py'
    result = subprocess.run([sys.executable, str(script), 'template', str(workspace / 'bad.json'),
                             '--out', str(workspace / 'bad-style.json')], capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert json.loads(result.stderr)['status'] == 'error'
    assert not (workspace / 'bad-style.json').exists()
