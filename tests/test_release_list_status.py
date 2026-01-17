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


def test_release_list_sorts_semver_and_marks_current(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    releases_dir = tmp_path / "releases"
    (releases_dir / "v1.0.0").mkdir(parents=True, exist_ok=True)
    (releases_dir / "v1.2.0").mkdir(parents=True, exist_ok=True)
    (releases_dir / "current").symlink_to("v1.2.0")

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "list"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    lines = [line.rstrip("\n") for line in result.stdout.splitlines() if line.strip()]
    assert lines[0] == "📦 RELEASES"
    assert lines[1] == "  v1.0.0"
    assert lines[2] == "  v1.2.0 (current)"


def test_release_status_fails_when_no_current_release(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    (tmp_path / "releases" / "v1.2.0").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "❌ No current release found" in result.stdout
    assert "ph release plan" in result.stdout


def test_release_commands_reject_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "release", "list"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Releases are project-scope only. Use: ph --scope project release ..."
