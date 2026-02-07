from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
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


def _seed_current_sprint(*, ph_root: Path, scope: str) -> Path:
    base = ph_root if scope == "project" else (ph_root / ".project-handbook" / "system")
    sprint_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01"
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    sprints_dir = base / "sprints"
    current_link = sprints_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(sprint_dir.relative_to(sprints_dir))
    return tasks_dir


def _write_task(*, tasks_dir: Path, directory: str, content: str) -> None:
    task_dir = tasks_dir / directory
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(content, encoding="utf-8")


def _write_backlog_item(*, base: Path) -> None:
    item_dir = base / "backlog" / "bugs" / "BUG-001"
    item_dir.mkdir(parents=True, exist_ok=True)
    (item_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "title: Bug 1",
                "type: bugs",
                "severity: P2",
                "status: open",
                "created: 2099-01-01",
                "owner: unassigned",
                "---",
                "",
                "# Bug 1",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_parking_item(*, base: Path) -> None:
    item_dir = base / "parking-lot" / "technical-debt" / "DEBT-001"
    item_dir.mkdir(parents=True, exist_ok=True)
    (item_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "title: Debt 1",
                "type: technical-debt",
                "status: parking-lot",
                "created: 2099-01-01",
                "owner: unassigned",
                "tags: []",
                "---",
                "",
                "# Debt 1",
                "",
            ]
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("scope", ["project", "system"])
def test_task_status_dependency_enforcement_and_archiving(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)
    tasks_dir = _seed_current_sprint(ph_root=tmp_path, scope=scope)

    _write_task(
        tasks_dir=tasks_dir,
        directory="TASK-001-first",
        content="\n".join(
            [
                "id: TASK-001",
                "title: First task",
                "feature: feat-a",
                "decision: ADR-0001",
                "owner: @owner",
                "status: todo",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "prio: P2",
                "due: 2099-01-08",
                "links: []",
                "",
            ]
        ),
    )

    _write_task(
        tasks_dir=tasks_dir,
        directory="TASK-002-second",
        content="\n".join(
            [
                "id: TASK-002",
                "title: Second task",
                "feature: feat-b",
                "decision: ADR-0002",
                "owner: @owner",
                "status: todo",
                "story_points: 5",
                "depends_on: [TASK-001]",
                "prio: P2",
                "due: 2099-01-08",
                "links: []",
                "",
            ]
        ),
    )

    env = dict(os.environ)
    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "task", "status", "--id", "TASK-002", "--status", "doing"]
    blocked = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert blocked.returncode == 1
    assert blocked.stdout.splitlines() == [
        "❌ Cannot move TASK-002 to 'doing' because dependencies are still open: TASK-001",
        "   Finish the prerequisite tasks or rerun with --force after explicit user approval.",
    ]

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "task", "status", "--id", "TASK-002", "--status", "doing", "--force"]
    forced = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert forced.returncode == 0
    assert forced.stdout.splitlines()[0] == "⚠️  Forcing status update despite unresolved dependencies: TASK-001"

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    _write_backlog_item(base=base)
    _write_parking_item(base=base)

    task_yaml = tasks_dir / "TASK-001-first" / "task.yaml"
    task_yaml.write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: First task",
                "feature: feat-a",
                "decision: ADR-0001",
                "owner: @owner",
                "status: todo",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "prio: P2",
                "due: 2099-01-08",
                "links:",
                "  - backlog/bugs/BUG-001/README.md",
                "  - parking-lot/technical-debt/DEBT-001/README.md",
                "",
            ]
        ),
        encoding="utf-8",
    )

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "task", "status", "--id", "TASK-001", "--status", "done"]
    done = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert done.returncode == 0

    archived_backlog = base / "backlog" / "archive" / "bugs" / "BUG-001" / "README.md"
    archived_parking = base / "parking-lot" / "archive" / "technical-debt" / "DEBT-001" / "README.md"
    assert archived_backlog.exists()
    assert archived_parking.exists()

    backlog_readme = archived_backlog.read_text(encoding="utf-8")
    assert "archived_by_task: TASK-001" in backlog_readme
    assert "archived_by_sprint: SPRINT-2099-01-01" in backlog_readme

    parking_readme = archived_parking.read_text(encoding="utf-8")
    assert "archived_by_task: TASK-001" in parking_readme
    assert "archived_by_sprint: SPRINT-2099-01-01" in parking_readme


def test_task_status_project_scope_emits_pnpm_make_preamble_when_package_json_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    tasks_dir = _seed_current_sprint(ph_root=tmp_path, scope="project")

    _write_task(
        tasks_dir=tasks_dir,
        directory="TASK-001-first",
        content="\n".join(
            [
                "id: TASK-001",
                "title: First task",
                "feature: feat-a",
                "decision: ADR-0001",
                "owner: @owner",
                "status: todo",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "prio: P2",
                "due: 2099-01-08",
                "links: []",
                "",
            ]
        ),
    )

    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )

    env = dict(os.environ)
    cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "task",
        "status",
        "--id",
        "TASK-001",
        "--status",
        "doing",
    ]
    updated = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert updated.returncode == 0

    root_display = str(tmp_path.resolve())
    expected_prefix = "\n".join(
        [
            "",
            f"> project-handbook@0.0.0 ph {root_display}",
            "> ph task status --id TASK-001 --status doing",
            "",
            "✅ Updated TASK-001 status: doing",
        ]
    )
    assert updated.stdout.startswith(expected_prefix)

    task_yaml = tasks_dir / "TASK-001-first" / "task.yaml"
    assert "status: doing\n" in task_yaml.read_text(encoding="utf-8")

    cmd_force = cmd + ["--force"]
    forced = subprocess.run(cmd_force, capture_output=True, text=True, env=env)
    assert forced.returncode == 0
    expected_force_prefix = "\n".join(
        [
            "",
            f"> project-handbook@0.0.0 ph {root_display}",
            "> ph task status --id TASK-001 --status doing --force",
            "",
            "✅ Updated TASK-001 status: doing",
        ]
    )
    assert forced.stdout.startswith(expected_force_prefix)
