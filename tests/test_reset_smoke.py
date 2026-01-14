from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_ph_root_for_reset_smoke(ph_root: Path) -> None:
    config = ph_root / "cli_plan" / "project_handbook.config.json"
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

    reset_spec = {
        "schema_version": 1,
        "forbidden_subtrees": [".project-handbook/system"],
        "delete_contents_roots": [
            "sprints",
            "features",
            "adr",
            "decision-register",
            "backlog",
            "parking-lot",
            "releases",
            "contracts",
            "status",
            "process/sessions/logs",
            "process/sessions/session_end",
        ],
        "delete_paths": [".project-handbook/history.log"],
        "preserve_paths": [
            ".project-handbook/.gitkeep",
            "sprints/archive/.gitkeep",
            "adr/README.md",
            "adr/EXAMPLE-0001-sample-decision.md",
            "decision-register/README.md",
            "releases/CHANGELOG.md",
            "releases/EXAMPLE-v0.1.0.md",
            "status/README.md",
            "process/sessions/logs/.gitkeep",
            "process/sessions/logs/latest_summary.md",
            "process/sessions/session_end/session_end_index.json",
        ],
        "rewrite_paths": [
            "roadmap/now-next-later.md",
            "backlog/index.json",
            "parking-lot/index.json",
            "sprints/archive/index.json",
            "process/sessions/logs/latest_summary.md",
            "process/sessions/session_end/session_end_index.json",
        ],
        "recreate_dirs": [
            ".project-handbook",
            "backlog",
            "parking-lot",
            "process/sessions/logs",
            "process/sessions/session_end",
            "roadmap",
            "sprints/archive",
        ],
        "recreate_files": [
            ".project-handbook/.gitkeep",
            "process/sessions/logs/.gitkeep",
            "sprints/archive/.gitkeep",
        ],
    }
    spec_path = ph_root / "process" / "automation" / "reset_spec.json"
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

    assert not (tmp_path / "features" / "reset-smoke-project").exists()
    assert not (tmp_path / "sprints" / "2099" / "SPRINT-2099-01-02").exists()
    assert (tmp_path / "sprints" / "2099" / "SPRINT-2099-01-03").exists()
    current = tmp_path / "sprints" / "current"
    assert current.exists()
    assert current.resolve() == (tmp_path / "sprints" / "2099" / "SPRINT-2099-01-03").resolve()

    assert (tmp_path / ".project-handbook" / "system" / "features" / "handbook-reset-smoke").exists()
    assert (tmp_path / ".project-handbook" / "system" / "sprints" / "2099" / "SPRINT-2099-01-01").exists()

    report = tmp_path / "status" / "validation.json"
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data.get("issues") == []

    assert not history.exists()
