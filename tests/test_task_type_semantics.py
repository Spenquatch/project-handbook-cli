from __future__ import annotations

from pathlib import Path

from ph.validate_docs import validate_sprints


def _write_sprint_task_yaml(
    task_dir: Path,
    *,
    task_id: str,
    session: str,
    task_type: str | None = None,
) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"id: {task_id}",
        "title: T",
        "feature: f",
        f"session: {session}",
    ]
    if task_type is not None:
        lines.append(f"task_type: {task_type}")
    lines.append("")
    (task_dir / "task.yaml").write_text("\n".join(lines), encoding="utf-8")


def _validate_one_task(*, tmp_path: Path) -> tuple[Path, Path]:
    ph_data_root = tmp_path / ".project-handbook"
    task_dir = ph_data_root / "sprints" / "2026" / "SPRINT-2026-01-01" / "tasks" / "TASK-001-type-semantics"
    return ph_data_root, task_dir


def test_validate_sprints_flags_invalid_task_type(tmp_path: Path) -> None:
    ph_data_root, task_dir = _validate_one_task(tmp_path=tmp_path)
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="task-execution", task_type="not-a-real-type")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": False,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )

    assert any(i.get("code") == "task_type_invalid" and i.get("found") == "not-a-real-type" for i in issues), issues


def test_validate_sprints_flags_task_type_session_mismatch(tmp_path: Path) -> None:
    ph_data_root, task_dir = _validate_one_task(tmp_path=tmp_path)
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="research-discovery", task_type="implementation")

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": False,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )

    assert any(
        i.get("code") == "task_type_session_mismatch"
        and i.get("task_type") == "implementation"
        and i.get("expected") == "task-execution"
        and i.get("found") == "research-discovery"
        for i in issues
    ), issues


def test_validate_sprints_defaults_missing_task_type_for_legacy_task_execution(tmp_path: Path) -> None:
    ph_data_root, task_dir = _validate_one_task(tmp_path=tmp_path)
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="task-execution", task_type=None)

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": False,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )

    assert not any(
        i.get("code") in {"task_type_invalid", "task_type_missing", "task_type_session_mismatch"} for i in issues
    )


def test_validate_sprints_defaults_missing_task_type_for_legacy_research_discovery(tmp_path: Path) -> None:
    ph_data_root, task_dir = _validate_one_task(tmp_path=tmp_path)
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="research-discovery", task_type=None)

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": False,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )

    assert not any(
        i.get("code") in {"task_type_invalid", "task_type_missing", "task_type_session_mismatch"} for i in issues
    )


def test_validate_sprints_flags_missing_task_type_for_non_legacy_session(tmp_path: Path) -> None:
    ph_data_root, task_dir = _validate_one_task(tmp_path=tmp_path)
    _write_sprint_task_yaml(task_dir, task_id="TASK-001", session="sprint-gate", task_type=None)

    issues: list[dict] = []
    validate_sprints(
        issues=issues,
        rules={
            "sprint_tasks": {
                "required_task_fields": ["id", "title", "feature", "session"],
                "require_task_yaml": True,
                "require_single_decision_per_task": False,
                "require_task_directory_files": False,
                "enforce_sprint_scoped_dependencies": False,
            }
        },
        root=ph_data_root,
    )

    assert not any(i.get("code") == "task_type_missing" for i in issues), issues
    assert any(i.get("code") == "task_type_missing_legacy_session" for i in issues), issues
