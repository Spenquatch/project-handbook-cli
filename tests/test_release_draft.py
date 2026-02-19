from __future__ import annotations

import json
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


def test_release_draft_json_is_stable_and_local_only(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    feat_a = tmp_path / ".project-handbook" / "features" / "feat-a"
    feat_b = tmp_path / ".project-handbook" / "features" / "feat-b"
    feat_a.mkdir(parents=True, exist_ok=True)
    feat_b.mkdir(parents=True, exist_ok=True)
    (feat_a / "status.md").write_text("Stage: developing\n", encoding="utf-8")
    (feat_b / "status.md").write_text("Stage: proposed\n", encoding="utf-8")

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "draft",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["type"] == "release-draft"
    assert payload["schema_version"] == 1
    assert payload["version"] == "v1.2.3"
    assert payload["planned_sprints"] == 2
    assert any(c.get("feature") == "feat-a" for c in payload.get("candidate_features", []))
    assert any(c.get("feature") == "feat-b" for c in payload.get("candidate_features", []))
    assert any("ph release add-feature" in cmd for cmd in payload.get("commands", {}).get("release_add_feature", []))


def test_release_draft_schema_is_valid_json_and_has_expected_properties(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "draft", "--schema"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    schema = json.loads(result.stdout)
    props = schema.get("properties", {})
    assert "type" in props
    assert "schema_version" in props
    assert "candidate_features" in props
    assert "suggested_features" in props
    assert "operator_questions" in props
    assert "commands" in props
