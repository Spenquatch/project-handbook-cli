from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
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


def _write_status_stub(*, ph_root: Path, feature: str) -> None:
    feature_dir = ph_root / "features" / feature
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "status.md").write_text(
        "\n".join(
            [
                "---",
                f"title: {feature} Status",
                "type: status",
                f"feature: {feature}",
                "date: 2099-01-01",
                "tags: [status]",
                "links: []",
                "---",
                "",
                f"# Status: {feature}",
                "",
                "Stage: proposed",
                "",
                "## Manual Notes",
                "- Keep this section",
                "",
                "## Active Work (auto-generated)",
                "*Last updated: 2000-01-01*",
                "",
                "- old auto content",
                "",
            ]
        )
        + "\n",
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


def test_feature_update_status_preamble_and_estimated_completion_strings(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)

    _write_status_stub(ph_root=tmp_path, feature="feat-complete")
    _write_status_stub(ph_root=tmp_path, feature="feat-remaining")

    sprint_dir = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01"
    (sprint_dir / "tasks").mkdir(parents=True, exist_ok=True)

    sprints_dir = tmp_path / "sprints"
    current_link = sprints_dir / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(sprint_dir.relative_to(sprints_dir))

    _write_task(sprint_dir=sprint_dir, task_id="TASK-001", feature="feat-complete", status="done", story_points=5)
    _write_task(sprint_dir=sprint_dir, task_id="TASK-002", feature="feat-complete", status="done", story_points=3)

    _write_task(sprint_dir=sprint_dir, task_id="TASK-101", feature="feat-remaining", status="done", story_points=10)
    _write_task(sprint_dir=sprint_dir, task_id="TASK-102", feature="feat-remaining", status="todo", story_points=22)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "feature", "update-status"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    lines = result.stdout.splitlines()
    assert lines[0] == ""
    assert lines[1].startswith("> project-handbook@0.0.0 ph ")
    assert lines[2] == "> ph feature update-status"
    assert lines[3] == ""

    status_complete = (tmp_path / "features" / "feat-complete" / "status.md").read_text(encoding="utf-8")
    assert "- **Estimated Completion**: Complete" in status_complete

    status_remaining = (tmp_path / "features" / "feat-remaining" / "status.md").read_text(encoding="utf-8")
    assert "- **Estimated Completion**: ~2 sprint(s)" in status_remaining


def test_feature_update_status_current_sprint_fallback_prefers_recent_plan_md(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_status_stub(ph_root=tmp_path, feature="feat-a")

    sprint_old = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01"
    sprint_new = tmp_path / "sprints" / "2099" / "SPRINT-2099-02-02"
    (sprint_old / "tasks").mkdir(parents=True, exist_ok=True)
    (sprint_new / "tasks").mkdir(parents=True, exist_ok=True)

    (sprint_old / "plan.md").write_text("# old\n", encoding="utf-8")
    (sprint_new / "plan.md").write_text("# new\n", encoding="utf-8")

    old_mtime = 1_000_000_000
    new_mtime = 1_000_000_100
    os.utime(sprint_old / "plan.md", (old_mtime, old_mtime))
    os.utime(sprint_new / "plan.md", (new_mtime, new_mtime))

    _write_task(sprint_dir=sprint_old, task_id="TASK-001", feature="feat-a", status="doing", story_points=3)
    _write_task(sprint_dir=sprint_new, task_id="TASK-002", feature="feat-a", status="doing", story_points=5)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "feature", "update-status"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    status_md = (tmp_path / "features" / "feat-a" / "status.md").read_text(encoding="utf-8")
    assert "### Current Sprint (SPRINT-2099-02-02)" in status_md
