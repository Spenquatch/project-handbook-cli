from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _write_task(
    *,
    root: Path,
    task_id: str,
    session: str,
    decision: str,
    task_type: str | None,
    steps_md: str,
    validation_md: str,
    extra_task_yaml_lines: list[str] | None = None,
) -> None:
    tasks_dir = root / ".project-handbook" / "sprints" / "current" / "tasks"
    task_dir = tasks_dir / f"{task_id}-t"
    task_dir.mkdir(parents=True, exist_ok=True)

    yaml_lines = [
        f"id: {task_id}",
        "title: Title",
        "owner: @a",
        "lane: ops",
        "feature: f",
        f"decision: {decision}",
        f"session: {session}",
        "story_points: 1",
        "depends_on: []",
    ]
    if task_type is not None:
        yaml_lines.insert(7, f"task_type: {task_type}")
    if extra_task_yaml_lines:
        yaml_lines.extend(extra_task_yaml_lines)

    (task_dir / "task.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    readme = "\n".join(
        [
            "---",
            f"task_id: {task_id}",
            f"session: {session}",
            "feature: f",
            "---",
            "",
            f"# {task_id} - Title",
            "",
            f"Evidence: status/evidence/{task_id}/",
            "",
        ]
    )
    (task_dir / "README.md").write_text(readme, encoding="utf-8")

    (task_dir / "steps.md").write_text(steps_md, encoding="utf-8")

    commands = "\n".join(
        [
            "# Commands",
            "",
            f"- Write evidence to `status/evidence/{task_id}/command-output.txt`",
            "",
        ]
    )
    (task_dir / "commands.md").write_text(commands, encoding="utf-8")

    checklist = "\n".join(["# Checklist", "", "- [ ] One item", ""])
    (task_dir / "checklist.md").write_text(checklist, encoding="utf-8")

    (task_dir / "validation.md").write_text(validation_md, encoding="utf-8")

    (task_dir / "references.md").write_text("# References\n\n- None\n", encoding="utf-8")


def _write_passing_sprint_gate_task(*, root: Path, task_id: str = "TASK-000") -> None:
    _write_task(
        root=root,
        task_id=task_id,
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=[f"evidence_dir: status/evidence/{task_id}/"],
        steps_md="# Steps\n\n- Run the gate checks\n",
        validation_md=(
            "# Validation\n\n"
            "Sprint Goal: Ensure the sprint is closeable\n"
            "Exit criteria: All checks pass\n\n"
            "- Evidence lives in `status/evidence/`\n"
            f"- Expect `status/evidence/{task_id}/secret-scan.txt`\n"
            "- Include `pre-exec-lint.txt`\n"
            "- Sprint plan: `sprints/current/plan.md`\n"
        ),
    )


