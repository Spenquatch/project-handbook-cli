from __future__ import annotations

import subprocess
from pathlib import Path


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


def test_ph_runs_in_repo_root(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0


def test_ph_version_flag_works_outside_repo(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    result = subprocess.run(["ph", "--version"], cwd=outside, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip()


def test_ph_runs_from_nested_subdir(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    result = subprocess.run(["ph"], cwd=nested, capture_output=True, text=True)
    assert result.returncode == 0


def test_ph_fails_outside_repo_with_remediation(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    result = subprocess.run(["ph"], cwd=outside, capture_output=True, text=True)
    assert result.returncode != 0
    assert "ph --root" in result.stderr


def test_root_override_allows_running_outside_repo(tmp_path: Path) -> None:
    ph_root = tmp_path / "handbook"
    ph_root.mkdir()
    _write_minimal_ph_root(ph_root)

    outside = tmp_path / "outside"
    outside.mkdir()

    result = subprocess.run(["ph", "--root", str(ph_root)], cwd=outside, capture_output=True, text=True)
    assert result.returncode == 0
