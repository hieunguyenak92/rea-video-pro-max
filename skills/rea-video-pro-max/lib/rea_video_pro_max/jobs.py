"""Bounded, cancellable subprocess jobs for the local MCP service."""
from __future__ import annotations

import os
import base64
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from .core import confined, read_json, write_json
from .operations import OPERATIONS, revision


class Jobs:
    def __init__(self, workspace: str | Path, *, max_jobs=2, timeout=3600):
        self.root = Path(workspace).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("workspace must be an existing directory")
        self.directory = confined(self.root, ".rea-video-jobs")
        self.directory.mkdir(exist_ok=True)
        self.max_jobs = max_jobs
        self.timeout = timeout
        self.processes = {}
        self.outputs = {}
        self.lock = threading.RLock()

    def start(self, operation, input_path, out_path, options=None, expected_sha256=None):
        if operation not in OPERATIONS:
            raise ValueError("Unsupported job operation")
        source = confined(self.root, input_path, must_exist=True)
        output = confined(self.root, out_path)
        if expected_sha256 and revision(source) != expected_sha256:
            raise ValueError("Input revision conflict; reread before starting the job")
        # Validate nested paths again in the child immediately before media access.
        with self.lock:
            if output.exists() or any(p.poll() is None and (output.is_relative_to(self.outputs[j]) or self.outputs[j].is_relative_to(output)) for j, p in self.processes.items()):
                raise ValueError("Job output must be new and disjoint from active job outputs")
            if sum(p.poll() is None for p in self.processes.values()) >= self.max_jobs:
                raise ValueError("Concurrent job budget reached; wait or cancel a job")
            job_id = uuid.uuid4().hex
            folder = self.directory / job_id
            folder.mkdir()
            request = {"operation": operation, "input_path": str(source), "out_path": str(output),
                       "options": options or {}, "workspace": str(self.root), "expected_sha256": expected_sha256}
            write_json(folder / "request.json", request)
            write_json(folder / "status.json", {"job_id": job_id, "status": "running", "started_at": time.time(), "operation": operation})
            environment = dict(os.environ)
            # Skills run without an installed wheel; children must import the same package.
            environment["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent) + os.pathsep + environment.get("PYTHONPATH", "")
            with (folder / "stderr.log").open("wb") as log:
                process = subprocess.Popen([sys.executable, "-m", "rea_video_pro_max.worker", str(folder / "request.json")],
                                           cwd=self.root, env=environment, stdout=subprocess.DEVNULL,
                                           stderr=log, start_new_session=True)
            self.processes[job_id] = process
            self.outputs[job_id] = output
            threading.Thread(target=self._watch, args=(job_id, process), daemon=True).start()
            return {"job_id": job_id, "status": "running", "status_path": str((folder/"status.json").relative_to(self.root))}

    def _stop(self, process):
        if process.poll() is None:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    if process.poll() is None:
                        raise
            else:
                process.kill()
            process.wait(timeout=10)

    def _watch(self, job_id, process):
        try:
            process.wait(timeout=self.timeout)
            with self.lock:
                status = self.status(job_id)
                if status["status"] == "running":
                    write_json(self.directory/job_id/"status.json", {**status, "status": "failed", "reason": "worker exited without result", "exit_code": process.returncode})
        except subprocess.TimeoutExpired:
            with self.lock:
                self._stop(process)
                status = self.status(job_id)
                write_json(self.directory/job_id/"status.json", {**status, "status": "timed-out", "reason": "bounded job deadline exceeded; partial artifacts may remain"})

    def status(self, job_id):
        if not isinstance(job_id, str) or len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
            raise ValueError("Invalid job ID")
        return read_json(confined(self.root, self.directory/job_id/"status.json", must_exist=True))

    def cancel(self, job_id):
        with self.lock:
            status = self.status(job_id)
            process = self.processes.get(job_id)
            if status["status"] != "running":
                return status
            if process and process.poll() is None:
                self._stop(process)
                status = {**status, "status": "cancelled", "reason": "cancelled; completed evidence and partial files may remain"}
                write_json(self.directory/job_id/"status.json", status)
            elif status["status"] == "running":
                status = {**status, "status": "interrupted", "reason": "worker handle unavailable in this server session"}
            return status

    def close(self):
        for job_id in list(self.processes):
            self.cancel(job_id)

    def read(self, path, offset=0, limit=16000):
        if not isinstance(offset, int) or offset < 0 or not isinstance(limit, int) or not 1 <= limit <= 64000:
            raise ValueError("Use non-negative byte offset and limit 1..64000")
        target = confined(self.root, path, must_exist=True)
        if target.suffix.lower() not in {".json", ".md", ".txt", ".csv", ".srt", ".vtt", ".ass", ".edl", ".log"}:
            raise ValueError("Artifact paging supports text formats only")
        with target.open("rb") as file:
            file.seek(offset)
            data = file.read(limit)
        return {"path": str(target.relative_to(self.root)), "offset_bytes": offset,
                "next_offset_bytes": offset+len(data), "total_bytes": target.stat().st_size,
                "text": data.decode("utf-8", "replace"), "bytes_base64": base64.b64encode(data).decode("ascii"),
                "text_note": "For lossless concatenation across multibyte boundaries decode concatenated bytes_base64 chunks.", "untrusted_content": True}
