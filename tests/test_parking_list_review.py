from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
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


def test_parking_list_json_table_and_review_outputs(tmp_path: Path) -> None:
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

    list_json_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "parking",
        "list",
        "--format",
        "json",
    ]
    list_json = subprocess.run(list_json_cmd, capture_output=True, text=True, env=env)
    assert list_json.returncode == 0
    parsed = json.loads(list_json.stdout)
    assert parsed["total_items"] == 1

    list_table_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "parking",
        "list",
    ]
    list_table = subprocess.run(list_table_cmd, capture_output=True, text=True, env=env)
    assert list_table.returncode == 0
    assert "📦 PARKING LOT ITEMS" in list_table.stdout
    assert expected_id in list_table.stdout

    review_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "parking",
        "review",
    ]
    review = subprocess.run(review_cmd, capture_output=True, text=True, env=env, input="q\n")
    assert review.returncode == 0
    assert "🔍 PARKING LOT QUARTERLY REVIEW" in review.stdout


def test_parking_list_json_works_in_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

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

    list_json_cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--scope",
        "system",
        "--no-post-hook",
        "parking",
        "list",
        "--format",
        "json",
    ]
    result = subprocess.run(list_json_cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["total_items"] == 1
