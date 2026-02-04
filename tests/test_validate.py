from __future__ import annotations

import subprocess
from pathlib import Path


def _write_basic_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")


def test_validate_project_scope_writes_report_and_silent_success(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "validate", "--quick", "--silent-success", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert (tmp_path / "status" / "validation.json").exists()


def test_validate_system_scope_writes_report_and_silent_success(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "validate", "--quick", "--silent-success", "--scope", "system", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert (tmp_path / ".project-handbook" / "system" / "status" / "validation.json").exists()
