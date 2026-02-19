from __future__ import annotations

import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    ph_project_root = ph_root / ".project-handbook"
    config = ph_project_root / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_project_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_sprint_plan_autoscaffolds_sprint_gate_and_validates(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "sprint", "plan"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    current_link = tmp_path / ".project-handbook" / "sprints" / "current"
    assert current_link.exists()
    sprint_dir = current_link.resolve()
    tasks_dir = sprint_dir / "tasks"
    assert tasks_dir.exists()

    gate_tasks = []
    for task_dir in tasks_dir.iterdir():
        if not task_dir.is_dir():
            continue
        task_yaml = task_dir / "task.yaml"
        if not task_yaml.exists():
            continue
        if "task_type: sprint-gate" in task_yaml.read_text(encoding="utf-8"):
            gate_tasks.append(task_dir)

    assert gate_tasks, "Expected sprint plan to scaffold at least one sprint-gate task"

    validate = subprocess.run(
        ["ph", "--root", str(tmp_path), "validate", "--quick"],
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0
