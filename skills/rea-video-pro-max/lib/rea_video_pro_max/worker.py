"""Internal worker: only fixed operations, never eval/shell or arbitrary plugins."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from .core import read_json, write_json
from .operations import execute, revision


def main():
    request_path = Path(sys.argv[1]).resolve()
    folder = request_path.parent
    status = read_json(folder/"status.json")
    try:
        request = read_json(request_path)
        expected = request.pop("expected_sha256", None)
        if expected and revision(request["input_path"]) != expected:
            raise ValueError("Input revision changed before execution")
        result = execute(**request)
        write_json(folder/"result.json", result)
        write_json(folder/"status.json", {**status, "status": "failed" if result.get("status") == "failed" else "completed",
                                         "finished_at": time.time(), "result_path": str((folder/"result.json").relative_to(Path(request["workspace"])))})
        return 0
    except Exception as error:
        write_json(folder/"status.json", {**status, "status": "failed", "finished_at": time.time(),
                                         "error": type(error).__name__, "reason": str(error)[:2000]})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
