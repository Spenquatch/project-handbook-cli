from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_basic_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    rules_path = ph_root / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text("{}", encoding="utf-8")


def _run_validate_and_read_report(ph_root: Path) -> tuple[int, dict]:
    result = subprocess.run(
        ["ph", "validate", "--quick", "--root", str(ph_root)],
        capture_output=True,
        text=True,
    )
    report_path = ph_root / ".project-handbook" / "status" / "validation.json"
    assert report_path.exists()
    return result.returncode, json.loads(report_path.read_text(encoding="utf-8"))


def test_validate_release_plan_missing_slot_sections(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)

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
                "No slot sections yet.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    issues = report["issues"]
    missing = [i for i in issues if i.get("code") == "release_slot_missing"]
    assert {m.get("slot") for m in missing} == {1, 2}


def test_validate_release_plan_intended_gates_requires_gate_item(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)

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
                "",
                "### Intended Gates",
                "- TBD",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    issues = report["issues"]
    assert any(i.get("code") == "release_slot_intended_gates_missing_gate_item" for i in issues)


def test_validate_sprint_plan_requires_release_alignment_heading_when_assigned(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)

    sprint_plan = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-W01" / "plan.md"
    sprint_plan.parent.mkdir(parents=True, exist_ok=True)
    sprint_plan.write_text(
        "\n".join(
            [
                "---",
                "title: Sprint plan",
                "type: sprint-plan",
                "date: 2099-01-01",
                "sprint: SPRINT-2099-W01",
                "mode: bounded",
                "release: current",
                "release_sprint_slot: 2",
                "---",
                "",
                "# SPRINT-2099-W01",
                "",
                "No release alignment section yet.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    issues = report["issues"]
    assert any(i.get("code") == "sprint_release_alignment_missing" for i in issues)


def test_validate_sprint_plan_release_alignment_heading_ok_when_present(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)

    sprint_plan = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-W01" / "plan.md"
    sprint_plan.parent.mkdir(parents=True, exist_ok=True)
    sprint_plan.write_text(
        "\n".join(
            [
                "---",
                "title: Sprint plan",
                "type: sprint-plan",
                "date: 2099-01-01",
                "sprint: SPRINT-2099-W01",
                "mode: bounded",
                "release: current",
                "release_sprint_slot: 2",
                "---",
                "",
                "# SPRINT-2099-W01",
                "",
                "## Release Alignment (Slot 2)",
                "Slot goal: Example.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _, report = _run_validate_and_read_report(tmp_path)
    issues = report["issues"]
    assert not any(i.get("code") == "sprint_release_alignment_missing" for i in issues)
