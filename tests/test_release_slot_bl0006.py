from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path, *, validation_rules: str = "{}") -> None:
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

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text(validation_rules, encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _run_validate_and_read_report(ph_root: Path) -> tuple[int, dict]:
    result = subprocess.run(
        ["ph", "validate", "--quick", "--root", str(ph_root)],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    report_path = ph_root / ".project-handbook" / "status" / "validation.json"
    assert report_path.exists()
    return result.returncode, json.loads(report_path.read_text(encoding="utf-8"))


def test_validate_release_plan_slot_sections_happy_path(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    plan_path = tmp_path / ".project-handbook" / "releases" / "v1.0.0" / "plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
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
                "## Slot 1: Foundation",
                "### Slot Goal",
                "- Build login flow",
                "### Enablement",
                "- Unblocks onboarding",
                "### Scope Boundaries",
                "In scope:",
                "- Basic auth",
                "Out of scope:",
                "- SSO",
                "### Intended Gates",
                "- Gate: Login smoke test",
                r"\s-\sGate: Login smoke test",
                "",
                "## Slot 2: Hardening",
                "### Slot Goal",
                "- Stabilize and polish",
                "### Enablement",
                "- Raises confidence",
                "### Scope Boundaries",
                "In scope:",
                "- Error states",
                "Out of scope:",
                "- New major features",
                "### Intended Gates",
                "- Gate: Demo-ready UX",
                r"\s-\sGate: Demo-ready UX",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 0
    issues = report["issues"]
    assert not [i for i in issues if i.get("code", "").startswith("release_slot_")]


def test_validate_release_plan_duplicate_slot_heading_errors(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    plan_path = tmp_path / ".project-handbook" / "releases" / "v1.0.0" / "plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "---",
                "title: Release v1.0.0 Plan",
                "type: release-plan",
                "version: v1.0.0",
                "timeline_mode: sprint_slots",
                "planned_sprints: 1",
                "sprint_slots: [1]",
                "status: planned",
                "date: 2099-01-01",
                "---",
                "",
                "# Release v1.0.0",
                "",
                "## Slot 1: Foundation",
                "### Intended Gates",
                "- Gate: Login smoke test",
                r"\s-\sGate: Login smoke test",
                "",
                "## Slot 1: Duplicate",
                "### Intended Gates",
                "- Gate: Second marker",
                r"\s-\sGate: Second marker",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    issues = report["issues"]
    assert any(i.get("code") == "release_slot_duplicate" and i.get("slot") == 1 for i in issues)


def test_validate_release_plan_slot_missing_intended_gates_section_errors(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    plan_path = tmp_path / ".project-handbook" / "releases" / "v1.0.0" / "plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "---",
                "title: Release v1.0.0 Plan",
                "type: release-plan",
                "version: v1.0.0",
                "timeline_mode: sprint_slots",
                "planned_sprints: 1",
                "sprint_slots: [1]",
                "status: planned",
                "date: 2099-01-01",
                "---",
                "",
                "# Release v1.0.0",
                "",
                "## Slot 1: Foundation",
                "### Slot Goal",
                "- Build login flow",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    issues = report["issues"]
    assert any(i.get("code") == "release_slot_intended_gates_missing" and i.get("slot") == 1 for i in issues)


def test_release_status_warns_when_current_slot_assignment_is_misaligned(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    version = "v1.2.3"
    release_dir = tmp_path / ".project-handbook" / "releases" / version
    release_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".project-handbook" / "releases" / "current").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".project-handbook" / "releases" / "current").symlink_to(version)

    # NOTE: release status alignment parsing currently expects "### Slot <n>" + "#### ..." subsections.
    (release_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                f"title: Release {version} Plan",
                "type: release-plan",
                f"version: {version}",
                "timeline_mode: sprint_slots",
                "planned_sprints: 2",
                "sprint_slots: [1, 2]",
                "status: planned",
                "date: 2099-01-01",
                "---",
                "",
                f"# Release {version}",
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
                "* Gate: Login smoke test",
                "",
                "#### Enablement",
                "- Unblocks onboarding",
                "",
                "### Slot 2",
                "",
                "#### Goal / Purpose",
                "- TBD",
                "",
                "#### Scope boundaries (in/out)",
                "- In: TBD",
                "- Out: TBD",
                "",
                "#### Intended gate(s)",
                "- TBD",
                "",
                "#### Enablement",
                "- TBD",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # No features are required to surface alignment warnings.
    (release_dir / "features.yaml").write_text("features:\n", encoding="utf-8")

    year_dir = tmp_path / ".project-handbook" / "sprints" / "2026"
    sprint_1 = year_dir / "SPRINT-SEQ-0001"
    sprint_2 = year_dir / "SPRINT-SEQ-0002"
    sprint_1.mkdir(parents=True, exist_ok=True)
    sprint_2.mkdir(parents=True, exist_ok=True)

    # Two sprints claim slot 1; release status should warn about the mismatch and duplicates.
    for sprint_dir in (sprint_1, sprint_2):
        (sprint_dir / "plan.md").write_text(
            "\n".join(
                [
                    "---",
                    f"release: {version}",
                    "release_sprint_slot: 1",
                    "---",
                    "",
                    "## Release Alignment (Slot 1)",
                    "Slot goal: Build login flow",
                    "Enablement: Unblocks onboarding",
                    "Intended gates:",
                    "- Gate: Login smoke test",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    (tmp_path / ".project-handbook" / "sprints" / "current").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".project-handbook" / "sprints" / "current").symlink_to(Path("2026") / "SPRINT-SEQ-0002")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "show"],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert result.returncode == 0
    assert "⚠️ Alignment warnings:" in result.stdout
    assert "  - Slot 1 is assigned to `SPRINT-SEQ-0001`, but current sprint is `SPRINT-SEQ-0002`." in result.stdout
    assert "  - Slot 1 has multiple sprint assignments: SPRINT-SEQ-0001, SPRINT-SEQ-0002." in result.stdout
