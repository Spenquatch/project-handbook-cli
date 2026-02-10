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

    rules_path = ph_root / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(
        json.dumps(
            {
                "validation": {"require_front_matter": False, "skip_docs_directory": True},
                "sprint_tasks": {
                    "require_task_yaml": True,
                    "required_task_fields": [
                        "id",
                        "title",
                        "feature",
                        "decision",
                        "owner",
                        "status",
                        "story_points",
                        "task_type",
                        "session",
                    ],
                    "require_task_directory_files": False,
                    "enforce_sprint_scoped_dependencies": False,
                },
                "story_points": {"validate_fibonacci_sequence": False},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _read_validation_issues(ph_root: Path) -> list[dict]:
    report_path = ph_root / ".project-handbook" / "status" / "validation.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    issues = data.get("issues")
    assert isinstance(issues, list)
    return issues


def test_validate_errors_when_sprint_missing_sprint_gate_task(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    sprint_id = "SPRINT-SEQ-0099"
    task_dir = ph_data_root / "sprints" / "SEQ" / sprint_id / "tasks" / "TASK-001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Implementation task",
                "feature: f",
                "decision: ADR-0001",
                "owner: @a",
                "status: done",
                "story_points: 1",
                "task_type: implementation",
                "session: task-execution",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1

    issues = _read_validation_issues(tmp_path)
    gate_issue = next((i for i in issues if i.get("code") == "sprint_gate_task_missing"), None)
    assert gate_issue is not None
    assert "Sprint is missing a sprint gate task." in str(gate_issue.get("message"))
    assert "expected: at least 1 task under tasks/ with `task_type: sprint-gate`" in str(gate_issue.get("message"))


def test_validate_errors_when_sprint_gate_task_missing_required_markers(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    sprint_id = "SPRINT-SEQ-0100"
    gate_dir = ph_data_root / "sprints" / "SEQ" / sprint_id / "tasks" / "TASK-001-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Sprint gate",
                "feature: f",
                "decision: ADR-0001",
                "owner: @a",
                "status: done",
                "story_points: 1",
                "task_type: sprint-gate",
                "session: sprint-gate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Missing: Sprint Goal:, secret-scan.txt, status/evidence/, sprint plan reference.
    (gate_dir / "validation.md").write_text(
        "\n".join(
            [
                "# Validation",
                "",
                "Exit criteria: criteria",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1

    issues = _read_validation_issues(tmp_path)
    codes = {issue.get("code") for issue in issues}
    assert "sprint_gate_validation_markers_missing" in codes
    assert "sprint_gate_task_yaml_missing_evidence_prefix" in codes
    assert "sprint_gate_task_missing" not in codes

    marker_issue = next(i for i in issues if i.get("code") == "sprint_gate_validation_markers_missing")
    missing_markers = marker_issue.get("missing_markers")
    assert isinstance(missing_markers, list)
    assert "Sprint Goal:" in missing_markers
    assert "secret-scan.txt" in missing_markers
    assert "status/evidence/" in missing_markers
    assert any(str(m).startswith("sprint plan reference (one of:") for m in missing_markers)
    assert "task_id: TASK-001" in str(marker_issue.get("message"))

    yaml_issue = next(i for i in issues if i.get("code") == "sprint_gate_task_yaml_missing_evidence_prefix")
    assert "required_literal: status/evidence/" in str(yaml_issue.get("message"))


def test_validate_passes_when_sprint_gate_task_has_required_markers(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    sprint_id = "SPRINT-SEQ-0101"
    gate_dir = ph_data_root / "sprints" / "SEQ" / sprint_id / "tasks" / "TASK-001-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Sprint gate",
                "feature: f",
                "decision: ADR-0001",
                "owner: @a",
                "status: done",
                "story_points: 1",
                "task_type: sprint-gate",
                "session: sprint-gate",
                "evidence_dir: status/evidence/TASK-001/",
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
                "Sprint Goal: Validate the sprint is closeable",
                "Exit criteria: All gates pass",
                "",
                "- Evidence root: status/evidence/",
                "- Include secret-scan.txt",
                "- Sprint plan: sprints/current/plan.md",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout

    issues = _read_validation_issues(tmp_path)
    assert issues == []
