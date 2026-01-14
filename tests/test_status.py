from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "cli_plan" / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
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


def test_status_writes_outputs_and_prints_expected_format(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    expected_json = (tmp_path / "status" / "current.json").resolve()
    expected_summary = (tmp_path / "status" / "current_summary.md").resolve()

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert expected_json.exists()
    assert expected_summary.exists()

    assert f"Generated: {expected_json}\n" in result.stdout
    assert f"Updated: {expected_summary}\n" in result.stdout
    assert "\n\n===== status/current_summary.md =====\n\n" in result.stdout
    assert "\n\n====================================\n" in result.stdout


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
