from __future__ import annotations

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

    ph_data_root = config.parent
    (ph_data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_data_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_data_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_parking_promote_defaults_target_later_and_moves_directory(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    expected_id = "FEAT-20990101-my-idea"

    add_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "parking",
        "add",
        "--type",
        "features",
        "--title",
        "My Idea",
        "--desc",
        "D",
    ]
    add_result = subprocess.run(add_cmd, capture_output=True, text=True, env=env)
    assert add_result.returncode == 0

    promote_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "parking",
        "promote",
        "--item",
        expected_id,
    ]
    result = subprocess.run(promote_cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0
    assert f"✅ Promoted {expected_id} to roadmap/later/" in result.stdout

    assert (tmp_path / ".project-handbook" / "roadmap" / "later" / expected_id).exists()
    assert not (tmp_path / ".project-handbook" / "parking-lot" / "features" / expected_id).exists()


def test_parking_promote_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    expected_id = "FEAT-20990101-my-idea"

    add_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--scope",
        "system",
        "--no-post-hook",
        "parking",
        "add",
        "--type",
        "features",
        "--title",
        "My Idea",
        "--desc",
        "D",
    ]
    add_result = subprocess.run(add_cmd, capture_output=True, text=True, env=env)
    assert add_result.returncode == 0

    promote_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--scope",
        "system",
        "--no-post-hook",
        "parking",
        "promote",
        "--item",
        expected_id,
    ]
    result = subprocess.run(promote_cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 1
    assert (
        result.stdout.strip()
        == "Error: Roadmap is project-scope-only and MUST NOT be created or written in system scope"
    )
