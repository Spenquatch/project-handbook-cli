from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_init_creates_root_marker_and_is_idempotent(tmp_path: Path) -> None:
    result = subprocess.run(
        ["ph", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "Created: project_handbook.config.json"

    marker = tmp_path / "project_handbook.config.json"
    assert marker.exists()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data == {
        "handbook_schema_version": 1,
        "requires_ph_version": ">=0.1.0,<0.2.0",
        "repo_root": ".",
    }

    assert (tmp_path / "process" / "checks" / "validation_rules.json").exists()
    assert (tmp_path / "process" / "automation" / "system_scope_config.json").exists()
    assert (tmp_path / "process" / "automation" / "reset_spec.json").exists()
    assert (tmp_path / "process" / "sessions" / "templates").exists()

    result2 = subprocess.run(
        ["ph", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0
    assert result2.stdout.strip() == "Already exists: project_handbook.config.json"


def test_init_uses_root_override(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / "target"
    target.mkdir()

    result = subprocess.run(
        ["ph", "--root", str(target), "init"],
        cwd=outside,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (target / "project_handbook.config.json").exists()
