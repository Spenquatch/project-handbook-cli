from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


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
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _write_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_bounded_sprint_config(ph_root: Path) -> None:
    (ph_root / "process" / "checks" / "validation_rules.json").write_text(
        '{\n  "sprint_management": {\n    "mode": "bounded"\n  }\n}\n',
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("scope", "base_rel"),
    [
        ("project", ""),
        ("system", ".project-handbook/system"),
    ],
)
def test_sprint_burndown_writes_burndown_md_under_scope(tmp_path: Path, scope: str, base_rel: str) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    planned = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert planned.returncode == 0

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "burndown"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    base = tmp_path if scope == "project" else (tmp_path / base_rel)
    sprint_dir = base / "sprints" / "2099" / "SPRINT-2099-01-01"
    assert (sprint_dir / "burndown.md").exists()

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "capacity"]
    capacity = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert capacity.returncode == 0
    assert capacity.stdout.strip()


def test_sprint_burndown_stdout_matches_make_preamble_and_spacing(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-02"

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    planned = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert planned.returncode == 0

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "burndown"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    expected_prefix = (
        f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph sprint burndown\n\n"
    )
    assert result.stdout.startswith(expected_prefix)

    saved_path = (tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01" / "burndown.md").resolve()
    assert result.stdout.endswith(f"\n\nSaved to: {saved_path}\n")


def test_sprint_capacity_stdout_matches_make_preamble_and_bounded_output(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)
    _write_bounded_sprint_config(tmp_path)

    (tmp_path / "backlog").mkdir(parents=True, exist_ok=True)
    (tmp_path / "backlog" / "index.json").write_text(
        '{\n  "items": [\n    {"severity": "P0"},\n    {"severity": "P1"},\n    {"severity": "P2"}\n  ]\n}\n',
        encoding="utf-8",
    )

    env = dict(os.environ)
    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    planned = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert planned.returncode == 0

    task_root = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"

    task_1 = task_root / "TASK-001-ci"
    task_1.mkdir(parents=True, exist_ok=True)
    (task_1 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: CI evidence",
                "lane: ci/evidence",
                "status: done",
                "story_points: 5",
                "depends_on: [FIRST_TASK]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_2 = task_root / "TASK-002-inprog"
    task_2.mkdir(parents=True, exist_ok=True)
    (task_2 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                "title: Demo integration",
                "lane: integration/v2-demo",
                "status: doing",
                "story_points: 3",
                "depends_on: [TASK-001]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_3 = task_root / "TASK-003-blocked"
    task_3.mkdir(parents=True, exist_ok=True)
    (task_3 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-003",
                "title: Blocked integration",
                "lane: integration/v2-demo",
                "status: blocked",
                "story_points: 2",
                "depends_on: [TASK-002]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_4 = task_root / "TASK-004-ui"
    task_4.mkdir(parents=True, exist_ok=True)
    (task_4 / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-004",
                "title: UI harness",
                "lane: ui/twenty-harness",
                "status: done",
                "story_points: 1",
                "depends_on: [TASK-001]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "capacity"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    expected = (
        f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph sprint capacity\n\n"
        "\n📊 SPRINT METRICS (BOUNDED)\n"
        + "=" * 80
        + "\n"
        "\n🎯 Sprint: SPRINT-2099-01-01\n"
        + "-" * 40
        + "\n"
        "\nPoints by status (telemetry; not a scope cap):\n"
        "Total Points:      11\n"
        "Completed:         6 (54.5%)\n"
        "In Progress:       3 (27.3%)\n"
        "Blocked:           2 (18.2%)\n"
        "\n🚨 Backlog Pressure (P0/P1 count): 2\n"
        "\n🧵 Lanes:\n"
        f"- {'ci/evidence':24} {5:3d}/{5:3d} pts done (blocked 0)\n"
        f"- {'integration/v2-demo':24} {0:3d}/{5:3d} pts done (blocked 2)\n"
        f"- {'ui/twenty-harness':24} {1:3d}/{1:3d} pts done (blocked 0)\n"
        "\n"
        + "=" * 80
        + "\n"
    )
    assert result.stdout == expected
