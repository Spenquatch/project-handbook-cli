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


def _seed_current_sprint_with_tasks(*, ph_root: Path, scope: str) -> None:
    base = ph_root if scope == "project" else (ph_root / ".project-handbook" / "system")
    sprint_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01"
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    sprints_dir = base / "sprints"
    current_link = sprints_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(sprint_dir.relative_to(sprints_dir))

    task1 = tasks_dir / "TASK-001-first"
    task1.mkdir(parents=True, exist_ok=True)
    (task1 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: First task",
                "feature: feat-a",
                "lane: ops",
                "decision: ADR-0001",
                "session: task-execution",
                "owner: @owner",
                "status: doing",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "prio: P2",
                "due: 2099-01-08",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task2 = tasks_dir / "TASK-002-second"
    task2.mkdir(parents=True, exist_ok=True)
    (task2 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Second task",
                "feature: feat-b",
                "decision: ADR-0002",
                "owner: @owner",
                "status: todo",
                "story_points: 5",
                "depends_on: []",
                "prio: P2",
                "due: 2099-01-08",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("scope", ["project", "system"])
def test_task_list_and_show_match_v0_formatting_rules(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_current_sprint_with_tasks(ph_root=tmp_path, scope=scope)

    env = dict(os.environ)
    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "task", "list"]

    listed = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert listed.returncode == 0
    assert listed.stdout.splitlines() == [
        "📋 SPRINT TASKS: SPRINT-2099-01-01",
        "=" * 60,
        "🔄 TASK-001: First task [ops] (task-execution) [3pts] (depends: FIRST_TASK)",
        "⭕ TASK-002: Second task [5pts]",
    ]

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "task", "show", "--id", "TASK-001"]
    shown = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert shown.returncode == 0
    assert shown.stdout.splitlines()[:2] == ["📋 TASK DETAILS: TASK-001", "=" * 50]
    assert any(line.startswith("Title: First task") for line in shown.stdout.splitlines())

    expected_location = (
        ".project-handbook/system/sprints/current/tasks/TASK-001-first"
        if scope == "system"
        else "sprints/current/tasks/TASK-001-first"
    )
    assert f"Location: {expected_location}" in shown.stdout.splitlines()

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "task", "show", "--id", "TASK-999"]
    missing = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert missing.returncode == 1
    assert missing.stdout.strip() == "❌ Task TASK-999 not found"
