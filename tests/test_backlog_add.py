from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
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


@pytest.mark.parametrize("scope", ["project", "system"])
def test_backlog_add_creates_issue_updates_index_and_prints_hint_block(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    expected_id = "BUG-P1-20990101-090000"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += [
        "--no-post-hook",
        "backlog",
        "add",
        "--type",
        "bug",
        "--title",
        "T",
        "--severity",
        "P1",
        "--desc",
        "D",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    issue_dir = base / "backlog" / "bugs" / expected_id
    assert issue_dir.exists()
    assert (issue_dir / "README.md").read_text(encoding="utf-8").startswith("---")

    index_path = base / "backlog" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert expected_id in index["by_category"]["bugs"]
    assert any(item.get("id") == expected_id for item in index["items"])

    hint_lines = [
        "Backlog entry created.",
        f"  - Run 'ph backlog triage --issue {expected_id}' for P0 analysis",
        f"  - Assign it into a sprint via 'ph backlog assign --issue {expected_id} --sprint current'",
        "  - Re-run 'ph validate --quick' if files were edited manually",
    ]
    if scope == "project":
        assert result.stdout.splitlines()[-4:] == hint_lines
    else:
        assert "Backlog entry created." not in result.stdout


def test_backlog_add_p0_creates_triage_template(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-02T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-02"

    expected_id = "BUG-P0-20990102-090000"

    cmd = [
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
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    triage_path = tmp_path / "backlog" / "bugs" / expected_id / "triage.md"
    assert triage_path.exists()
    assert "P0 Triage Analysis:" in triage_path.read_text(encoding="utf-8")
