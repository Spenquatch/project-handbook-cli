from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_ph_root_for_reset_smoke(ph_root: Path) -> None:
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
            ".project-handbook/process/sessions/logs/.gitkeep",
            ".project-handbook/sprints/archive/.gitkeep",
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
    spec_path = ph_project_root / "process" / "automation" / "reset_spec.json"
    spec_path.write_text(json.dumps(reset_spec, indent=2) + "\n", encoding="utf-8")


def test_reset_smoke_creates_system_artifacts_wipes_project_and_validates(tmp_path: Path) -> None:
    _write_ph_root_for_reset_smoke(tmp_path)

    history = tmp_path / ".project-handbook" / "history.log"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text("sentinel\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "reset-smoke"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Running reset smoke verification: docs/RESET_SMOKE.md" in result.stdout
    assert "✅ reset-smoke complete (project scope wiped; system scope preserved)." in result.stdout

    project_root = tmp_path / ".project-handbook"
    assert not (project_root / "features" / "reset-smoke-project").exists()
    assert not (project_root / "sprints" / "2099" / "SPRINT-2099-01-02").exists()
    assert (project_root / "sprints" / "2099" / "SPRINT-2099-01-03").exists()
    current = project_root / "sprints" / "current"
    assert current.exists()
    assert current.resolve() == (project_root / "sprints" / "2099" / "SPRINT-2099-01-03").resolve()

    assert (tmp_path / ".project-handbook" / "system" / "features" / "handbook-reset-smoke").exists()
    assert (tmp_path / ".project-handbook" / "system" / "sprints" / "2099" / "SPRINT-2099-01-01").exists()

    report = project_root / "status" / "validation.json"
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data.get("issues") == []

    assert not history.exists()


def test_reset_smoke_include_system_wipes_both_scopes(tmp_path: Path) -> None:
    _write_ph_root_for_reset_smoke(tmp_path)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "reset-smoke", "--include-system"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "✅ reset-smoke complete (project + system scopes wiped)." in result.stdout

    project_root = tmp_path / ".project-handbook"
    assert not (project_root / "features" / "reset-smoke-project").exists()
    assert not (project_root / "sprints" / "2099" / "SPRINT-2099-01-02").exists()
    assert (project_root / "sprints" / "2099" / "SPRINT-2099-01-03").exists()

    assert not (tmp_path / ".project-handbook" / "system").exists()
