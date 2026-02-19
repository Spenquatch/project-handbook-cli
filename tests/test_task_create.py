from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path, *, routing_rules: dict | None = None) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )

    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    ph_data_root = config.parent
    (ph_data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    system_scope_config = {"routing_rules": routing_rules or {}}
    (ph_data_root / "process" / "automation" / "system_scope_config.json").write_text(
        __import__("json").dumps(system_scope_config), encoding="utf-8"
    )
    (ph_data_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _plan_sprint(*, ph_root: Path, scope: str) -> None:
    cmd = ["ph", "--root", str(ph_root)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0


def test_task_create_project_stdout_and_files_match_make_task_create(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _plan_sprint(ph_root=tmp_path, scope="project")

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "task",
            "create",
            "--title",
            "T",
            "--feature",
            "f",
            "--decision",
            "ADR-0000",
            "--points",
            "5",
            "--owner",
            "@a",
            "--prio",
            "P1",
            "--lane",
            "ops",
            "--session",
            "task-execution",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    task_dir = resolved / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks" / "TASK-002-t"

    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph task create --title T --feature f --decision ADR-0000 --points 5 --owner @a --prio P1 "
        "--lane ops --session task-execution\n"
        "\n"
        "✅ Created task directory: TASK-002-t\n"
        f"📁 Location: {task_dir}\n"
        f"cd -- {task_dir}\n"
        "📝 Next steps:\n"
        f"   1. Edit {task_dir}/steps.md with implementation details\n"
        f"   2. Update {task_dir}/commands.md with specific commands\n"
        f"   3. Review checklist/logistics in {task_dir}/checklist.md\n"
        "   4. Run 'ph validate --quick' before pushing changes\n"
        "   5. Set status to 'doing' when starting work\n"
        "Next steps:\n"
        "  - Open .project-handbook/sprints/current/tasks/ for the new directory, update steps.md + commands.md\n"
        "  - Set status to 'doing' when work starts and log progress in checklist.md\n"
        "  - Run 'ph validate --quick' once initial scaffolding is filled in\n"
    )
    assert result.stdout == expected_stdout

    assert task_dir.exists()
    expected_files = {
        "source",
        "task.yaml",
        "README.md",
        "steps.md",
        "commands.md",
        "checklist.md",
        "validation.md",
        "references.md",
    }
    assert expected_files.issubset({p.name for p in task_dir.iterdir()})

    assert (task_dir / "task.yaml").read_text(encoding="utf-8") == (
        "id: TASK-002\n"
        "title: T\n"
        "feature: f\n"
        "lane: ops\n"
        "decision: ADR-0000\n"
        "session: task-execution\n"
        "task_type: implementation\n"
        "owner: @a\n"
        "status: todo\n"
        "story_points: 5\n"
        "depends_on: []\n"
        "prio: P1\n"
        "due: 2099-01-08\n"
        "release: null\n"
        "release_gate: false\n"
        "acceptance:\n"
        "  - Implementation complete and tested\n"
        "  - Code review passed\n"
        "  - Documentation updated\n"
        "links: []\n"
    )

    assert (task_dir / "README.md").read_text(encoding="utf-8") == (
        "---\n"
        "title: Task TASK-002 - T\n"
        "type: task\n"
        "date: 2099-01-01\n"
        "task_id: TASK-002\n"
        "feature: f\n"
        "session: task-execution\n"
        "tags: [task, f]\n"
        "links: [../../../../../features/f/overview.md]\n"
        "---\n"
        "\n"
        "# Task TASK-002: T\n"
        "\n"
        "## Overview\n"
        "**Feature**: [f](../../../../../features/f/overview.md)\n"
        "**Decision**: `ADR-0000`\n"
        "**Story Points**: 5\n"
        "**Owner**: @a\n"
        "**Lane**: ops\n"
        "**Session**: `task-execution`\n"
        "**Release**: (none)\n"
        "**Release Gate**: `false`\n"
        "\n"
        "## Agent Navigation Rules\n"
        "1. **Start work**: Run `ph task status --id TASK-002 --status doing`\n"
        "2. **Read first**: `steps.md` for implementation sequence\n"
        "3. **Use commands**: Copy-paste from `commands.md`\n"
        "4. **Validate progress**: Follow `validation.md` guidelines\n"
        "5. **Check completion**: Use `checklist.md` before marking done\n"
        '6. **Update status**: Run `ph task status --id TASK-002 --status review` when ready for review\n'
        "\n"
        "## Context & Background\n"
        "This task implements the `ADR-0000` decision for the [f] feature.\n"
        "\n"
        "## Quick Start\n"
        "```bash\n"
        "# Update status when starting\n"
        "cd .project-handbook/sprints/current/tasks/TASK-002-t/\n"
        "ph task status --id TASK-002 --status doing\n"
        "\n"
        "# Follow implementation\n"
        "cat steps.md              # Read implementation steps\n"
        "cat commands.md           # Copy-paste commands\n"
        "cat validation.md         # Validation approach\n"
        "```\n"
        "\n"
        "## Dependencies\n"
        "Review `task.yaml` for any `depends_on` tasks that must be completed first.\n"
        "\n"
        "## Acceptance Criteria\n"
        "See `task.yaml` acceptance section and `checklist.md` for completion requirements.\n"
    )

    assert (task_dir / "checklist.md").read_text(encoding="utf-8") == (
        "---\n"
        "title: T - Completion Checklist\n"
        "type: checklist\n"
        "date: 2099-01-01\n"
        "task_id: TASK-002\n"
        "tags: [checklist]\n"
        "links: []\n"
        "---\n"
        "\n"
        "# Completion Checklist: T\n"
        "\n"
        "## Pre-Work\n"
        "- [ ] Confirm all `depends_on` tasks are `done`\n"
        "- [ ] Review `README.md`, `steps.md`, `commands.md`\n"
        "- [ ] Align with the feature owner on acceptance criteria\n"
        "\n"
        "## During Execution\n"
        "- [ ] Capture implementation steps in `steps.md`\n"
        "- [ ] Record shell commands in `commands.md`\n"
        "- [ ] Document verification steps in `validation.md`\n"
        "- [ ] Keep this checklist updated as milestones are completed\n"
        "\n"
        "## Before Review\n"
        "- [ ] Run `ph validate --quick`\n"
        "- [ ] Update daily status with progress/blockers\n"
        "- [ ] Gather artifacts (screenshots, logs, PR links)\n"
        "- [ ] Set status to `review` via `ph task status --id TASK-002 --status review`\n"
        "\n"
        "## After Completion\n"
        "- [ ] Peer review approved and merged\n"
        "- [ ] Update owning feature docs/changelog if needed\n"
        "- [ ] Move status to `done` with `ph task status --id TASK-002 --status done`\n"
        "- [ ] Capture learnings for the sprint retrospective\n"
    )

    assert (task_dir / "commands.md").read_text(encoding="utf-8") == (
        "---\n"
        "title: T - Commands\n"
        "type: commands\n"
        "date: 2099-01-01\n"
        "task_id: TASK-002\n"
        "tags: [commands]\n"
        "links: []\n"
        "---\n"
        "\n"
        "# Commands: T\n"
        "\n"
        "## Task Status Updates\n"
        "```bash\n"
        "# When starting work\n"
        "cd .project-handbook/sprints/current/tasks/TASK-002-t/\n"
        "ph task status --id TASK-002 --status doing\n"
        "\n"
        "# When ready for review\n"
        "ph task status --id TASK-002 --status review\n"
        "\n"
        "# When complete\n"
        "ph task status --id TASK-002 --status done\n"
        "```\n"
        "\n"
        "## Evidence Paths (Avoid Relative Outputs)\n"
        "When a tool runs from another working directory (e.g. `pnpm -C ...`), relative `--output` paths can land in "
        "the\n"
        "wrong place. Prefer absolute evidence paths:\n"
        "```bash\n"
        "PH_ROOT=\"$(git rev-parse --show-toplevel)\"\n"
        "EVID_REL=\".project-handbook/status/evidence/TASK-002\"\n"
        "EVID_ABS=\"$PH_ROOT/$EVID_REL\"\n"
        "mkdir -p \"$EVID_ABS\"\n"
        "\n"
        "# Example usage:\n"
        "# pnpm -C apps/web exec playwright test --output \"$EVID_ABS/playwright\"\n"
        "```\n"
        "\n"
        "## Validation Commands\n"
        "```bash\n"
        "# Run validation\n"
        "ph validate\n"
        "\n"
        "# Check sprint status\n"
        "ph sprint status\n"
        "\n"
        "# Update daily status\n"
        "ph daily generate\n"
        "```\n"
        "\n"
        "## Implementation Commands\n"
        "```bash\n"
        "# Add specific commands for this task here\n"
        "# Example:\n"
        "# npm install package-name\n"
        "# python3 -m pytest tests/\n"
        "# docker build -t app .\n"
        "```\n"
        "\n"
        "## Git Integration\n"
        "```bash\n"
        "# Commit with task reference\n"
        'git commit -m "feat: t\n'
        "\n"
        "Implements TASK-002 for f feature.\n"
        "Part of sprint: SPRINT-2099-01-01\n"
        "\n"
        'Refs: #TASK-002"\n'
        "\n"
        "# Link PR to task (in PR description)\n"
        "# Closes #TASK-002\n"
        "# Implements ADR-0000\n"
        "```\n"
        "\n"
        "## Quick Copy-Paste\n"
        "```bash\n"
        "# Most common commands for this task type\n"
        'echo "Add task-specific commands here"\n'
        "```\n"
    )

    assert (task_dir / "validation.md").read_text(encoding="utf-8") == (
        "---\n"
        "title: T - Validation Guide\n"
        "type: validation\n"
        "date: 2099-01-01\n"
        "task_id: TASK-002\n"
        "tags: [validation]\n"
        "links: []\n"
        "---\n"
        "\n"
        "# Validation Guide: T\n"
        "\n"
        "## Automated Validation\n"
        "```bash\n"
        "ph validate\n"
        "ph sprint status\n"
        "```\n"
        "\n"
        "## Manual Validation (Must Be Task-Specific)\n"
        "This file must be updated during sprint planning so an execution agent can validate without inventing steps.\n"
        "\n"
        "Before the task is marked `review`, add:\n"
        "- exact copy/paste command(s),\n"
        "- exact pass/fail success criteria,\n"
        "- exact evidence file list (under `.project-handbook/status/evidence/TASK-002/`).\n"
        "\n"
        "## Sign-off\n"
        "- [ ] All validation steps completed\n"
        "- [ ] Evidence documented above\n"
        '- [ ] Ready to mark task as "done"\n'
    )

    assert (task_dir / "references.md").read_text(encoding="utf-8") == (
        "---\n"
        "title: T - References\n"
        "type: references\n"
        "date: 2099-01-01\n"
        "task_id: TASK-002\n"
        "tags: [references]\n"
        "links: []\n"
        "---\n"
        "\n"
        "# References: T\n"
        "\n"
        "## Internal References\n"
        "\n"
        "### Decision Context\n"
        "- **Decision**: `ADR-0000`\n"
        "- **Feature**: [Feature overview](../../../../../features/f/overview.md)\n"
        "- **Architecture**: [Feature architecture](../../../../../features/f/architecture/ARCHITECTURE.md)\n"
        "\n"
        "### Sprint Context\n"
        "- **Sprint Plan**: [Current sprint](../../plan.md)\n"
        "- **Sprint Tasks**: [All sprint tasks](../)\n"
        "- **Daily Progress**: [Daily status](../../daily/)\n"
        "\n"
        "## Notes\n"
        "Add concrete links here only when you discover resources during the task (no placeholders).\n"
    )


def test_task_create_system_scope_prints_hint_block(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _plan_sprint(ph_root=tmp_path, scope="system")

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "task",
            "create",
            "--title",
            "T",
            "--feature",
            "f",
            "--decision",
            "ADR-0000",
            "--lane",
            "ops",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines()[-4:] == [
        "Next steps:",
        "  - Open .project-handbook/system/sprints/current/tasks/ for the new directory, update steps.md + commands.md",
        "  - Set status to 'doing' when work starts and log progress in checklist.md",
        "  - Run 'ph --scope system validate --quick' once initial scaffolding is filled in",
    ]


def test_task_create_guardrail_rejects_system_scoped_lanes_in_project_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path, routing_rules={"task_lane_prefixes_for_system_scope": ["handbook/"]})
    _plan_sprint(ph_root=tmp_path, scope="project")

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "task",
        "create",
        "--title",
        "T",
        "--feature",
        "f",
        "--decision",
        "ADR-0000",
        "--lane",
        "handbook/automation",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 1
    resolved = tmp_path.resolve()
    assert result.stdout == (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph task create --title T --feature f --decision ADR-0000 --lane handbook/automation\n"
        "\n"
        "Use: ph --scope system task create ...\n"
    )

    tasks_dir = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks"
    task_dirs = [p for p in tasks_dir.iterdir() if p.is_dir()]
    assert len(task_dirs) == 1
    assert "task_type: sprint-gate" in (task_dirs[0] / "task.yaml").read_text(encoding="utf-8")


def _write_minimal_dr_entry(*, ph_root: Path, dr_id: str, feature: str | None = None) -> None:
    ph_data_root = ph_root / ".project-handbook"
    if feature:
        dr_dir = ph_data_root / "features" / feature / "decision-register"
    else:
        dr_dir = ph_data_root / "decision-register"
    dr_dir.mkdir(parents=True, exist_ok=True)
    (dr_dir / f"{dr_id}.md").write_text(
        "\n".join(
            [
                "---",
                f"title: {dr_id}",
                "type: decision-register",
                "date: 2099-01-01",
                f"id: {dr_id}",
                "tags: [dr]",
                "links: []",
                "---",
                "",
                f"### {dr_id}",
                "",
                "Option A",
                "- A",
                "",
                "Option B",
                "- B",
                "",
                "Recommendation",
                "- A",
                "",
                "## Sources",
                "- URL: https://example.com",
                "  - Accessed: 2099-01-01",
                "  - Relevance: Fixture source",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_task_create_each_task_type_passes_validate_quick(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _plan_sprint(ph_root=tmp_path, scope="project")
    _write_minimal_dr_entry(ph_root=tmp_path, dr_id="DR-0000", feature="f")

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cases = [
        ("implementation", "ADR-0000"),
        ("research-discovery", "DR-0000"),
        ("sprint-gate", "ADR-0000"),
        ("feature-research-planning", "DR-0000"),
        ("task-docs-deep-dive", "DR-0000"),
    ]

    task_type_to_session = {
        "implementation": "task-execution",
        "research-discovery": "research-discovery",
        "sprint-gate": "sprint-gate",
        "feature-research-planning": "feature-research-planning",
        "task-docs-deep-dive": "task-docs-deep-dive",
    }

    for task_type, decision in cases:
        result = subprocess.run(
            [
                "ph",
                "--root",
                str(tmp_path),
                "--no-post-hook",
                "task",
                "create",
                "--title",
                f"T {task_type}",
                "--feature",
                "f",
                "--decision",
                decision,
                "--type",
                task_type,
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
        m = re.search(r"^📁 Location: (?P<path>.+)$", result.stdout, flags=re.MULTILINE)
        assert m is not None, result.stdout
        task_dir = Path(m.group("path"))
        task_yaml = (task_dir / "task.yaml").read_text(encoding="utf-8")
        assert f"task_type: {task_type}\n" in task_yaml
        assert f"session: {task_type_to_session[task_type]}\n" in task_yaml

    validate = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert validate.returncode == 0
