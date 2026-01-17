from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path, *, routing_rules: dict | None = None) -> None:
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
    system_scope_config = {"routing_rules": routing_rules or {}}
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        __import__("json").dumps(system_scope_config), encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _plan_sprint(*, ph_root: Path, scope: str) -> None:
    cmd = ["ph", "--root", str(ph_root)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0


@pytest.mark.parametrize(
    ("scope", "hint_lines"),
    [
        (
            "project",
            [
                "Next steps:",
                "  - Open sprints/current/tasks/ for the new directory, update steps.md + commands.md",
                "  - Set status to 'doing' when work starts and log progress in checklist.md",
                "  - Run 'ph validate --quick' once initial scaffolding is filled in",
            ],
        ),
        (
            "system",
            [
                "Next steps:",
                "  - Open .project-handbook/system/sprints/current/tasks/ for the new directory, "
                "update steps.md + commands.md",
                "  - Set status to 'doing' when work starts and log progress in checklist.md",
                "  - Run 'ph --scope system validate --quick' once initial scaffolding is filled in",
            ],
        ),
    ],
)
def test_task_create_creates_expected_files_and_prints_hint_block(
    tmp_path: Path, scope: str, hint_lines: list[str]
) -> None:
    _write_minimal_ph_root(tmp_path)
    _plan_sprint(ph_root=tmp_path, scope=scope)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += [
        "--no-post-hook",
        "task",
        "create",
        "--title",
        "T",
        "--feature",
        "f",
        "--decision",
        "ADR-0000",
        "--points",
        "5",
        "--owner",
        "@a",
        "--prio",
        "P1",
        "--lane",
        "ops",
        "--session",
        "task-execution",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0
    assert result.stdout.splitlines()[-4:] == hint_lines

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    tasks_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"
    task_dirs = [p for p in tasks_dir.iterdir() if p.is_dir()]
    assert len(task_dirs) == 1
    assert task_dirs[0].name.startswith("TASK-001-")

    expected = {
        "source",
        "task.yaml",
        "README.md",
        "steps.md",
        "commands.md",
        "checklist.md",
        "validation.md",
        "references.md",
    }
    assert expected.issubset({p.name for p in task_dirs[0].iterdir()})

    task_yaml = (task_dirs[0] / "task.yaml").read_text(encoding="utf-8")
    assert "id: TASK-001" in task_yaml
    assert "status: todo" in task_yaml


def test_task_create_guardrail_rejects_system_scoped_lanes_in_project_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path, routing_rules={"task_lane_prefixes_for_system_scope": ["handbook/"]})
    _plan_sprint(ph_root=tmp_path, scope="project")

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "task",
        "create",
        "--title",
        "T",
        "--feature",
        "f",
        "--decision",
        "ADR-0000",
        "--lane",
        "handbook/automation",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 1
    assert result.stdout.strip() == "Use: ph --scope system task create ..."

    tasks_dir = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"
    assert not any(p.is_dir() for p in tasks_dir.iterdir())
