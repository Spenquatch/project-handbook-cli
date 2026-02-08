from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_init_creates_root_marker_and_is_idempotent(tmp_path: Path) -> None:
    result = subprocess.run(
        ["ph", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "Created: .project-handbook/config.json"

    marker = tmp_path / ".project-handbook" / "config.json"
    assert marker.exists()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data == {
        "handbook_schema_version": 1,
        "requires_ph_version": ">=0.0.1,<0.1.0",
        "repo_root": ".",
    }

    data_root = tmp_path / ".project-handbook"

    assert (data_root / "process" / "checks" / "validation_rules.json").exists()
    assert (data_root / "process" / "automation" / "system_scope_config.json").exists()
    assert (data_root / "process" / "automation" / "reset_spec.json").exists()
    assert (data_root / "process" / "sessions" / "templates").exists()
    assert (data_root / "process" / "sessions" / "templates" / "sprint-planning.md").exists()
    assert (data_root / "process" / "playbooks").exists()
    assert (data_root / "process" / "AI_AGENT_START_HERE.md").exists()
    assert (data_root / "process" / "sessions" / "logs" / "latest_summary.md").exists()
    assert (data_root / "process" / "sessions" / "session_end" / "session_end_index.json").exists()
    assert (data_root / "ONBOARDING.md").exists()

    assert (data_root / ".gitkeep").exists()
    assert (data_root / "adr").exists()
    assert (data_root / "assets" / ".gitkeep").exists()
    assert (data_root / "backlog" / "bugs").exists()
    assert (data_root / "backlog" / "index.json").exists()
    assert (data_root / "features" / "implemented").exists()
    assert (data_root / "releases").exists()
    assert (data_root / "roadmap" / "now-next-later.md").exists()
    assert (data_root / "sprints" / "archive").exists()
    assert (data_root / "sprints" / "archive" / "index.json").exists()
    assert (data_root / "status" / "daily").exists()
    assert (data_root / "parking-lot" / "index.json").exists()
    assert (data_root / "docs" / "logs" / ".gitkeep").exists()
    assert (data_root / "tools" / ".gitkeep").exists()

    gitignore_path = tmp_path / ".gitignore"
    assert gitignore_path.exists()
    gitignore_text = gitignore_path.read_text(encoding="utf-8")
    assert ".project-handbook/history.log" in gitignore_text

    result2 = subprocess.run(
        ["ph", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0
    assert result2.stdout.strip() == "Already exists: .project-handbook/config.json"


def test_init_uses_root_override(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / "target"
    target.mkdir()

    result = subprocess.run(
        ["ph", "--root", str(target), "init"],
        cwd=outside,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (target / ".project-handbook" / "config.json").exists()


def test_init_no_gitignore_flag_does_not_write_gitignore(tmp_path: Path) -> None:
    result = subprocess.run(
        ["ph", "init", "--no-gitignore"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert not (tmp_path / ".gitignore").exists()
