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

    assert (tmp_path / "process" / "checks" / "validation_rules.json").exists()
    assert (tmp_path / "process" / "automation" / "system_scope_config.json").exists()
    assert (tmp_path / "process" / "automation" / "reset_spec.json").exists()
    assert (tmp_path / "process" / "sessions" / "templates").exists()
    assert (tmp_path / "process" / "sessions" / "templates" / "sprint-planning.md").exists()
    assert (tmp_path / "process" / "playbooks").exists()
    assert (tmp_path / "process" / "AI_AGENT_START_HERE.md").exists()
    assert (tmp_path / "process" / "sessions" / "logs" / "latest_summary.md").exists()
    assert (tmp_path / "process" / "sessions" / "session_end" / "session_end_index.json").exists()
    assert (tmp_path / "ONBOARDING.md").exists()

    assert (tmp_path / ".project-handbook" / ".gitkeep").exists()
    assert (tmp_path / "adr").exists()
    assert (tmp_path / "assets" / ".gitkeep").exists()
    assert (tmp_path / "backlog" / "bugs").exists()
    assert (tmp_path / "backlog" / "index.json").exists()
    assert (tmp_path / "features" / "implemented").exists()
    assert (tmp_path / "releases").exists()
    assert (tmp_path / "roadmap" / "now-next-later.md").exists()
    assert (tmp_path / "sprints" / "archive").exists()
    assert (tmp_path / "sprints" / "archive" / "index.json").exists()
    assert (tmp_path / "status" / "daily").exists()
    assert (tmp_path / "parking-lot" / "index.json").exists()
    assert (tmp_path / "docs" / "logs" / ".gitkeep").exists()
    assert (tmp_path / "tools" / ".gitkeep").exists()

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