def test_pre_exec_lint_defaults_task_type_for_legacy_session(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_passing_sprint_gate_task(root=tmp_path)
    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="task-execution",
        decision="ADR-0001",
        task_type=None,
        steps_md="# Steps\n\n- Run the command\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 0, lint.stdout


def test_pre_exec_lint_enforces_task_type_session_mapping(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="task-execution",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-001/"],
        steps_md="# Steps\n\n- Run the command\n",
        validation_md=(
            "# Validation\n\n"
            "Sprint Goal: goal\n"
            "Exit criteria: criteria\n\n"
            "- Evidence lives in `status/evidence/`\n"
            "- Sprint plan: `sprints/current/plan.md`\n"
            "- Include `secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "task_type/session mismatch" in lint.stdout


def test_pre_exec_lint_sprint_gate_requires_markers(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-001/"],
        steps_md="# Steps\n\n- Run the command\n",
        validation_md=(
            "# Validation\n\n"
            "Exit criteria: criteria\n\n"
            "- Evidence lives in `status/evidence/`\n"
            "- Sprint plan: `sprints/current/plan.md`\n"
            "- Include `secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "sprint-gate validation.md missing required marker: 'Sprint Goal:'" in lint.stdout


def test_pre_exec_lint_task_docs_deep_dive_forbids_impl_words(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="task-docs-deep-dive",
        decision="DR-0001",
        task_type="task-docs-deep-dive",
        steps_md="# Steps\n\n- Deploy the doc updates\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "task-docs-deep-dive steps.md contains forbidden implementation word" in lint.stdout


def test_pre_exec_lint_feature_research_planning_requires_headings(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="feature-research-planning",
        decision="DR-0001",
        task_type="feature-research-planning",
        steps_md="# Steps\n\n## Execution tasks to create\n\n- Task 1\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "feature-research-planning steps.md missing required heading line exactly" in lint.stdout


def test_pre_exec_lint_defaults_task_type_for_legacy_research_discovery_session(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_passing_sprint_gate_task(root=tmp_path)
    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="research-discovery",
        decision="DR-0001",
        task_type=None,
        steps_md="# Steps\n\n- Create DR-0001\n- Document Option A\n- Document Option B\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 0, lint.stdout


def test_pre_exec_lint_research_discovery_requires_dr_artifact_and_options(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="research-discovery",
        decision="DR-0001",
        task_type="research-discovery",
        steps_md="# Steps\n\n- Investigate the problem\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "research-discovery task does not clearly produce a Decision Register (DR-XXXX) artefact" in lint.stdout
    assert "research-discovery task must explicitly require exactly two options (Option A / Option B)" in lint.stdout


def test_pre_exec_lint_task_execution_forbids_decision_register_language(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="task-execution",
        decision="ADR-0001",
        task_type="implementation",
        steps_md="# Steps\n\n- Update Decision Register DR-0001 with findings\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "task-execution task contains Decision Register language" in lint.stdout


def test_pre_exec_lint_fails_when_sprint_missing_sprint_gate_task(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="task-execution",
        decision="ADR-0001",
        task_type="implementation",
        steps_md="# Steps\n\n- Run the command\n",
        validation_md=(
            "# Validation\n\n"
            "- Expect `secret-scan.txt` under `status/evidence/TASK-001/secret-scan.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "Current sprint is missing a required sprint gate task (task_type: sprint-gate)" in lint.stdout


def test_pre_exec_lint_sprint_gate_requires_explicit_sprint_goal_statement(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-001/"],
        steps_md="# Steps\n\n- Run the gate checks\n",
        validation_md=(
            "# Validation\n\n"
            "Sprint Goal: TBD\n"
            "Exit criteria: criteria\n\n"
            "- Evidence lives in `status/evidence/`\n"
            "- Include `secret-scan.txt`\n"
            "- Include `pre-exec-lint.txt`\n"
            "- Sprint plan: `sprints/current/plan.md`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "must state an explicit sprint goal" in lint.stdout


def test_pre_exec_lint_sprint_gate_requires_additional_evidence_artifact(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-001/"],
        steps_md="# Steps\n\n- Run the gate checks\n",
        validation_md=(
            "# Validation\n\n"
            "Sprint Goal: Ensure the sprint is closeable\n"
            "Exit criteria: criteria\n\n"
            "- Evidence lives in `status/evidence/`\n"
            "- Include `secret-scan.txt`\n"
            "- Sprint plan: `sprints/current/plan.md`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "must list at least one additional evidence artifact besides secret-scan.txt" in lint.stdout


def test_pre_exec_lint_sprint_gate_requires_task_yaml_evidence_prefix(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=[],
        steps_md="# Steps\n\n- Run the gate checks\n",
        validation_md=(
            "# Validation\n\n"
            "Sprint Goal: Ensure the sprint is closeable\n"
            "Exit criteria: All checks pass\n\n"
            "- Evidence lives in `status/evidence/`\n"
            "- Include `secret-scan.txt`\n"
            "- Include `pre-exec-lint.txt`\n"
            "- Sprint plan: `sprints/current/plan.md`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "sprint-gate task.yaml must mention evidence root prefix 'status/evidence/'" in lint.stdout


def test_pre_exec_lint_sprint_gate_requires_sprint_plan_reference(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan"], cwd=tmp_path).returncode == 0

    _write_task(
        root=tmp_path,
        task_id="TASK-001",
        session="sprint-gate",
        decision="ADR-0001",
        task_type="sprint-gate",
        extra_task_yaml_lines=["evidence_dir: status/evidence/TASK-001/"],
        steps_md="# Steps\n\n- Run the gate checks\n",
        validation_md=(
            "# Validation\n\n"
            "Sprint Goal: Ensure the sprint is closeable\n"
            "Exit criteria: All checks pass\n\n"
            "- Evidence lives in `status/evidence/`\n"
            "- Include `secret-scan.txt`\n"
            "- Include `pre-exec-lint.txt`\n"
        ),
    )

    lint = _run(["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "sprint-gate validation.md must reference the sprint plan" in lint.stdout
