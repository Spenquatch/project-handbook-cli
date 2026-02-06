from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    (ph_root / "project_handbook.config.json").write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
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


def _seed_current_sprint(*, ph_root: Path) -> Path:
    sprint_dir = ph_root / "sprints" / "2099" / "SPRINT-2099-01-01"
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    sprints_dir = ph_root / "sprints"
    current_link = sprints_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(sprint_dir.relative_to(sprints_dir))
    return tasks_dir


def test_post_hook_validation_errors_do_not_change_exit_code(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    tasks_dir = _seed_current_sprint(ph_root=tmp_path)

    task_dir = tasks_dir / "TASK-001-first"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: First task",
                "feature: feat-a",
                "decision: ADR-0001",
                "owner: @owner",
                "status: todo",
                "story_points: 3",
                "depends_on: []",
                "prio: P2",
                "due: 2099-01-08",
                "links: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Force quick validation to have at least one error (legacy make still exits 0).
    (tmp_path / "INVALID.md").write_text("# Missing front matter\n", encoding="utf-8")

    env = dict(os.environ)
    cmd = [
        "ph",
        "--root",
        str(tmp_path),
        # Ensure post-hook runs (no --no-post-hook).
        "task",
        "status",
        "--id",
        "TASK-001",
        "--status",
        "doing",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    assert result.returncode == 0
    assert "validation:" in result.stdout
    assert "status/validation.json" in result.stdout
