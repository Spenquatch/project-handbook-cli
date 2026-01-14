from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


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
        json.dumps({"routing_rules": {}}), encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


@pytest.mark.parametrize("scope", ["project", "system"])
def test_feature_status_updates_stage_and_date(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    create_env = dict(os.environ)
    create_env["PH_FAKE_TODAY"] = "2099-01-02"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "create", "--name", "feat-a"]
    created = subprocess.run(cmd, capture_output=True, text=True, env=create_env)
    assert created.returncode == 0

    status_env = dict(os.environ)
    status_env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "status", "--name", "feat-a", "--stage", "developing"]
    updated = subprocess.run(cmd, capture_output=True, text=True, env=status_env)
    assert updated.returncode == 0
    assert updated.stdout.strip() == "✅ Updated 'feat-a' stage to 'developing'"

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    status_md = (base / "features" / "feat-a" / "status.md").read_text(encoding="utf-8")
    assert "Stage: developing" in status_md
    assert "date: 2099-01-01" in status_md


@pytest.mark.parametrize("scope", ["project", "system"])
def test_feature_status_not_found(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "status", "--name", "missing", "--stage", "developing"]
    missing = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert missing.returncode == 1
    assert missing.stdout.strip() == "❌ Feature 'missing' not found"
