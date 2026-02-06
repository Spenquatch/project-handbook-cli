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


def test_backlog_assign_stdout_matches_legacy_make_preamble_and_next_steps_v1p0034(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    sprint_dir = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01"
    sprint_dir.mkdir(parents=True, exist_ok=True)

    current_link = tmp_path / "sprints" / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to("2099/SPRINT-2099-01-01")

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-02T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-02"

    issue_id = "BUG-P2-20990102-090000"

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
            "Parity assign issue",
            "--severity",
            "P2",
            "--desc",
            "Seed for V1P-0034",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add.returncode == 0

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "backlog",
            "assign",
            "--issue",
            issue_id,
            "--sprint",
            "current",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    expected_root = tmp_path.resolve()
    expected = (
        f"\n> project-handbook@0.0.0 ph {expected_root}\n"
        f"> ph backlog assign --issue {issue_id} --sprint current\n\n"
        "📊 Updated backlog index: 1 items\n\n"
        f"Assigning {issue_id} to sprint SPRINT-2099-01-01\n"
        "Severity: P2\n"
        "Title: Parity assign issue\n"
        "📊 Updated backlog index: 1 items\n\n"
        f"✅ Recorded assignment: {issue_id} → SPRINT-2099-01-01\n"
        "Next steps:\n"
        "1. Create/assign the actual sprint task via 'ph task create ...' (feature + decision required; "
        "discovery tasks may use --session research-discovery --decision DR-XXXX).\n"
        "2. If needed, update the sprint plan lanes/integration tasks to reflect the new work.\n"
    )
    assert result.stdout == expected
