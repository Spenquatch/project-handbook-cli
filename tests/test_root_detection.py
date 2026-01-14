from __future__ import annotations

import subprocess
from pathlib import Path


def _write_marker(ph_root: Path) -> None:
    marker = ph_root / "cli_plan" / "project_handbook.config.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{}", encoding="utf-8")


def test_ph_runs_in_repo_root(tmp_path: Path) -> None:
    _write_marker(tmp_path)
    result = subprocess.run(["ph"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0


def test_ph_runs_from_nested_subdir(tmp_path: Path) -> None:
    _write_marker(tmp_path)
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
    _write_marker(ph_root)

    outside = tmp_path / "outside"
    outside.mkdir()

    result = subprocess.run(["ph", "--root", str(ph_root)], cwd=outside, capture_output=True, text=True)
    assert result.returncode == 0
