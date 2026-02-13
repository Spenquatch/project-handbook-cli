from __future__ import annotations

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


def test_release_migrate_slot_format_converts_legacy_to_strict(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = tmp_path / ".project-handbook" / "releases" / "v1.0.0" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        "\n".join(
            [
                "---",
                "title: Release v1.0.0 Plan",
                "type: release-plan",
                "version: v1.0.0",
                "timeline_mode: sprint_slots",
                "planned_sprints: 2",
                "sprint_slots: [1, 2]",
                "status: planned",
                "date: 2099-01-01",
                "---",
                "",
                "# Release v1.0.0",
                "",
                "## Slot Plans",
                "",
                "### Slot 1",
                "",
                "#### Goal / Purpose",
                "- Build login flow",
                "",
                "#### Scope boundaries (in/out)",
                "- In: Basic auth",
                "- Out: SSO",
                "",
                "#### Intended gate(s)",
                "- Gate: Login smoke test",
                "",
                "#### Enablement",
                "- Unlock onboarding",
                "",
                "### Slot 2",
                "",
                "#### Goal / Purpose",
                "- Stabilize",
                "",
                "#### Scope boundaries (in/out)",
                "- In: Error states",
                "- Out: New major features",
                "",
                "#### Intended gate(s)",
                "- Gate: Demo-ready UX",
                "",
                "#### Enablement",
                "- Raise confidence",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    diff = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "migrate-slot-format",
            "--release",
            "v1.0.0",
            "--diff",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert diff.returncode == 0
    assert "## Slot 1:" in diff.stdout

    applied = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "migrate-slot-format",
            "--release",
            "v1.0.0",
            "--write-back",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert applied.returncode == 0

    migrated = plan.read_text(encoding="utf-8")
    assert "## Slot Plans" not in migrated
    assert "## Slot 1:" in migrated
    assert "### Intended Gates" in migrated
