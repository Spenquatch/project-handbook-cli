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


def test_release_activate_and_clear(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "releases" / "v1.0.0").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "activate", "--release", "v1.0.0"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    current_link = tmp_path / "releases" / "current"
    assert current_link.is_symlink()
    assert current_link.readlink().name == "v1.0.0"

    result2 = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "clear"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result2.returncode == 0
    assert not current_link.exists()


def test_release_progress_and_show(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "plan", "--version", "v1.2.3", "--activate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    result2 = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "progress"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result2.returncode == 0
    progress_path = tmp_path / "releases" / "v1.2.3" / "progress.md"
    assert progress_path.exists()
    assert "type: release-progress" in progress_path.read_text(encoding="utf-8")

    result3 = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result3.returncode == 0
    assert "# Release v1.2.3" in result3.stdout
    assert "📦 RELEASE STATUS: v1.2.3" in result3.stdout

