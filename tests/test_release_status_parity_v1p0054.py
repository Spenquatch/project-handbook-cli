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


def _write_release_status_fixture(ph_root: Path) -> None:
    version = "v1.2.0"

    releases_dir = ph_root / ".project-handbook" / "releases"
    release_dir = releases_dir / version
    release_dir.mkdir(parents=True, exist_ok=True)
    (releases_dir / "current").symlink_to(version)

    (release_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                "title: Release v1.2.0 Plan",
                "type: release-plan",
                "version: v1.2.0",
                "timeline_mode: sprint_ids",
                "planned_sprints: 2",
                "sprint_ids: [SPRINT-SEQ-0001, SPRINT-SEQ-0002]",
                "status: planned",
                "---",
                "",
                "# Release v1.2.0",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (release_dir / "features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "  feature_one:",
                "    critical_path: true",
                "  feature_two:",
                "    critical_path: false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    sprint_root = ph_root / ".project-handbook" / "sprints" / "2026" / "SPRINT-SEQ-0001"
    tasks_root = sprint_root / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    (ph_root / ".project-handbook" / "sprints" / "current").parent.mkdir(parents=True, exist_ok=True)
    (ph_root / ".project-handbook" / "sprints" / "current").symlink_to(Path("2026") / "SPRINT-SEQ-0001")

    task_1 = tasks_root / "TASK-001-ship-check"
    task_1.mkdir(parents=True, exist_ok=True)
    (task_1 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Gate: ship-check",
                "feature: feature_one",
                "status: done",
                "story_points: 1",
                "release: current",
                "release_gate: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    task_2 = tasks_root / "TASK-002-core"
    task_2.mkdir(parents=True, exist_ok=True)
    (task_2 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Implement: core work",
                "feature: feature_one",
                "status: done",
                "story_points: 2",
                "release: current",
                "",
            ]
        ),
        encoding="utf-8",
    )

    task_3 = tasks_root / "TASK-003-followup"
    task_3.mkdir(parents=True, exist_ok=True)
    (task_3 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-003",
                "title: Implement: followup",
                "feature: feature_two",
                "status: done",
                "story_points: 3",
                "release: current",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_release_status_stdout_parity_v1p0054(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_release_status_fixture(tmp_path)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    expected_lines = [
        "📦 RELEASE STATUS: v1.2.0",
        "=" * 60,
        "Sprint: 1 of 2 (SPRINT-SEQ-0001)",
        "Feature Completion (historical): 100% (2/2 features started)",
        "Target: SPRINT-SEQ-0002",
        "Feature Trajectory (historical): 🟢 GREEN - Ahead of expected completion for Sprint 1",
        "  Expected completion band: 0–50% by end of Sprint 1/2",
        "Release-Tagged Workstream: 100% (6/6 pts) across 3 tasks (2 features)",
        "Release-Tagged Trajectory: 🟢 GREEN - Ahead of expected completion for Sprint 1",
        "  Expected completion band: 0–50% by end of Sprint 1/2",
        "Gate Burn-up: 1/1 complete (in timeline: 1/1)",
        "Release Readiness (gate-first): 🟢 GREEN - Gates complete (Ready to ship)",
        "",
        "🎯 Feature Completion (historical):",
        f"✅ {'feature_one':<20} {100:3d}% complete (Critical Path)",
        f"✅ {'feature_two':<20} {100:3d}% complete",
        "",
        "🏷️ Release-Tagged Tasks:",
        "✅ TASK-001: Gate: ship-check (1pts) [feature_one] SPRINT-SEQ-0001 [gate]",
        "✅ TASK-002: Implement: core work (2pts) [feature_one] SPRINT-SEQ-0001",
        "✅ TASK-003: Implement: followup (3pts) [feature_two] SPRINT-SEQ-0001",
        "",
        "📅 Sprint Breakdown:",
        "🔄 In progress SPRINT-SEQ-0001 (Sprint 1 of 2)",
        "⭕ Planned SPRINT-SEQ-0002 (Sprint 2 of 2)",
    ]
    assert result.stdout == "\n".join(expected_lines) + "\n"
