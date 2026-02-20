from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ph", "--root", str(cwd), "--no-post-hook", *cmd],
        capture_output=True,
        text=True,
        env=env,
    )


def test_process_refresh_respects_seed_ownership_and_force(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    assert _run(["init"], cwd=tmp_path, env=env).returncode == 0

    template_path = tmp_path / ".project-handbook" / "process" / "sessions" / "templates" / "release-planning.md"
    original = template_path.read_text(encoding="utf-8")
    assert "seed_id:" in original
    assert "seed_hash:" in original

    marker = "\n\n<!-- local-modification -->\n"
    template_path.write_text(original + marker, encoding="utf-8")

    # Default refresh must NOT overwrite modified seed-owned files.
    refreshed = _run(["process", "refresh", "--templates"], cwd=tmp_path, env=env)
    assert refreshed.returncode == 0
    assert template_path.read_text(encoding="utf-8").endswith(marker)

    # Force refresh must overwrite.
    forced = _run(["process", "refresh", "--templates", "--force"], cwd=tmp_path, env=env)
    assert forced.returncode == 0
    assert "<!-- local-modification -->" not in template_path.read_text(encoding="utf-8")


def test_process_refresh_disable_system_scope_enforcement_updates_rules_and_deletes_config(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    assert _run(["init"], cwd=tmp_path, env=env).returncode == 0

    rules_path = tmp_path / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules_path.write_text(
        __import__("json").dumps(
            {
                "system_scope_enforcement": {
                    "enabled": True,
                    "config_path": "process/automation/system_scope_config.json",
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    config_path = tmp_path / ".project-handbook" / "process" / "automation" / "system_scope_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('{"schema_version": 1, "routing_rules": {}}', encoding="utf-8")
    assert config_path.exists()

    refreshed = _run(
        ["process", "refresh", "--templates", "--disable-system-scope-enforcement"],
        cwd=tmp_path,
        env=env,
    )
    assert refreshed.returncode == 0

    rules = __import__("json").loads(rules_path.read_text(encoding="utf-8"))
    assert rules.get("system_scope_enforcement", {}).get("enabled") is False
    assert not config_path.exists()


def test_process_refresh_migrate_tasks_drop_session(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    assert _run(["init"], cwd=tmp_path, env=env).returncode == 0

    ph_data_root = tmp_path / ".project-handbook"
    sprint_id = "SPRINT-SEQ-0001"
    sprint_dir = ph_data_root / "sprints" / "SEQ" / sprint_id
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # Set current sprint (process_refresh migration resolves .project-handbook/sprints/current).
    current_link = ph_data_root / "sprints" / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(sprint_dir, target_is_directory=True)

    # 1) Legacy task.yaml: session-only (mappable) -> infer task_type and drop session.
    task1 = tasks_dir / "TASK-001-legacy"
    task1.mkdir(parents=True, exist_ok=True)
    (task1 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Legacy task",
                "feature: f",
                "decision: ADR-0001",
                "owner: @a",
                "status: todo",
                "story_points: 1",
                "session: task-execution",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (task1 / "README.md").write_text(
        "\n".join(
            [
                "---",
                "task_id: TASK-001",
                "session: task-execution",
                "---",
                "",
                "# TASK-001",
                "",
                "**Session**: task-execution",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # 2) Modern task.yaml: task_type + deprecated session -> drop session.
    task2 = tasks_dir / "TASK-002-modern"
    task2.mkdir(parents=True, exist_ok=True)
    (task2 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Modern task",
                "feature: f",
                "decision: ADR-0002",
                "owner: @a",
                "status: todo",
                "story_points: 1",
                "task_type: implementation",
                "session: task-execution",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # 3) Unmappable legacy session should not be deleted (avoid data loss).
    task3 = tasks_dir / "TASK-003-unmappable"
    task3.mkdir(parents=True, exist_ok=True)
    (task3 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-003",
                "title: Unmappable session task",
                "feature: f",
                "decision: ADR-0003",
                "owner: @a",
                "status: todo",
                "story_points: 1",
                "session: custom-session",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    refreshed = _run(["process", "refresh", "--migrate-tasks-drop-session"], cwd=tmp_path, env=env)
    assert refreshed.returncode == 0, refreshed.stdout
    assert "Task migration complete (drop deprecated `session:`)" in refreshed.stdout
    assert "Unmappable session values encountered" in refreshed.stdout
    assert "custom-session" in refreshed.stdout

    # Task 1: inferred type inserted, session removed.
    task1_yaml = (task1 / "task.yaml").read_text(encoding="utf-8")
    assert "session:" not in task1_yaml
    assert "task_type: implementation" in task1_yaml
    task1_readme = (task1 / "README.md").read_text(encoding="utf-8")
    assert "session:" not in task1_readme
    assert "**Session**:" not in task1_readme

    # Task 2: session removed, task_type preserved.
    task2_yaml = (task2 / "task.yaml").read_text(encoding="utf-8")
    assert "session:" not in task2_yaml
    assert "task_type: implementation" in task2_yaml

    # Task 3: session preserved (unmappable) and task_type not injected.
    task3_yaml = (task3 / "task.yaml").read_text(encoding="utf-8")
    assert "session: custom-session" in task3_yaml
    assert "task_type:" not in task3_yaml
