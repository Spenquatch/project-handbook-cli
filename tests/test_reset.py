from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    data_root = config.parent
    (data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (data_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )


def _write_reset_spec(ph_root: Path) -> None:
    reset_spec = {
        "schema_version": 1,
        "forbidden_subtrees": [".project-handbook/system"],
        "delete_contents_roots": [
            ".project-handbook/sprints",
            ".project-handbook/features",
            ".project-handbook/adr",
            ".project-handbook/decision-register",
            ".project-handbook/backlog",
            ".project-handbook/parking-lot",
            ".project-handbook/releases",
            ".project-handbook/contracts",
            ".project-handbook/status",
            ".project-handbook/process/sessions/logs",
            ".project-handbook/process/sessions/session_end",
        ],
        "delete_paths": [".project-handbook/history.log"],
        "preserve_paths": [
            ".project-handbook/.gitkeep",
            ".project-handbook/sprints/archive/.gitkeep",
            ".project-handbook/adr/README.md",
            ".project-handbook/adr/EXAMPLE-0001-sample-decision.md",
            ".project-handbook/decision-register/README.md",
            ".project-handbook/releases/CHANGELOG.md",
            ".project-handbook/releases/EXAMPLE-v0.1.0.md",
            ".project-handbook/status/README.md",
            ".project-handbook/process/sessions/logs/.gitkeep",
            ".project-handbook/process/sessions/logs/latest_summary.md",
            ".project-handbook/process/sessions/session_end/session_end_index.json",
        ],
        "rewrite_paths": [
            ".project-handbook/roadmap/now-next-later.md",
            ".project-handbook/backlog/index.json",
            ".project-handbook/parking-lot/index.json",
            ".project-handbook/sprints/archive/index.json",
            ".project-handbook/process/sessions/logs/latest_summary.md",
            ".project-handbook/process/sessions/session_end/session_end_index.json",
        ],
        "recreate_dirs": [
            ".project-handbook",
            ".project-handbook/backlog",
            ".project-handbook/parking-lot",
            ".project-handbook/process/sessions/logs",
            ".project-handbook/process/sessions/session_end",
            ".project-handbook/roadmap",
            ".project-handbook/sprints/archive",
        ],
        "recreate_files": [
            ".project-handbook/.gitkeep",
            ".project-handbook/process/sessions/logs/.gitkeep",
            ".project-handbook/sprints/archive/.gitkeep",
        ],
    }
    spec_path = ph_root / ".project-handbook" / "process" / "automation" / "reset_spec.json"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(reset_spec, indent=2) + "\n", encoding="utf-8")


def _write_project_artifacts(ph_root: Path) -> None:
    data_root = ph_root / ".project-handbook"
    (data_root / "features" / "x").mkdir(parents=True, exist_ok=True)
    (data_root / "features" / "x" / "overview.md").write_text("---\n---\n", encoding="utf-8")

    sprint_dir = data_root / "sprints" / "2099" / "SPRINT-2099-01-01"
    sprint_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")

    current_link = data_root / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    os.symlink(sprint_dir, current_link)

    bug_dir = data_root / "backlog" / "bugs" / "BUG-001"
    bug_dir.mkdir(parents=True, exist_ok=True)
    (bug_dir / "issue.md").write_text("# Bug\n", encoding="utf-8")

    item_dir = data_root / "parking-lot" / "technical-debt" / "PARK-001"
    item_dir.mkdir(parents=True, exist_ok=True)
    (item_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")


def _write_system_artifacts(ph_root: Path) -> Path:
    sys_feature = ph_root / ".project-handbook" / "system" / "features" / "handbook-reset-smoke"
    sys_feature.mkdir(parents=True, exist_ok=True)
    (sys_feature / "overview.md").write_text("---\n---\n", encoding="utf-8")
    return sys_feature


def test_reset_dry_run_is_safe_and_skips_hook(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_reset_spec(tmp_path)

    sys_feature = _write_system_artifacts(tmp_path)
    _write_project_artifacts(tmp_path)

    history = tmp_path / ".project-handbook" / "history.log"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text("sentinel\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "reset"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "project-handbook reset report" in result.stdout
    assert "mode: DRY-RUN" in result.stdout
    assert "To execute: ph reset --confirm RESET --force true" in result.stdout

    data_root = tmp_path / ".project-handbook"
    assert (data_root / "features" / "x").exists()
    assert (data_root / "sprints" / "2099").exists()
    assert (data_root / "backlog" / "bugs" / "BUG-001").exists()
    assert sys_feature.exists()

    assert history.read_text(encoding="utf-8") == "sentinel\n"


def test_reset_execute_deletes_project_preserves_system_rewrites_templates_and_skips_hook(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_reset_spec(tmp_path)

    sys_feature = _write_system_artifacts(tmp_path)
    _write_project_artifacts(tmp_path)

    history = tmp_path / ".project-handbook" / "history.log"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text("sentinel\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "reset", "--confirm", "RESET", "--force", "true"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "mode: EXECUTE" in result.stdout
    assert "✅ Reset complete." in result.stdout

    data_root = tmp_path / ".project-handbook"
    assert not (data_root / "features" / "x").exists()
    assert not (data_root / "sprints" / "2099").exists()
    assert not (data_root / "sprints" / "current").exists()
    assert not (data_root / "backlog" / "bugs" / "BUG-001").exists()
    assert sys_feature.exists()

    assert (data_root / "roadmap" / "now-next-later.md").exists()
    assert (data_root / "backlog" / "index.json").exists()
    assert (data_root / "parking-lot" / "index.json").exists()

    assert not history.exists()
