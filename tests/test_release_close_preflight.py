from __future__ import annotations

import os
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


def test_release_close_blocks_on_incomplete_timeline_sprint_ids(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
            "--start-sprint",
            "SPRINT-2099-01-01",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0

    # Archive only the first planned sprint; the second remains unarchived.
    (tmp_path / ".project-handbook" / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01").mkdir(
        parents=True, exist_ok=True
    )

    close = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "close", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert close.returncode == 1
    assert close.stderr == (
        "\n".join(
            [
                "❌ Release close blocked: preflight failed.",
                "Release: v1.2.3",
                "",
                "Timeline blockers:",
                "- Mode: sprint_ids",
                "- Unarchived sprint(s): SPRINT-2099-01-08",
                "",
                "Next commands:",
                "- ph release status --release v1.2.3",
                "- ph sprint close --sprint SPRINT-2099-01-08",
                "- Re-run: ph release close --version v1.2.3",
            ]
        )
        + "\n"
    )


def test_release_close_blocks_on_unassigned_slot_sprint_slots(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0

    # Assign Slot 1 to an archived sprint; Slot 2 remains unassigned.
    sprint_dir = tmp_path / ".project-handbook" / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01"
    (sprint_dir / "tasks").mkdir(parents=True, exist_ok=True)
    (sprint_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                "title: Sprint Plan - SPRINT-2099-01-01",
                "type: sprint-plan",
                "date: 2099-01-01",
                "sprint: SPRINT-2099-01-01",
                "mode: bounded",
                "tags: [sprint, planning]",
                "release: v1.2.3",
                "release_sprint_slot: 1",
                "---",
                "",
                "# Sprint Plan: SPRINT-2099-01-01",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    close = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "close", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert close.returncode == 1
    assert close.stderr == (
        "\n".join(
            [
                "❌ Release close blocked: preflight failed.",
                "Release: v1.2.3",
                "",
                "Timeline blockers:",
                "- Mode: sprint_slots",
                "- Unassigned slot(s): 2",
                "",
                "Next commands:",
                "- ph release status --release v1.2.3",
                "- Assign Slot 2: ph sprint plan",
                "  then set in sprints/current/plan.md: release: v1.2.3, release_sprint_slot: 2",
                "- Re-run: ph release close --version v1.2.3",
            ]
        )
        + "\n"
    )


def test_release_close_blocks_on_incomplete_release_gate_task(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "1",
            "--start-sprint",
            "SPRINT-2099-01-01",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0

    sprint_dir = tmp_path / ".project-handbook" / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01"
    task_dir = sprint_dir / "tasks" / "TASK-001-gate"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Gate: ship-check",
                "feature: alpha",
                "status: todo",
                "story_points: 1",
                "release: v1.2.3",
                "release_gate: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    close = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "close", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert close.returncode == 1
    assert close.stderr == (
        "\n".join(
            [
                "❌ Release close blocked: preflight failed.",
                "Release: v1.2.3",
                "",
                "Gate blockers:",
                "- Incomplete release gate task(s): 1",
                "  - TASK-001 (SPRINT-2099-01-01) status=todo dir=TASK-001-gate",
                "",
                "Next commands:",
                "- ph release status --release v1.2.3",
                "- Complete gate task validations + evidence, then mark gate task(s) done in their archived task.yaml",
                "- Re-run: ph release close --version v1.2.3",
            ]
        )
        + "\n"
    )
