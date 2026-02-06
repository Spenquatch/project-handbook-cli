from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
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


def test_parking_add_stdout_matches_legacy_make_v1p0037(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "parking",
            "add",
            "--type",
            "technical-debt",
            "--title",
            "Parity parking item",
            "--desc",
            "Created for V1P-0037",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    expected_root = tmp_path.resolve()
    expected_id = "DEBT-20990101-parity-parking-item"
    expected = (
        f"\n> project-handbook@0.0.0 make {expected_root}\n"
        "> make -- parking-add type\\=technical-debt 'title=Parity parking item' 'desc=Created for V1P-0037'\n\n"
        f"✅ Created parking lot item: {expected_id}\n"
        f"   Location: parking-lot/technical-debt/{expected_id}\n"
        "📊 Updated parking lot index: 1 items\n"
        "Parking lot updated → review via 'make parking-list' or 'make parking-review'\n"
        "  - Capture owner/priority inside parking-lot/technical-debt/ entries if missing\n"
        "  - Promote items with 'make parking-promote' once they graduate to roadmap\n"
    )
    assert result.stdout == expected

    readme = tmp_path / "parking-lot" / "technical-debt" / expected_id / "README.md"
    assert readme.exists()

    index_path = tmp_path / "parking-lot" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert expected_id in index["by_category"]["technical-debt"]
    assert any(item.get("id") == expected_id for item in index["items"])

