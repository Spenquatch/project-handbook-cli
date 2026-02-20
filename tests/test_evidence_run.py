from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": "1",\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def test_evidence_run_captures_stdout_stderr_and_exit_code(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    run_id = "20260101T000000Z-v2-smoke"
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "evidence",
            "run",
            "--task",
            "TASK-001",
            "--name",
            "v2-smoke",
            "--run-id",
            run_id,
            "--",
            sys.executable,
            "-c",
            "import sys; print('ok'); sys.stderr.write('warn\\n'); sys.exit(3)",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3

    run_dir = tmp_path / ".project-handbook" / "status" / "evidence" / "TASK-001" / run_id
    assert (run_dir / "cmd.txt").exists()
    assert (run_dir / "stdout.txt").exists()
    assert (run_dir / "stderr.txt").exists()
    assert (run_dir / "meta.json").exists()

    assert (run_dir / "stdout.txt").read_text(encoding="utf-8").strip() == "ok"
    assert (run_dir / "stderr.txt").read_text(encoding="utf-8").strip() == "warn"

    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["exit_code"] == 3
    assert meta["started_at_utc"]
    assert meta["finished_at_utc"]
    assert meta["duration_ms"] >= 0


def test_evidence_run_missing_command_returns_127_and_writes_error(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    run_id = "20260101T000000Z-missing"
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "evidence",
            "run",
            "--task",
            "TASK-001",
            "--name",
            "missing",
            "--run-id",
            run_id,
            "--",
            "definitely-not-a-real-command-xyz",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 127

    run_dir = tmp_path / ".project-handbook" / "status" / "evidence" / "TASK-001" / run_id
    assert (run_dir / "stderr.txt").exists()
    assert "Command not found" in (run_dir / "stderr.txt").read_text(encoding="utf-8")

    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["exit_code"] == 127
    assert meta["error"]
