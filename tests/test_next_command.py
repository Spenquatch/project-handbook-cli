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

    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
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


def test_next_with_no_active_release_or_sprint_suggests_sprint_plan(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "next"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "🧭 NEXT" in result.stdout
    assert "Release:" in result.stdout
    assert "Sprint:" in result.stdout
    assert "ph sprint plan" in result.stdout


def test_next_with_active_sprint_and_incomplete_gate_suggests_completing_gate(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    planned = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert planned.returncode == 0

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "next"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "Active: SPRINT-2099-01-01" in result.stdout
    assert "Complete sprint gate TASK-001" in result.stdout
    assert ".project-handbook/sprints/current/tasks/" in result.stdout
    assert "/validation.md" in result.stdout


def test_next_json_is_machine_readable_and_has_stable_envelope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "next", "--format", "json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["type"] == "ph-next"
    assert parsed["schema_version"] == 1
    assert isinstance(parsed["next_actions"], list)
