from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        json.dumps({"routing_rules": {}}), encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _seed_complete_feature(*, base: Path, name: str, stage: str) -> None:
    feature_dir = base / "features" / name
    (base / "features" / "implemented").mkdir(parents=True, exist_ok=True)
    (feature_dir / "architecture").mkdir(parents=True, exist_ok=True)
    (feature_dir / "implementation").mkdir(parents=True, exist_ok=True)
    (feature_dir / "testing").mkdir(parents=True, exist_ok=True)
    (feature_dir / "fdr").mkdir(parents=True, exist_ok=True)
    (feature_dir / "decision-register").mkdir(parents=True, exist_ok=True)

    (feature_dir / "overview.md").write_text("- Owner: @alice\n", encoding="utf-8")
    (feature_dir / "status.md").write_text(f"Stage: {stage}\n", encoding="utf-8")
    (feature_dir / "changelog.md").write_text("# Changelog\n", encoding="utf-8")
    (feature_dir / "risks.md").write_text("# Risks\n", encoding="utf-8")
    (feature_dir / "architecture" / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    (feature_dir / "implementation" / "IMPLEMENTATION.md").write_text("# Implementation\n", encoding="utf-8")
    (feature_dir / "testing" / "TESTING.md").write_text("# Testing\n", encoding="utf-8")


def _seed_incomplete_feature(*, base: Path, name: str) -> None:
    feature_dir = base / "features" / name
    (base / "features" / "implemented").mkdir(parents=True, exist_ok=True)
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "status.md").write_text("Stage: completed\n", encoding="utf-8")
    (feature_dir / "overview.md").write_text("Brief description\n", encoding="utf-8")


def _archive_cmd(*, ph_root: Path, scope: str, name: str, force: bool) -> list[str]:
    cmd = ["ph", "--root", str(ph_root)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "archive", "--name", name]
    if force:
        cmd.append("--force")
    return cmd


def test_feature_archive_success_moves_directory(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_complete_feature(base=tmp_path, name="feat-archive", stage="completed")

    cmd = _archive_cmd(ph_root=tmp_path, scope="project", name="feat-archive", force=False)
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0

    assert not (tmp_path / "features" / "feat-archive").exists()
    assert (tmp_path / "features" / "implemented" / "feat-archive").exists()


def test_feature_archive_prints_pnpm_make_preamble_when_forced(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )
    _seed_complete_feature(base=tmp_path, name="feat-dev", stage="developing")

    cmd = _archive_cmd(ph_root=tmp_path, scope="project", name="feat-dev", force=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0

    expected_root = str(tmp_path.resolve())
    assert result.stdout.splitlines() == [
        "",
        f"> project-handbook@0.0.0 make {expected_root}",
        "> make -- feature-archive name\\=feat-dev force\\=true",
        "",
        "✅ Completeness check passed (all critical docs present and filled).",
        "📦 Moved feature 'feat-dev' to features/implemented/",
    ]


def test_feature_archive_blocks_on_non_completed_stage(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    feature_dir = tmp_path / "features" / "feat-blocked"
    (tmp_path / "features" / "implemented").mkdir(parents=True, exist_ok=True)
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "status.md").write_text("Stage: developing\n", encoding="utf-8")

    cmd = _archive_cmd(ph_root=tmp_path, scope="project", name="feat-blocked", force=False)
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 1
    assert (
        result.stdout.strip()
        == "❌ Feature 'feat-blocked' must be in a completed stage before archiving (current: developing). "
        "Use --force only with approval."
    )


def test_feature_archive_completeness_checks_block_unless_forced(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _seed_incomplete_feature(base=tmp_path, name="feat-incomplete")

    cmd = _archive_cmd(ph_root=tmp_path, scope="project", name="feat-incomplete", force=False)
    blocked = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert blocked.returncode == 1
    assert "⚠️  Archive blocked: completeness issues detected." in blocked.stdout
    assert "   Missing files:" in blocked.stdout
    assert "   Placeholder text found:" in blocked.stdout
    assert "Resolve these issues or rerun with --force after manual review." in blocked.stdout

    cmd = _archive_cmd(ph_root=tmp_path, scope="project", name="feat-incomplete", force=True)
    forced = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert forced.returncode == 0
    assert (tmp_path / "features" / "implemented" / "feat-incomplete").exists()


@pytest.mark.parametrize("scope", ["system"])
def test_feature_archive_success_system_scope(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)
    base = tmp_path / ".project-handbook" / "system"
    _seed_complete_feature(base=base, name="feat-system", stage="completed")

    cmd = _archive_cmd(ph_root=tmp_path, scope=scope, name="feat-system", force=False)
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0
    assert (base / "features" / "implemented" / "feat-system").exists()
