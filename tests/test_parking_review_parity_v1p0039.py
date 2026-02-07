from __future__ import annotations

import json
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
    parking_lot_dir = tmp_path / "parking-lot"
    parking_lot_dir.mkdir(parents=True, exist_ok=True)
    (parking_lot_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "parking", "review"],
        capture_output=True,
        text=True,
        env=env,
        stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 2

    expected_root = tmp_path.resolve()
    expected = (
        f"\n> project-handbook@0.0.0 ph {expected_root}\n"
        "> ph parking review\n\n"
        "\n🔍 PARKING LOT QUARTERLY REVIEW\n"
        + ("=" * 80)
        + "\n"
        "Review each item and decide its fate:\n"
        "  [p]romote to roadmap\n"
        "  [d]elete/archive\n"
        "  [s]kip (keep in parking lot)\n"
        "  [q]uit review\n\n"
        + ("-" * 40)
        + "\n"
        "ID: DEBT-20990102-bar-debt\n"
        "Type: technical-debt\n"
        "Title: Bar debt\n"
        "Created: 2099-01-02\n"
        "Owner: @alice\n"
        f"Description: {desc[:200]}...\n"
        "\nAction ([p]romote/[d]elete/[s]kip/[v]iew full/[q]uit): "
        "\u2009ELIFECYCLE\u2009 Command failed with exit code 2.\n"
    )
    assert result.stdout == expected
