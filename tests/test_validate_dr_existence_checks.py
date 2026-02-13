from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    rules = {
        "validation": {"require_front_matter": False},
        "sprint_tasks": {
            "required_task_fields": ["id", "title", "feature", "decision", "session", "task_type"],
            "require_task_yaml": True,
            "require_single_decision_per_task": True,
            "require_task_directory_files": False,
            "enforce_sprint_scoped_dependencies": False,
        },
        "story_points": {"validate_fibonacci_sequence": False},
        "roadmap": {"normalize_links": False},
    }
    rules_path = ph_root / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")


def test_validate_quick_flags_missing_dr_entry_for_research_discovery_task(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    tasks_dir = tmp_path / ".project-handbook" / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks"
    gate_dir = tasks_dir / "TASK-000-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-000",
                "title: Sprint gate",
                "feature: f",
                "decision: ADR-0001",
                "session: sprint-gate",
                "task_type: sprint-gate",
                "evidence_dir: status/evidence/TASK-000/",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (gate_dir / "validation.md").write_text(
        "\n".join(
            [
                "# Validation",
                "",
                "Sprint Goal: Ensure the sprint is closeable",
                "Exit criteria: All checks pass",
                "",
                "- Evidence root: status/evidence/",
                "- Include secret-scan.txt",
                "- Include pre-exec-lint.txt",
                "- Sprint plan: sprints/current/plan.md",
                "",
            ]
        ),
        encoding="utf-8",
    )

    task_dir = tasks_dir / "TASK-001-missing-dr"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Research task",
                "feature: f",
                "decision: DR-0001",
                "session: research-discovery",
                "task_type: research-discovery",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["ph", "validate", "--quick", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    report_path = tmp_path / ".project-handbook" / "status" / "validation.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert result.returncode == 1, result.stdout + result.stderr
    missing = next(i for i in report["issues"] if i.get("code") == "task_dr_missing")
    assert missing.get("severity") == "error"
    assert missing.get("dr_id") == "DR-0001"
    assert "decision-register" in str(missing.get("searched_dirs", []))
