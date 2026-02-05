from __future__ import annotations

import os
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


def test_release_clear_stdout_and_removes_current_symlink_matches_legacy(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    (tmp_path / "releases" / "v1.0.0").mkdir(parents=True, exist_ok=True)
    current_link = tmp_path / "releases" / "current"
    current_link.symlink_to("v1.0.0")
    assert current_link.is_symlink()

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "release", "clear"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout == "⭐ Cleared current release\n"
    assert not current_link.exists()
    assert not current_link.is_symlink()


def test_release_clear_no_preconditions_still_prints_legacy_stdout(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "releases").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "release", "clear"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout == "⭐ Cleared current release\n"
    assert not (tmp_path / "releases" / "current").exists()
