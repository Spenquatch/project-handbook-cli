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


def test_release_readiness_is_not_green_when_only_historical_feature_completion_is_100(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    version = "v1.2.0"
    releases_dir = tmp_path / ".project-handbook" / "releases"
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
                "planned_sprints: 1",
                "sprint_ids: [SPRINT-SEQ-0001]",
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
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    sprint_root = tmp_path / ".project-handbook" / "sprints" / "2026" / "SPRINT-SEQ-0001"
    tasks_root = sprint_root / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".project-handbook" / "sprints" / "current").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".project-handbook" / "sprints" / "current").symlink_to(Path("2026") / "SPRINT-SEQ-0001")

    task_dir = tasks_root / "TASK-001-historical"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Done: historical",
                "feature: feature_one",
                "status: done",
                "story_points: 1",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "Feature Completion (historical): 100% (1/1 features started)" in result.stdout
    assert (
        "Release Readiness (gate-first): 🟡 YELLOW - No release-tagged tasks/gates; readiness unknown "
        "(feature completion is historical)" in result.stdout
    )
