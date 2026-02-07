from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


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
        json.dumps({"routing_rules": {}}), encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _write_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_task(*, sprint_dir: Path, task_id: str, feature: str, status: str, story_points: int) -> None:
    task_dir = sprint_dir / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                f"id: {task_id}",
                f"title: {task_id} title",
                f"feature: {feature}",
                "owner: @owner",
                f"status: {status}",
                f"story_points: {story_points}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_feature_summary_pnpm_make_preamble_and_header(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)

    sprint_dir = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01"
    (sprint_dir / "tasks").mkdir(parents=True, exist_ok=True)

    sprints_dir = tmp_path / "sprints"
    current_link = sprints_dir / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(sprint_dir.relative_to(sprints_dir))

    _write_task(sprint_dir=sprint_dir, task_id="TASK-001", feature="feat-a", status="done", story_points=3)
    _write_task(sprint_dir=sprint_dir, task_id="TASK-002", feature="feat-a", status="doing", story_points=5)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "feature", "summary"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    lines = result.stdout.splitlines()
    assert lines[0] == ""
    assert lines[1] == f"> project-handbook@0.0.0 ph {tmp_path.resolve()}"
    assert lines[2] == "> ph feature summary"
    assert lines[3] == ""
    assert lines[4:6] == ["🎯 FEATURE SUMMARY WITH SPRINT DATA", "=" * 60]

    expected_points = f"{3:3d}/{8:3d} pts"
    assert any("feat-a" in line and expected_points in line and "Current: " in line for line in lines)
