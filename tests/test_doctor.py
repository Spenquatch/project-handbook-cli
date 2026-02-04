from __future__ import annotations

import subprocess
from pathlib import Path


def _write_valid_config(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def _write_required_assets(ph_root: Path) -> None:
    _write_valid_config(ph_root)
    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")


def test_doctor_ok_exits_zero(tmp_path: Path) -> None:
    _write_required_assets(tmp_path)
    result = subprocess.run(["ph", "doctor", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "PH_ROOT:" in result.stdout


def test_doctor_schema_mismatch_exits_2(tmp_path: Path) -> None:
    config = tmp_path / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 999,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )
    result = subprocess.run(["ph", "doctor", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 2


def test_doctor_missing_assets_exits_3(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    result = subprocess.run(["ph", "doctor", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 3
    assert "missing_paths:" in result.stderr
