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


def test_parking_promote_stdout_matches_legacy_make_v1p0040(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"

    expected_id = "DEBT-20990101-parity-promote-item"

    add_result = subprocess.run(
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
            "Parity promote item",
            "--desc",
            "Seed for V1P-0040",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add_result.returncode == 0

    promote_result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "parking",
            "promote",
            "--item",
            expected_id,
            "--target",
            "later",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert promote_result.returncode == 0

    expected_root = tmp_path.resolve()
    expected = (
        f"\n> project-handbook@0.0.0 ph {expected_root}\n"
        f"> ph parking promote --item {expected_id} --target later\n\n"
        f"✅ Promoted {expected_id} to roadmap/later/\n"
        "📊 Updated parking lot index: 0 items\n"
    )
    assert promote_result.stdout == expected

    assert (tmp_path / "roadmap" / "later" / expected_id).exists()
    assert not (tmp_path / "parking-lot" / "technical-debt" / expected_id).exists()
