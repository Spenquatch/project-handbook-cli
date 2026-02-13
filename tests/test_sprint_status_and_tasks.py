from __future__ import annotations

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

    ph_data_root = config.parent
    (ph_data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_data_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_data_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _seed_sprint_with_task(*, ph_root: Path, scope: str) -> None:
    cmd = ["ph", "--root", str(ph_root)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert res.returncode == 0

    base = (ph_root / ".project-handbook") if scope == "project" else (ph_root / ".project-handbook" / "system")
    task_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks" / "TASK-001-test"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Test task",
                "feature: feat-a",
                "decision: ADR-001",
                "owner: @owner",
                "status: doing",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "prio: P2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_sprint_status_and_tasks_non_empty_project_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_sprint_with_task(ph_root=tmp_path, scope="project")

    tasks = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "tasks"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert tasks.returncode == 0
    assert tasks.stdout.strip()

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert status.stdout.strip()


def test_sprint_status_project_scope_includes_make_preamble_and_tip(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )
    _seed_sprint_with_task(ph_root=tmp_path, scope="project")

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert status.stdout.startswith(f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph sprint status\n\n")
    assert (
        "Tip: use `ph onboarding session task-execution` (alias: `implement`) for detailed hand-off guidance.\n"
        in status.stdout
    )


def test_sprint_status_and_tasks_non_empty_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_sprint_with_task(ph_root=tmp_path, scope="system")

    tasks = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "sprint", "tasks"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert tasks.returncode == 0
    assert tasks.stdout.strip()

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert status.stdout.strip()


def test_sprint_tasks_project_scope_includes_make_preamble_and_release_tags(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert res.returncode == 0

    task_root = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"
    task_a = task_root / "TASK-001-rel"
    task_a.mkdir(parents=True, exist_ok=True)
    (task_a / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Rel task",
                "lane: ci/evidence",
                "session: task-execution",
                "status: done",
                "story_points: 3",
                "depends_on: [FIRST_TASK]",
                "release: v0.6.0",
                "release_gate: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_b = task_root / "TASK-002-gate"
    task_b.mkdir(parents=True, exist_ok=True)
    (task_b / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Gate task",
                "lane: ci/evidence",
                "session: task-execution",
                "status: done",
                "story_points: 1",
                "depends_on: [TASK-001]",
                "release: null",
                "release_gate: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    tasks = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "tasks"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert tasks.returncode == 0
    assert tasks.stdout == (
        f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph sprint tasks\n\n"
        "📋 SPRINT TASKS: SPRINT-2099-01-01\n" + "=" * 60 + "\n"
        "✅ TASK-001: Rel task  [ci/evidence] (task-execution) [rel:v0.6.0] [3pts] (depends: FIRST_TASK)\n"
        "✅ TASK-002: Gate task  [ci/evidence] (task-execution) [gate] [1pts] (depends: TASK-001)\n"
    )


def test_sprint_status_warns_when_no_sprint_gate_tasks_exist(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_sprint_with_task(ph_root=tmp_path, scope="project")

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert "Sprint gates:\n" in status.stdout
    assert "No sprint gate tasks found (task_type: sprint-gate)." in status.stdout
    assert "Gate-ready: NO\n" in status.stdout


def test_sprint_status_includes_sprint_gate_tasks_and_readiness(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert res.returncode == 0

    task_root = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"

    task_a = task_root / "TASK-001-base"
    task_a.mkdir(parents=True, exist_ok=True)
    (task_a / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Base task",
                "status: done",
                "story_points: 1",
                "depends_on: [FIRST_TASK]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_gate = task_root / "TASK-002-gate"
    task_gate.mkdir(parents=True, exist_ok=True)
    (task_gate / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Sprint gate task",
                "task_type: sprint-gate",
                "status: todo",
                "story_points: 1",
                "depends_on: [TASK-001]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert "Sprint gates:\n" in status.stdout
    assert "Gate-ready: NO (0/1 done)\n" in status.stdout
    assert "- TASK-002: Sprint gate task | status todo | dependency-ready True\n" in status.stdout


def test_sprint_status_gate_ready_yes_when_all_sprint_gates_done(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert res.returncode == 0

    task_root = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"

    base = task_root / "TASK-001-base"
    base.mkdir(parents=True, exist_ok=True)
    (base / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Base task",
                "status: done",
                "story_points: 1",
                "depends_on: [FIRST_TASK]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    gate = task_root / "TASK-002-gate"
    gate.mkdir(parents=True, exist_ok=True)
    (gate / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Sprint gate task",
                "task_type: sprint-gate",
                "status: done",
                "story_points: 1",
                "depends_on: [TASK-001]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "status"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert status.returncode == 0
    assert "Sprint gates:\n" in status.stdout
    assert "Gate-ready: YES (1/1 done)\n" in status.stdout
    assert "- TASK-002: Sprint gate task | status done | dependency-ready True\n" in status.stdout
