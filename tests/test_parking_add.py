from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
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


@pytest.mark.parametrize("scope", ["project", "system"])
def test_parking_add_creates_item_updates_index_and_prints_hint_block(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    expected_id = "FEAT-20990101-my-idea"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += [
        "--no-post-hook",
        "parking",
        "add",
        "--type",
        "features",
        "--title",
        "My Idea",
        "--desc",
        "D",
        "--owner",
        "@a",
        "--tags",
        "foo,bar",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    item_dir = base / "parking-lot" / "features" / expected_id
    assert item_dir.exists()
    assert (item_dir / "README.md").read_text(encoding="utf-8").startswith("---")

    index_path = base / "parking-lot" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert expected_id in index["by_category"]["features"]
    assert any(item.get("id") == expected_id for item in index["items"])

    hint_lines = [
        "Parking lot updated → review via 'ph parking list' or 'ph parking review'",
        "  - Capture owner/priority inside parking-lot/features/ entries if missing",
        "  - Promote items with 'ph parking promote' once they graduate to roadmap",
    ]
    if scope == "project":
        assert result.stdout.splitlines()[-3:] == hint_lines
    else:
        assert hint_lines[0] not in result.stdout
