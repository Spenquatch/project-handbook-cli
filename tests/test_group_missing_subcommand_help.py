from __future__ import annotations

import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def test_group_missing_subcommand_outside_root_shows_overview(tmp_path: Path) -> None:
    result = subprocess.run(["ph", "release"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert "Usage: ph release <subcommand>" in result.stderr
    assert "Subcommands:" in result.stderr
    assert "plan" in result.stderr
    assert "Next commands:" in result.stderr
    assert "No current ph project found" in result.stderr


def test_group_missing_subcommand_inside_root_has_no_root_note(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(["ph", "--root", str(tmp_path), "release"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Usage: ph release <subcommand>" in result.stderr
    assert "Subcommands:" in result.stderr
    assert "Next commands:" in result.stderr
    assert "No current ph project found" not in result.stderr

