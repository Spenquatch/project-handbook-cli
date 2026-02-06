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

    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
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


def test_backlog_triage_existing_issue_stdout_matches_legacy_make_preamble_v1p0033(tmp_path: Path) -> None:
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
            "Parity P0 issue",
            "--severity",
            "P0",
            "--desc",
            "Seed for V1P-0033",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add.returncode == 0

    triage_path = tmp_path / "backlog" / "bugs" / issue_id / "triage.md"
    assert triage_path.exists()
    triage_content = triage_path.read_text(encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "triage", "--issue", issue_id],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    expected_root = tmp_path.resolve()
    expected = (
        f"\n> project-handbook@0.0.0 ph {expected_root}\n"
        f"> ph backlog triage --issue {issue_id}\n\n"
        "📊 Updated backlog index: 1 items\n\n"
        f"🎯 TRIAGE ANALYSIS: {issue_id}\n"
        f"{'=' * 80}\n"
        f"{triage_content}\n"
    )
    assert result.stdout == expected
