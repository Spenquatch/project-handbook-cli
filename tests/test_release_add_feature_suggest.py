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


def test_release_add_feature_updates_yaml_and_suggest_lists_feature(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = subprocess.run(
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
    assert plan.returncode == 0

    feature_dir = tmp_path / "features" / "feat-a"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "status.md").write_text("Stage: developing\n", encoding="utf-8")

    add_feature = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "add-feature",
            "--release",
            "v1.2.3",
            "--feature",
            "feat-a",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add_feature.returncode == 0

    features_yaml = (tmp_path / "releases" / "v1.2.3" / "features.yaml").read_text(encoding="utf-8")
    assert "  feat-a:" in features_yaml
    assert "    type: regular" in features_yaml
    assert "    critical_path: false" in features_yaml

    suggest = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "suggest", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert suggest.returncode == 0
    assert suggest.stdout.splitlines()[0] == "💡 SUGGESTED FEATURES FOR v1.2.3"
    assert "feat-a" in suggest.stdout


def test_release_add_feature_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "release",
            "suggest",
            "--version",
            "v1.2.3",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Releases are project-scope only. Use: ph --scope project release ..."
