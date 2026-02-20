from __future__ import annotations

import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": "1",\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def test_evidence_new_creates_run_dir_and_index(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    run_id = "20260101T000000Z-manual"
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "evidence",
            "new",
            "--task",
            "TASK-001",
            "--name",
            "manual",
            "--run-id",
            run_id,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    index = tmp_path / ".project-handbook" / "status" / "evidence" / "TASK-001" / run_id / "index.md"
    assert index.exists()
    assert "EVIDENCE_RUN_DIR=" in result.stdout
    assert f"EVIDENCE_RUN_ID={run_id}" in result.stdout
