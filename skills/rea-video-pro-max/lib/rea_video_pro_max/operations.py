"""One operation router shared by CLI and workspace-bound job workers."""
from __future__ import annotations

from pathlib import Path

from .core import confined, read_json, sha256, validate, write_json

OPERATIONS = {"analyze", "template", "compose", "render", "report", "export", "verify", "timeline", "transcribe", "bind-speech"}


def artifact_path(path, operation=None):
    path = Path(path).resolve()
    if path.is_dir():
        filename = "project.json" if operation == "render" or (operation in {None, "verify"} and (path / "project.json").is_file()) else "analysis.json"
        return path / filename
    return path


def execute(operation: str, input_path: str | Path, out_path: str | Path,
            options: dict | None = None, *, workspace: str | Path | None = None) -> dict:
    if operation not in OPERATIONS:
        raise ValueError("Unknown operation")
    options = dict(options or {})
    allowed = {
        "analyze": {"ocr", "ocr_lang", "max_seconds", "sample_fps", "transcript", "motion_profile"},
        "transcribe": {"model_dir", "language", "max_seconds", "timeout_seconds", "cpu_threads", "compute_type"},
        "bind-speech": {"transcript"},
        "compose": {"content"}, "render": {"timeout_seconds"},
        "report": {"include_media"}, "export": {"format"},
        "verify": {"mode", "render_path", "ocr_lang"}, "template": set(), "timeline": set(),
    }
    if options.keys() - allowed[operation]:
        raise ValueError("Unknown option(s): " + ", ".join(sorted(options.keys() - allowed[operation])))
    source = Path(input_path).resolve()
    target = Path(out_path).resolve()
    if workspace:
        source = confined(workspace, source, must_exist=True)
        target = confined(workspace, target)
        for name in ("content", "transcript", "render_path", "model_dir"):
            if options.get(name):
                options[name] = str(confined(workspace, options[name], must_exist=True))
    if source == target or (source.is_file() and source.is_relative_to(target) and operation == "analyze"):
        raise ValueError("Output must not replace or contain input media")
    if operation == "analyze":
        from .analysis import analyze
        return analyze(source, target, **options)
    if operation == "transcribe":
        from .asr import transcribe
        return transcribe(source, options.pop("model_dir"), target, **options)
    path = artifact_path(source, operation)
    if workspace:
        path = confined(workspace, path, must_exist=True)
    value = read_json(path)
    if value.get("kind") in {"rea-video-analysis", "rea-video-style-template", "rea-video-project", "rea-video-content"}:
        validate(value)
    if operation == "bind-speech":
        from .timing import bind_speech
        result = bind_speech(value, read_json(options["transcript"]), path.parent, workspace=workspace)
        # Output bindings resolve copied media from their new directory.
        for key in ("audio", "font"):
            if result.get(key):
                result[key] = str((path.parent / result[key]).resolve())
        for scene in result["scenes"]:
            if scene.get("asset"):
                scene["asset"] = str((path.parent / scene["asset"]).resolve())
        write_json(target, result)
        return result
    if operation == "template":
        from .template import extract_template
        validate(value, "rea-video-analysis")
        result = extract_template(value)
        write_json(target, result)
        return result
    if operation == "compose":
        from .template import compose
        content_path = Path(options["content"]).resolve()
        content = read_json(content_path)
        validate(content, "rea-video-content")
        content.pop("_base_dir", None)
        content["_base_dir"] = str(content_path.parent)
        if workspace:
            for key in ("font", "audio"):
                if content.get(key):
                    confined(workspace, content_path.parent / content[key], must_exist=True)
            for scene in content["scenes"]:
                if scene.get("asset"):
                    confined(workspace, content_path.parent / scene["asset"], must_exist=True)
        return compose(value, content, target)
    if operation == "render":
        from .render import render
        return render(path, target, **options)
    if operation in {"report", "verify"} and value.get("kind") == "rea-video-analysis" and workspace:
        confined(workspace, value["source"]["path"], must_exist=True)
        # Copying a symlinked evidence tree could escape the explicit workspace.
        evidence = path.parent / "evidence"
        if evidence.exists():
            for item in evidence.rglob("*"):
                if item.is_symlink():
                    raise ValueError("Evidence symlinks are not allowed in MCP jobs")
                confined(workspace, item, must_exist=True)
    if operation == "report":
        from .reports import report
        return report(value, target, analysis_dir=path.parent, **options)
    if operation == "export":
        from .exporters import export_analysis
        return export_analysis(value, target, **options)
    if operation == "timeline":
        from .exporters import native_timeline
        result = native_timeline(value)
        write_json(target, result)
        return result
    from .verification import verify
    result = verify(path, **options)
    write_json(target, result)
    return result


def revision(path):
    return sha256(artifact_path(path))
