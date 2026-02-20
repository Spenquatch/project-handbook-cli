from __future__ import annotations

import datetime as dt
import os
import subprocess
from pathlib import Path


def _write_legacy_like_config(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('{\n  "repo_root": "/tmp"\n}\n', encoding="utf-8")


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_validation_rules_no_front_matter(ph_root: Path) -> None:
    rules_path = ph_root / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text('{\n  "validation": {\n    "require_front_matter": false\n  }\n}\n', encoding="utf-8")


def _write_seq_sprint_with_one_task(*, ph_root: Path, sprint_id: str, today: dt.date) -> None:
    sprint_dir = ph_root / ".project-handbook" / "sprints" / "archive" / "SEQ" / sprint_id
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    (sprint_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                f"title: Sprint Plan - {sprint_id}",
                "type: sprint-plan",
                f"date: {today:%Y-%m-%d}",
                f"sprint: {sprint_id}",
                "mode: bounded",
                "tags: [sprint, planning]",
                "release: null",
                "---",
                "",
                f"# Sprint Plan: {sprint_id}",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    task_dir = tasks_dir / "TASK-001-minimal"
    task_dir.mkdir(parents=True, exist_ok=True)

    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Implement minimal task",
                "owner: @owner",
                "lane: lane-a",
                "feature: feature-a",
                "decision: ADR-0001",
                "session: task-execution",
                "status: done",
                "story_points: 3",
                "prio: P1",
                "due: 2026-01-01",
                "acceptance: done",
                "depends_on: FIRST_TASK",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Keep docs non-empty and lint-clean: include evidence path + secret scan marker.
    docs = {
        "README.md": "# TASK-001\n\nMinimal task.\n",
        "steps.md": "1. Do the thing.\n",
        "commands.md": "echo status/evidence/TASK-001/example.txt\n",
        "checklist.md": "- [x] Done\n",
        "validation.md": "Expect secret-scan.txt in status/evidence/TASK-001/\n",
        "references.md": "- none\n",
    }
    for name, content in docs.items():
        (task_dir / name).write_text(content, encoding="utf-8")

    sprints_dir = ph_root / ".project-handbook" / "sprints"
    sprints_dir.mkdir(parents=True, exist_ok=True)
    current_link = sprints_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(Path("archive") / "SEQ" / sprint_id)


def test_pre_exec_audit_stdout_and_evidence_match_make_pre_exec_audit(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_validation_rules_no_front_matter(tmp_path)

    sprint_id = "SPRINT-SEQ-0001"
    date = "2026-01-01"
    today = dt.date.today()
    _write_seq_sprint_with_one_task(ph_root=tmp_path, sprint_id=sprint_id, today=today)

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "pre-exec",
            "audit",
            "--sprint",
            sprint_id,
            "--date",
            date,
        ],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert result.returncode == 1

    resolved = tmp_path.resolve()
    evidence_dir = (resolved / ".project-handbook" / "status" / "evidence" / "PRE-EXEC" / sprint_id / date).resolve()
    section = "════════════════════════════════════════════════"
    rule = "=" * 60

    sprint_status_out = (
        "Sprint: SPRINT-SEQ-0001\n"
        "Mode: bounded | Age: 0 days\n"
        "Health: 🟢 GREEN - Flowing\n"
        "Progress: 3/3 points (100%)\n"
        "\n"
        "Sprint gates:\n"
        "⚠️  No sprint gate tasks found (task_type: sprint-gate).\n"
        "Gate-ready: NO\n"
        "\n"
        "Current focus:\n"
        "- No active tasks. Pull the next planned item.\n"
        "Next up:\n"
        "- No planned backlog entries remaining in this sprint.\n"
        "\n"
        "Lanes:\n"
        "- lane-a: 3/3 pts done (blocked 0)\n"
        "\n"
        "Tip: use `ph onboarding session task-execution` (alias: `implement`) for detailed hand-off guidance.\n"
    )

    release_status_out = (
        "❌ No current release found\n\n"
        "Next commands:\n"
        "- ph release plan --version v1.2.0 --sprints 3 --activate\n"
        "- Re-run: ph release status\n"
    )

    task_list_out = (
        "📋 SPRINT TASKS: SPRINT-SEQ-0001\n"
        f"{rule}\n"
        "✅ TASK-001: Implement minimal task  [lane-a] (task-execution) [3pts] (depends: FIRST_TASK)\n"
    )

    feature_summary_line = f"🎉 {'feature-a':<25} {3:3d}/{3:3d} pts ({100:3d}%) Current: 1 tasks\n"
    feature_summary_out = f"🎯 FEATURE SUMMARY WITH SPRINT DATA\n{rule}\n{feature_summary_line}"

    validate_out = (
        f"validation: 9 error(s), 0 warning(s), report: {resolved}/.project-handbook/status/validation.json\n"
    )

    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        f"> ph pre-exec audit --sprint {sprint_id} --date {date}\n"
        "\n"
        f"EVIDENCE_DIR={evidence_dir}\n"
        "\n"
        f"{section}\n"
        "PRE-EXEC: sprint-status\n"
        f"{section}\n"
        f"{sprint_status_out}"
        "\n"
        f"{section}\n"
        "PRE-EXEC: release-status\n"
        f"{section}\n"
        f"{release_status_out}"
        "\n"
        f"{section}\n"
        "PRE-EXEC: task-list\n"
        f"{section}\n"
        f"{task_list_out}"
        "\n"
        f"{section}\n"
        "PRE-EXEC: feature-summary\n"
        f"{section}\n"
        f"{feature_summary_out}"
        "\n"
        f"{section}\n"
        "PRE-EXEC: validate\n"
        f"{section}\n"
        f"{validate_out}"
        f"\n❌ PRE-EXEC AUDIT FAILED: validate failed (exit 1). See {evidence_dir}/handbook-validate.txt\n"
    )
    assert result.stdout == expected_stdout

    assert (evidence_dir / "sprint-status.txt").read_text(encoding="utf-8") == sprint_status_out
    assert (evidence_dir / "release-status.txt").read_text(encoding="utf-8") == release_status_out
    assert (evidence_dir / "task-list.txt").read_text(encoding="utf-8") == task_list_out
    assert (evidence_dir / "feature-summary.txt").read_text(encoding="utf-8") == feature_summary_out
    assert (evidence_dir / "handbook-validate.txt").read_text(encoding="utf-8") == validate_out
    assert not (evidence_dir / "pre-exec-lint.txt").exists()
    assert not (evidence_dir / "validation.json").exists()


def test_release_status_sprint_slots_matches_legacy_format(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_validation_rules_no_front_matter(tmp_path)

    sprint_id = "SPRINT-SEQ-0001"
    today = dt.date.today()
    _write_seq_sprint_with_one_task(ph_root=tmp_path, sprint_id=sprint_id, today=today)

    version = "v1.0.0"
    (tmp_path / ".project-handbook" / "releases" / version).mkdir(parents=True, exist_ok=True)
    releases_dir = tmp_path / ".project-handbook" / "releases"
    current_link = releases_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink()
    current_link.symlink_to(version)

    (tmp_path / ".project-handbook" / "releases" / version / "plan.md").write_text(
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
                f"date: {today:%Y-%m-%d}",
                "tags: [release, planning]",
                "links: []",
                "---",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / ".project-handbook" / "releases" / version / "features.yaml").write_text(
        "\n".join(
            [
                "version: v1.0.0",
                "features:",
                "  feature-a:",
                "    type: regular",
                "    critical_path: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Attach the sprint to slot 1.
    sprint_dir = tmp_path / ".project-handbook" / "sprints" / "archive" / "SEQ" / sprint_id
    plan_path = sprint_dir / "plan.md"
    plan_path.write_text(
        plan_path.read_text(encoding="utf-8").replace("release: null", f"release: {version}\nrelease_sprint_slot: 1"),
        encoding="utf-8",
    )

    # Tag TASK-001 to the release so it shows up in the tagged workstream.
    task_001_yaml = sprint_dir / "tasks" / "TASK-001-minimal" / "task.yaml"
    task_001_yaml.write_text(
        task_001_yaml.read_text(encoding="utf-8") + f"release: {version}\n",
        encoding="utf-8",
    )

    # Add a second tagged task to exercise tagged sort + gate suffix.
    task_dir = sprint_dir / "tasks" / "TASK-002-gate"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-002",
                f"title: Gate: Example ({version})",
                "owner: @owner",
                "lane: lane-a",
                "feature: feature-a",
                "decision: ADR-0002",
                "session: task-execution",
                "status: done",
                "story_points: 3",
                "prio: P1",
                "due: 2026-01-01",
                "acceptance: done",
                "depends_on: TASK-001",
                f"release: {version}",
                "release_gate: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for name, content in {
        "README.md": "# TASK-002\n",
        "steps.md": "1. Run gate.\n",
        "commands.md": "echo status/evidence/TASK-002/example.txt\n",
        "checklist.md": "- [x] Done\n",
        "validation.md": "Expect secret-scan.txt in status/evidence/TASK-002/\n",
        "references.md": "- none\n",
    }.items():
        (task_dir / name).write_text(content, encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "status"],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert result.returncode == 0

    expected = (
        f"📦 RELEASE STATUS: {version}\n" + "=" * 60 + "\n"
        f"Sprint: 1 of 2 (slot 1) ({sprint_id})\n"
        "Slot Goal: TBD\n"
        "⚠️ Alignment warnings:\n"
        "  - Current sprint plan is missing required heading: `## Release Alignment (Slot 1)`.\n"
        "  - Release plan is missing required slot markers for Slot 1 (expected `## Slot 1: <label>` + subsections).\n"
        "Feature Completion (historical): 100% (1/1 features started)\n"
        "Target: Slot 2\n"
        "Feature Trajectory (historical): 🟢 GREEN - Ahead of expected completion for Sprint 1\n"
        "  Expected completion band: 0–50% by end of Sprint 1/2\n"
        "Release-Tagged Workstream: 100% (6/6 pts) across 2 tasks (1 features)\n"
        "Release-Tagged Trajectory: 🟢 GREEN - Ahead of expected completion for Sprint 1\n"
        "  Expected completion band: 0–50% by end of Sprint 1/2\n"
        "Gate Burn-up: 1/1 complete (in timeline: 1/1)\n"
        "Release Readiness (gate-first): 🟢 GREEN - Gates complete (Ready to ship)\n"
        "\n"
        "🎯 Feature Completion (historical):\n"
        "✅ feature-a            100% complete (Critical Path)\n"
        "\n"
        "🏷️ Release-Tagged Tasks:\n"
        f"✅ TASK-002: Gate: Example ({version}) (3pts) [feature-a] {sprint_id} [gate]\n"
        "✅ TASK-001: Implement minimal task (3pts) [feature-a] SPRINT-SEQ-0001\n"
        "\n"
        "📅 Sprint Breakdown:\n"
        f"🔄 In progress ▶ Slot 1: {sprint_id} — Goal: TBD (Sprint 1 of 2)\n"
        "⭕ Planned Slot 2: (unassigned) — Goal: TBD (Sprint 2 of 2)\n"
    )
    assert result.stdout == expected
