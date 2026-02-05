from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )

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


def _seed_backlog_items(ph_root: Path, *, count: int) -> None:
    backlog_dir = ph_root / "backlog" / "bugs"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        issue_id = f"BUG-P4-20000101-0000{i:02d}"
        issue_dir = backlog_dir / issue_id
        issue_dir.mkdir(parents=True, exist_ok=True)
        (issue_dir / "README.md").write_text(
            "\n".join(
                [
                    "---",
                    f"title: Seed {i}",
                    "type: bugs",
                    "input_type: bug",
                    "severity: P4",
                    "status: open",
                    "created: 2000-01-01",
                    "owner: unassigned",
                    "---",
                    "",
                    f"# ⚪ [P4] Seed {i}",
                    "",
                ]
            ),
            encoding="utf-8",
        )


@pytest.mark.parametrize("scope", ["project", "system"])
def test_backlog_add_creates_issue_updates_index_and_prints_hint_block(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    if scope == "project":
        _seed_backlog_items(tmp_path, count=24)

    expected_id = "BUG-P2-20990101-090000"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += [
        "--no-post-hook",
        "backlog",
        "add",
        "--type",
        "bugs",
        "--title",
        "Parity backlog issue",
        "--severity",
        "P2",
        "--desc",
        "Created for V1P-0031",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    issue_dir = base / "backlog" / "bugs" / expected_id
    assert issue_dir.exists()
    readme = (issue_dir / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("---")
    assert "input_type: bug" in readme
    assert "created: 2099-01-01" in readme

    index_path = base / "backlog" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert expected_id in index["by_category"]["bugs"]
    assert any(item.get("id") == expected_id for item in index["items"])
    entry = next(item for item in index["items"] if item.get("id") == expected_id)
    assert entry["input_type"] == "bug"
    assert entry["created"] == "2099-01-01"

    hint_lines = [
        "Backlog entry created.",
        "  - Run 'make backlog-triage issue=<ID>' for P0 analysis",
        "  - Assign it into a sprint via 'make backlog-assign issue=<ID> sprint=current'",
        "  - Re-run 'make validate-quick' if files were edited manually",
    ]
    if scope == "project":
        expected_root = str(tmp_path.resolve())
        expected_make_line = (
            "> make -- backlog-add type\\=bug 'title=Parity backlog issue' "
            "severity\\=P2 'desc=Created for V1P-0031'"
        )
        expected_stdout = "\n".join(
            [
                "",
                f"> project-handbook@0.0.0 make {expected_root}",
                expected_make_line,
                "",
                f"✅ Created backlog issue: {expected_id}",
                "   Severity: 🟡 P2 - Medium",
                f"   Location: backlog/bugs/{expected_id}",
                "📊 Updated backlog index: 25 items",
                *hint_lines,
                "",
            ]
        )
        assert result.stdout == expected_stdout
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
