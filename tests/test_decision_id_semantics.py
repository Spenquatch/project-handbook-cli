from __future__ import annotations

import subprocess
from pathlib import Path

from ph.validate_docs import validate_sprints


def _write_legacy_like_config(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('{\n  "repo_root": "/tmp"\n}\n', encoding="utf-8")


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_task(
    ph_root: Path,
    *,
    task_id: str,
    session: str,
    decision: str,
    task_type: str | None = None,
    steps: str,
    validation: str,
    extra_task_yaml_lines: list[str] | None = None,
) -> None:
    task_dir = ph_root / ".project-handbook" / "sprints" / "current" / "tasks" / f"{task_id}-decision-semantics"
    task_dir.mkdir(parents=True, exist_ok=True)

    yaml_lines = [
        f"id: {task_id}",
        "title: Parity task",
        "owner: '@a'",
        "lane: ops",
        "feature: f",
        f"decision: {decision}",
    ]
    if task_type is not None:
        yaml_lines.append(f"task_type: {task_type}")
    yaml_lines.extend(
        [
            f"session: {session}",
            "story_points: 1",
            "depends_on: []",
        ]
    )
    if extra_task_yaml_lines:
        yaml_lines.extend(extra_task_yaml_lines)

    (task_dir / "task.yaml").write_text(
        "\n".join([*yaml_lines, ""]),
        encoding="utf-8",
    )

    (task_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                f"task_id: {task_id}",
                f"session: {session}",
                "feature: f",
                "---",
                "",
                f"# {task_id}",
                "",
                f"Decision: {decision}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "steps.md").write_text(steps, encoding="utf-8")
    (task_dir / "commands.md").write_text(
        "\n".join(
            [
                "# Commands",
                "",
                f"Evidence path: status/evidence/{task_id}/command-output.txt",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "checklist.md").write_text(
        "\n".join(
            [
                "# Checklist",
                "",
                f"- [ ] {task_id} complete",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "validation.md").write_text(validation, encoding="utf-8")
    (task_dir / "references.md").write_text(
        "\n".join(
            [
                "# References",
                "",
                "### Decision Context",
                f"- **Decision**: {decision}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_pre_exec_lint_fails_when_research_discovery_task_uses_adr_decision(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_task(
        tmp_path,
        task_id="TASK-001",
        session="research-discovery",
        decision="ADR-0001",
        steps="\n".join(
            [
                "# Steps",
                "",
                "Decision Register entry: DR-0001",
                "",
                "Option A: Do A",
                "Option B: Do B",
                "",
                "1) Complete TASK-001",
                "",
            ]
        ),
        validation="\n".join(
            [
                "# Validation",
                "",
                "Expected evidence file: status/evidence/TASK-001/secret-scan.txt",
                "",
            ]
        ),
    )

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Decision id mismatch for session research-discovery" in result.stdout
    assert "expected DR-XXXX" in result.stdout
    assert "found ADR-0001" in result.stdout


def test_pre_exec_lint_fails_when_task_execution_task_uses_dr_decision(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_task(
        tmp_path,
        task_id="TASK-001",
        session="task-execution",
        decision="DR-0001",
        steps="\n".join(
            [
                "# Steps",
                "",
                "1) Implement the thing for TASK-001",
                "",
            ]
        ),
        validation="\n".join(
            [
                "# Validation",
                "",
                "Expected evidence file: status/evidence/TASK-001/secret-scan.txt",
                "",
            ]
        ),
    )

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Decision id mismatch for session task-execution" in result.stdout
    assert "expected ADR-XXXX or FDR-..." in result.stdout
    assert "found DR-0001" in result.stdout


def test_pre_exec_lint_fails_when_sprint_gate_task_uses_dr_decision(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_task(
        tmp_path,
        task_id="TASK-000",
        session="sprint-gate",
        decision="DR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-000/"],
        steps="\n".join(["# Steps", "", "1) Run the gate checks", ""]),
        validation="\n".join(
            [
                "# Validation",
                "",
                "Sprint Goal: Ensure the sprint is closeable",
                "Exit criteria: All checks pass",
                "",
                "- Evidence root: status/evidence/",
                "- Expect secret-scan.txt in status/evidence/TASK-000/",
                "- Include pre-exec-lint.txt",
                "- Sprint plan: sprints/current/plan.md",
                "",
            ]
        ),
    )

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Decision id mismatch for session task-execution" in result.stdout
    assert "expected ADR-XXXX or FDR-..." in result.stdout
    assert "found DR-0001" in result.stdout


def test_pre_exec_lint_passes_when_research_discovery_task_uses_dr_decision(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_task(
        tmp_path,
        task_id="TASK-000",
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-000/"],
        steps="\n".join(["# Steps", "", "1) Run the gate checks", ""]),
        validation="\n".join(
            [
                "# Validation",
                "",
                "Sprint Goal: Ensure the sprint is closeable",
                "Exit criteria: All checks pass",
                "",
                "- Evidence root: status/evidence/",
                "- Expect secret-scan.txt in status/evidence/TASK-000/",
                "- Include pre-exec-lint.txt",
                "- Sprint plan: sprints/current/plan.md",
                "",
            ]
        ),
    )
    _write_task(
        tmp_path,
        task_id="TASK-001",
        session="research-discovery",
        decision="DR-0001",
        steps="\n".join(
            [
                "# Steps",
                "",
                "Decision Register entry: DR-0001",
                "",
                "Option A: Do A",
                "Option B: Do B",
                "",
                "1) Complete TASK-001",
                "",
            ]
        ),
        validation="\n".join(
            [
                "# Validation",
                "",
                "Expected evidence file: status/evidence/TASK-001/secret-scan.txt",
                "",
            ]
        ),
    )

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "PRE-EXEC LINT PASSED" in result.stdout


def _write_sprint_task_yaml(task_dir: Path, *, task_id: str, session: str, decision: str) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join([f"id: {task_id}", "title: T", "feature: f", f"decision: {decision}", f"session: {session}", ""]),
        encoding="utf-8",
    )


def _write_dr_entry(ph_data_root: Path, *, dr_id: str, feature: str | None = None) -> None:
    if feature:
        folder = ph_data_root / "features" / feature / "decision-register"
    else:
        folder = ph_data_root / "decision-register"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{dr_id}-entry.md").write_text(f"# Decision Register Entry\n\n### {dr_id} — Test\n", encoding="utf-8")


def test_validate_sprints_flags_invalid_decision_for_session(tmp_path: Path) -> None:
    ph_data_root = tmp_path / ".project-handbook"
    task_dir = ph_data_root / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks" / "TASK-001-decision-semantics"
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="research-discovery", decision="ADR-0001")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "decision", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": True,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )
    assert any(
        i.get("code") == "task_decision_invalid" and i.get("expected") == "DR-XXXX" and i.get("found") == "ADR-0001"
        for i in issues
    ), issues


def test_validate_sprints_flags_dr_decision_on_task_execution(tmp_path: Path) -> None:
    ph_data_root = tmp_path / ".project-handbook"
    task_dir = ph_data_root / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks" / "TASK-001-decision-semantics"
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="task-execution", decision="DR-0001")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "decision", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": True,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )
    assert any(
        i.get("code") == "task_decision_invalid"
        and i.get("expected") == "ADR-XXXX or FDR-..."
        and i.get("found") == "DR-0001"
        for i in issues
    ), issues


def test_validate_sprints_accepts_valid_session_decision_pairs(tmp_path: Path) -> None:
    ph_data_root = tmp_path / ".project-handbook"
    _write_dr_entry(ph_data_root, dr_id="DR-0001")
    task_dir = ph_data_root / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks" / "TASK-001-decision-semantics"
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="research-discovery", decision="DR-0001")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "decision", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": True,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )
    assert not any(i.get("code") == "task_decision_invalid" for i in issues), issues


def test_validate_sprints_flags_missing_dr_doc(tmp_path: Path) -> None:
    ph_data_root = tmp_path / ".project-handbook"
    task_dir = ph_data_root / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks" / "TASK-001-decision-semantics"
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="research-discovery", decision="DR-0001")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "decision", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": True,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )
    missing = next(i for i in issues if i.get("code") == "task_dr_missing")
    assert missing.get("severity") == "error"
    assert missing.get("dr_id") == "DR-0001"
    assert "decision-register" in str(missing.get("searched_dirs", []))


def test_validate_sprints_accepts_feature_scoped_dr_doc(tmp_path: Path) -> None:
    ph_data_root = tmp_path / ".project-handbook"
    _write_dr_entry(ph_data_root, dr_id="DR-0001", feature="f")
    task_dir = ph_data_root / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks" / "TASK-001-decision-semantics"
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="research-discovery", decision="DR-0001")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "decision", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": True,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )
    assert not any(i.get("code") == "task_dr_missing" for i in issues), issues
