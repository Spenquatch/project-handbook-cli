from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
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


def _plan_sprint(*, ph_root: Path, scope: str) -> None:
    cmd = ["ph", "--root", str(ph_root)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0


@pytest.mark.parametrize("scope", ["project", "system"])
def test_backlog_assign_defaults_to_current_and_updates_front_matter(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)
    _plan_sprint(ph_root=tmp_path, scope=scope)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    issue_id = "BUG-P1-20990101-090000"

    base = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        base += ["--scope", "system"]

    created = subprocess.run(
        base
        + [
            "--no-post-hook",
            "backlog",
            "add",
            "--type",
            "bug",
            "--title",
            "T",
            "--severity",
            "P1",
            "--desc",
            "D",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert created.returncode == 0

    assigned = subprocess.run(
        base + ["--no-post-hook", "backlog", "assign", "--issue", issue_id],
        capture_output=True,
        text=True,
        env=env,
    )
    assert assigned.returncode == 0
    assert f"✅ Recorded assignment: {issue_id} → SPRINT-2099-01-01" in assigned.stdout

    data_root = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    readme = data_root / "backlog" / "bugs" / issue_id / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "sprint: SPRINT-2099-01-01" in content


def test_backlog_assign_missing_current_sprint_prints_tip_and_exits_1(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    issue_id = "BUG-P1-20990101-090000"

    created = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "backlog",
            "add",
            "--type",
            "bug",
            "--title",
            "T",
            "--severity",
            "P1",
            "--desc",
            "D",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert created.returncode == 0

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "assign", "--issue", issue_id],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "Error: Could not resolve sprint 'current'." in result.stdout
    assert "Tip: set sprints/current (via sprint planning)" in result.stdout
