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

    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "private": true,\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def test_status_writes_outputs_and_prints_expected_format(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2026-01-01T00:00:00Z"

    expected_json = (tmp_path / ".project-handbook" / "status" / "current.json").resolve()
    expected_summary = (tmp_path / ".project-handbook" / "status" / "current_summary.md").resolve()

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert expected_json.exists()
    assert expected_summary.exists()

    expected_preamble = f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph status\n\n"
    assert result.stdout.startswith(expected_preamble)
    assert f"Generated: {expected_json}\n" in result.stdout
    assert f"Updated: {expected_summary}\n" in result.stdout
    assert "\n\n===== status/current_summary.md =====\n\n" in result.stdout
    assert "\n\n====================================\n" in result.stdout
    assert "Updated feature status files\n" in result.stdout


def test_status_writes_outputs_under_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    expected_json = (tmp_path / ".project-handbook" / "system" / "status" / "current.json").resolve()
    expected_summary = (tmp_path / ".project-handbook" / "system" / "status" / "current_summary.md").resolve()

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert expected_json.exists()
    assert expected_summary.exists()


def test_status_supports_sequence_sprint_ids_using_plan_date(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2026-01-03T00:00:00Z"
    env["TZ"] = "UTC"

    sprints_dir = tmp_path / ".project-handbook" / "sprints"
    sprint_dir = sprints_dir / "SEQ" / "SPRINT-SEQ-0001"
    (sprint_dir / "tasks").mkdir(parents=True, exist_ok=True)
    (sprint_dir / "plan.md").write_text(
        "---\n"
        "title: Sprint Plan - SPRINT-SEQ-0001\n"
        "type: sprint-plan\n"
        "date: 2026-01-01\n"
        "sprint: SPRINT-SEQ-0001\n"
        "mode: bounded\n"
        "---\n"
        "\n"
        "# Sprint Plan: SPRINT-SEQ-0001\n",
        encoding="utf-8",
    )
    (sprints_dir / "current").parent.mkdir(parents=True, exist_ok=True)
    (sprints_dir / "current").symlink_to(Path("SEQ/SPRINT-SEQ-0001"))

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "- ID: `SPRINT-SEQ-0001`" in result.stdout
    assert "- Mode: bounded | Age: 2 days (since 2026-01-01)" in result.stdout
