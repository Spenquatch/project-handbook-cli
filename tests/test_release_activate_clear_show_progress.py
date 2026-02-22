from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    ph_project_root = ph_root / ".project-handbook"
    config = ph_project_root / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_project_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_release_activate_and_clear(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / ".project-handbook" / "releases" / "v1.0.0").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "activate", "--release", "v1.0.0"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "⭐ Current release set to: v1.0.0" in result.stdout
    assert "💡 Pointer: releases/current.txt" in result.stdout
    assert "📦 RELEASE STATUS: v1.0.0" in result.stdout
    current_link = tmp_path / ".project-handbook" / "releases" / "current"
    assert current_link.is_symlink()
    assert current_link.readlink().name == "v1.0.0"
    current_txt = tmp_path / ".project-handbook" / "releases" / "current.txt"
    assert current_txt.exists()
    assert current_txt.read_text(encoding="utf-8") == "v1.0.0\n"

    result2 = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "clear"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result2.returncode == 0
    assert not current_link.exists()
    assert not current_txt.exists()


def test_release_status_resolves_current_from_current_txt_when_symlink_missing(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / ".project-handbook" / "releases" / "v1.0.0").mkdir(parents=True, exist_ok=True)

    releases_dir = tmp_path / ".project-handbook" / "releases"
    (releases_dir / "current.txt").write_text("v1.0.0\n", encoding="utf-8")
    assert not (releases_dir / "current").exists()

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "📦 RELEASE STATUS: v1.0.0" in result.stdout


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

    progress_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "progress.md"

    result3 = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result3.returncode == 0
    assert "# Release v1.2.3" in result3.stdout
    assert "📦 RELEASE STATUS: v1.2.3" in result3.stdout
    assert progress_path.exists()
    assert "type: release-progress" in progress_path.read_text(encoding="utf-8")


def test_release_show_and_progress_accept_explicit_release_without_current(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    planned = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "plan", "--version", "v1.2.3", "--sprints", "1"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert planned.returncode == 0
    assert not (tmp_path / ".project-handbook" / "releases" / "current").exists()

    shown = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "show", "--release", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert shown.returncode == 0
    assert "📘 RELEASE PLAN: v1.2.3" in shown.stdout
    assert "📦 RELEASE STATUS: v1.2.3" in shown.stdout
    assert (tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "progress.md").exists()
