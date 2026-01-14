from __future__ import annotations

import json
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
        json.dumps({"routing_rules": {}}), encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _seed_feature_and_sprint(*, ph_root: Path, scope: str) -> Path:
    base = ph_root if scope == "project" else (ph_root / ".project-handbook" / "system")

    feature_dir = base / "features" / "feat-a"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "status.md").write_text(
        "\n".join(
            [
                "---",
                "title: Feat A Status",
                "type: status",
                "feature: feat-a",
                "date: 2099-01-01",
                "tags: [status]",
                "links: []",
                "---",
                "",
                "# Status: Feat A",
                "",
                "Stage: proposed",
                "",
                "## Manual Notes",
                "- Keep this section",
                "",
                "## Active Work (auto-generated)",
                "*Last updated: 2000-01-01*",
                "",
                "- old auto content",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sprint_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01"
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    sprints_dir = base / "sprints"
    current_link = sprints_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(sprint_dir.relative_to(sprints_dir))

    task1 = tasks_dir / "TASK-001-done"
    task1.mkdir(parents=True, exist_ok=True)
    (task1 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Done task",
                "feature: feat-a",
                "owner: @owner",
                "status: done",
                "story_points: 3",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task2 = tasks_dir / "TASK-002-doing"
    task2.mkdir(parents=True, exist_ok=True)
    (task2 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Doing task",
                "feature: feat-a",
                "owner: @owner",
                "status: doing",
                "story_points: 5",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return base


@pytest.mark.parametrize("scope", ["project", "system"])
def test_feature_update_status_rewrites_auto_section_and_summary_is_stable(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)
    base = _seed_feature_and_sprint(ph_root=tmp_path, scope=scope)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "update-status"]
    updated = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert updated.returncode == 0

    status_md = (base / "features" / "feat-a" / "status.md").read_text(encoding="utf-8")
    assert "## Active Work (auto-generated)" in status_md
    assert "SPRINT-2099-01-01" in status_md
    assert "TASK-001" in status_md
    assert "TASK-002" in status_md

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "summary"]
    summary = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert summary.returncode == 0

    lines = summary.stdout.splitlines()
    assert lines[:2] == ["🎯 FEATURE SUMMARY WITH SPRINT DATA", "=" * 60]

    expected_points = f"{3:3d}/{8:3d} pts"
    assert any("feat-a" in line and expected_points in line for line in lines)
