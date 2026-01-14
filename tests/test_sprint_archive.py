from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "cli_plan" / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


@pytest.mark.parametrize(
    ("scope", "base_rel"),
    [
        ("project", ""),
        ("system", ".project-handbook/system"),
    ],
)
def test_sprint_archive_moves_directory_into_sprints_archive(tmp_path: Path, scope: str, base_rel: str) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    planned = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert planned.returncode == 0

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "archive"]
    archived = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert archived.returncode == 0

    base = tmp_path if scope == "project" else (tmp_path / base_rel)
    original = base / "sprints" / "2099" / "SPRINT-2099-01-01"
    target = base / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01"
    assert not original.exists()
    assert target.exists()
