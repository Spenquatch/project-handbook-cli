from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
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
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_release_plan_creates_files_symlink_and_hints(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
            "--start-sprint",
            "SPRINT-2099-01-01",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    plan_path = tmp_path / "releases" / "v1.2.3" / "plan.md"
    progress_path = tmp_path / "releases" / "v1.2.3" / "progress.md"
    features_path = tmp_path / "releases" / "v1.2.3" / "features.yaml"
    assert plan_path.exists()
    assert progress_path.exists()
    assert features_path.exists()

    current_link = tmp_path / "releases" / "current"
    assert current_link.is_symlink()
    assert current_link.readlink().name == "v1.2.3"

    plan_text = plan_path.read_text(encoding="utf-8")
    assert "date: 2099-01-01" in plan_text

    expected_hints = [
        "Release plan saved under releases/current/plan.md",
        "  - Review lanes/dependencies + feature priorities in releases/current/plan.md",
        "  - Confirm sprint alignment via 'ph release status'",
        "  - Run 'ph validate --quick' before sharing externally",
    ]
    for line in expected_hints:
        assert line in result.stdout


def test_release_plan_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "release", "plan"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Releases are project-scope only. Use: ph --scope project release ..."
