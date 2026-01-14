from __future__ import annotations

import os
import subprocess
from pathlib import Path


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


def _seed_sprint_with_task(*, ph_root: Path, scope: str) -> None:
    cmd = ["ph", "--root", str(ph_root)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert res.returncode == 0

    base = ph_root if scope == "project" else (ph_root / ".project-handbook" / "system")
    task_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks" / "TASK-001-test"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Test task",
                "feature: feat-a",
                "decision: ADR-001",
                "owner: @owner",
                "status: doing",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "prio: P2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_sprint_status_and_tasks_non_empty_project_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_sprint_with_task(ph_root=tmp_path, scope="project")

    tasks = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "tasks"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert tasks.returncode == 0
    assert tasks.stdout.strip()

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert status.stdout.strip()


def test_sprint_status_and_tasks_non_empty_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_sprint_with_task(ph_root=tmp_path, scope="system")

    tasks = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "sprint", "tasks"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert tasks.returncode == 0
    assert tasks.stdout.strip()

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert status.stdout.strip()
