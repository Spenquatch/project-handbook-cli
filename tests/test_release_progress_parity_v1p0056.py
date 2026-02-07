from __future__ import annotations

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

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_release_progress_file_parity_v1p0056(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    version = "v0.6.0"
    release_dir = tmp_path / "releases" / version
    release_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "releases" / "current").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "releases" / "current").symlink_to(version)

    (release_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                "title: Release v0.6.0 Plan",
                "type: release-plan",
                "version: v0.6.0",
                "timeline_mode: sprint_slots",
                "planned_sprints: 4",
                "---",
                "",
                "# Release v0.6.0",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (release_dir / "features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "  v2_workspace-signup-onboarding:",
                "    critical_path: true",
                "  v2_provider-gateway-dynamic-providers:",
                "    critical_path: true",
                "  v2_launch:",
                "    critical_path: false",
                "  v2_context-glue-integrations:",
                "    critical_path: false",
                "  v2_context-knowledge-network:",
                "    critical_path: false",
                "  tribuence-mini-v2:",
                "    critical_path: false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Sprint slot assignments: slots 1-3 assigned, slot 4 unassigned.
    archived_2 = tmp_path / "sprints" / "archive" / "2026" / "SPRINT-SEQ-0002"
    archived_3 = tmp_path / "sprints" / "archive" / "2026" / "SPRINT-SEQ-0003"
    current_4 = tmp_path / "sprints" / "2026" / "SPRINT-SEQ-0004"
    for sprint_dir, slot in [(archived_2, 1), (archived_3, 2), (current_4, 3)]:
        sprint_dir.mkdir(parents=True, exist_ok=True)
        (sprint_dir / "plan.md").write_text(
            "\n".join(
                [
                    "---",
                    f"release: {version}",
                    f"release_sprint_slot: {slot}",
                    "---",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    (tmp_path / "sprints" / "current").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "sprints" / "current").symlink_to(Path("2026") / "SPRINT-SEQ-0004")

    # Tasks for feature completion (all done → 100%).
    tasks_root = current_4 / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    for i, feature in enumerate(
        [
            "v2_workspace-signup-onboarding",
            "v2_provider-gateway-dynamic-providers",
            "v2_launch",
            "v2_context-glue-integrations",
            "v2_context-knowledge-network",
            "tribuence-mini-v2",
        ],
        1,
    ):
        task_dir = tasks_root / f"TASK-{i:03d}-{feature}"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "task.yaml").write_text(
            "\n".join(
                [
                    f"id: TASK-{i:03d}",
                    f"title: Done: {feature}",
                    f"feature: {feature}",
                    "status: done",
                    "story_points: 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    # A single done gate task in Sprint slot 2 (archived).
    gate_tasks_root = archived_3 / "tasks"
    gate_tasks_root.mkdir(parents=True, exist_ok=True)
    gate_dir = gate_tasks_root / "TASK-005-gate-demo"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-005",
                "title: Gate: V2 functional demo gate (v0.6.0)",
                "feature: v2_launch",
                "status: done",
                "story_points: 1",
                "release: current",
                "release_gate: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2026-02-05"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "progress"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    progress_path = tmp_path / "releases" / version / "progress.md"
    expected_stdout = f"📝 Updated: {progress_path}\n"
    assert result.stdout == expected_stdout

    expected_progress = (
        "\n".join(
            [
                "---",
                "title: Release v0.6.0 Progress",
                "type: release-progress",
                "version: v0.6.0",
                "date: 2026-02-05",
                "tags: [release, progress]",
                "links: [releases/v0.6.0/plan.md, releases/v0.6.0/features.yaml]",
                "---",
                "",
                "# Release v0.6.0 Progress",
                "",
                "*This file is auto-generated. Do not edit manually.*",
                "",
                "## Sprint Progress",
                "- **Slot 1**: ✅ Complete — SPRINT-SEQ-0002 (Sprint 1 of 4)",
                "- **Slot 2**: ✅ Complete — SPRINT-SEQ-0003 (Sprint 2 of 4)",
                "- **Slot 3**: 🔄 In Progress — SPRINT-SEQ-0004 (Sprint 3 of 4)",
                "- **Slot 4**: ⭕ Planned — (unassigned) (Sprint 4 of 4)",
                "",
                "## Feature Progress",
                "- ✅ v2_workspace-signup-onboarding: 100% (Critical Path)",
                "- ✅ v2_provider-gateway-dynamic-providers: 100% (Critical Path)",
                "- ✅ v2_launch: 100%",
                "- ✅ v2_context-glue-integrations: 100%",
                "- ✅ v2_context-knowledge-network: 100%",
                "- ✅ tribuence-mini-v2: 100%",
                "",
                "## Gate Burn-up",
                "- Gates: 1/1 complete",
                "- ✅ TASK-005: Gate: V2 functional demo gate (v0.6.0) (SPRINT-SEQ-0003)",
                "",
                "## Release Health",
                "- Readiness: 🟢 GREEN - Ready to ship",
            ]
        )
        + "\n"
    )
    assert progress_path.read_text(encoding="utf-8") == expected_progress
