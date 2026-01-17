from __future__ import annotations

import os
import subprocess
from pathlib import Path


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


def test_sprint_plan_creates_skeleton_and_prints_project_hints(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "Sprint scaffold ready:",
        "  1. Edit sprints/current/plan.md with goals, lanes, and integration tasks",
        "  2. Seed tasks via 'ph task create --title ... --feature ... --decision ADR-###'",
        "  3. Re-run 'ph sprint status' to confirm health + next-up ordering",
        "  4. Run 'ph validate --quick' before handing off to another agent",
        "  5. Need facilitation tips? 'ph onboarding session sprint-planning'",
    ]

    sprint_dir = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01"
    assert sprint_dir.exists()
    assert (sprint_dir / "tasks").exists()
    assert (sprint_dir / "plan.md").exists()
    assert (tmp_path / "sprints" / "current").resolve() == sprint_dir.resolve()


def test_sprint_plan_and_open_work_in_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    planned = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "sprint",
            "plan",
            "--sprint",
            "SPRINT-2099-01-02",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert planned.returncode == 0
    assert planned.stdout.splitlines() == [
        "System-scope sprint scaffold ready:",
        "  1. Edit .project-handbook/system/sprints/current/plan.md with goals, lanes, and integration tasks",
        "  2. Seed tasks via 'ph --scope system task create --title ... --feature ... --decision ADR-###'",
        "  3. Re-run 'ph --scope system sprint status' to confirm health + next-up ordering",
        "  4. Run 'ph --scope system validate --quick' before handing off to another agent",
    ]

    sprint_dir = tmp_path / ".project-handbook" / "system" / "sprints" / "2099" / "SPRINT-2099-01-02"
    plan_md = sprint_dir / "plan.md"
    assert plan_md.exists()
    text = plan_md.read_text(encoding="utf-8")
    assert "release: null" in text
    assert "Release Context" not in text

    opened = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "sprint",
            "open",
            "--sprint",
            "SPRINT-2099-01-02",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert opened.returncode == 0
    assert opened.stdout.strip() == "✅ Current sprint set to: SPRINT-2099-01-02"
    assert (tmp_path / ".project-handbook" / "system" / "sprints" / "current").resolve() == sprint_dir.resolve()
