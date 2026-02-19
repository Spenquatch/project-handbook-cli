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

    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
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


def test_parking_review_stdout_matches_legacy_make_v1p0039(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    desc = "A" * 250
    index = {
        "last_updated": "2099-01-01T09:00:00Z",
        "total_items": 1,
        "by_category": {
            "features": [],
            "technical-debt": ["DEBT-20990102-bar-debt"],
            "research": [],
            "external-requests": [],
        },
        "items": [
            {
                "title": "Bar debt",
                "type": "technical-debt",
                "status": "parking-lot",
                "created": "2099-01-02",
                "owner": "@alice",
                "tags": [],
                "description": desc,
                "id": "DEBT-20990102-bar-debt",
                "path": "parking-lot/technical-debt/DEBT-20990102-bar-debt",
            }
        ],
    }
    parking_lot_dir = tmp_path / ".project-handbook" / "parking-lot"
    parking_lot_dir.mkdir(parents=True, exist_ok=True)
    (parking_lot_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "parking", "review"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    expected_root = tmp_path.resolve()
    expected = (
        f"\n> project-handbook@0.0.0 ph {expected_root}\n"
        "> ph parking review\n\n"
        "\n📦 PARKING LOT REVIEW (NON-INTERACTIVE)\n" + ("=" * 80) + "\n"
        "Total items: 1\n"
        "Last updated: 2099-01-01T09:00:00Z\n"
        "By category:\n"
        "  - features: 0\n"
        "  - technical-debt: 1\n"
        "  - research: 0\n"
        "  - external-requests: 0\n"
        "\nQueue:\n"
        "\n📁 TECHNICAL DEBT (1 items)\n" + ("-" * 40) + "\n"
        "ID: DEBT-20990102-bar-debt\n"
        "Title: Bar debt\n"
        "Created: 2099-01-02 | Owner: @alice\n"
        "Path: parking-lot/technical-debt/DEBT-20990102-bar-debt\n"
        "\n"
        "Suggested actions (explicit; no prompting):\n"
        "- Promote an item:\n"
        "  ph parking promote --item <ID> --target later\n"
        "- List items (table/json):\n"
        "  ph parking list --format table\n"
        "  ph parking list --format json\n"
    )
    assert result.stdout == expected
