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

    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
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


def test_backlog_triage_generates_then_displays_p0(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    issue_id = "BUG-P0-20990101-090000"

    add = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "backlog",
            "add",
            "--type",
            "bug",
            "--title",
            "T",
            "--severity",
            "P0",
            "--desc",
            "D",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add.returncode == 0

    triage_path = tmp_path / "backlog" / "bugs" / issue_id / "triage.md"
    assert triage_path.exists()
    triage_path.unlink()

    first = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "triage", "--issue", issue_id],
        capture_output=True,
        text=True,
        env=env,
    )
    assert first.returncode == 0
    assert f"No triage analysis found for {issue_id}" in first.stdout
    assert "Generating triage template..." in first.stdout
    assert f"✅ Generated triage template: backlog/bugs/{issue_id}/triage.md" in first.stdout
    assert triage_path.exists()

    second = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "triage", "--issue", issue_id],
        capture_output=True,
        text=True,
        env=env,
    )
    assert second.returncode == 0
    assert f"🎯 TRIAGE ANALYSIS: {issue_id}" in second.stdout
    assert "P0 Triage Analysis:" in second.stdout


def test_backlog_triage_not_found_system_scope_prints_exact_message(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    issue_id = "BUG-P9-00000000-000000"
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "backlog",
            "triage",
            "--issue",
            issue_id,
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout == f"Error: Issue '{issue_id}' not found\n"
