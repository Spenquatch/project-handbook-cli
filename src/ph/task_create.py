from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from .clock import today as clock_today
from .context import Context


def slugify(value: str, *, max_len: int = 80) -> str:
    import re

    raw = (value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    if not raw:
        raw = "task"
    return raw[:max_len].rstrip("-") or "task"


def _read_head(path: Path, *, max_lines: int = 80) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            lines: list[str] = []
            for _ in range(max_lines):
                line = handle.readline()
                if not line:
                    break
                lines.append(line)
            return "".join(lines)
    except Exception:
        return ""


def _find_markdown_with_frontmatter_id(folder: Path, decision_id: str) -> Path | None:
    if not folder.exists():
        return None
    needle = f"id: {decision_id}"
    for candidate in sorted(folder.glob("*.md")):
        head = _read_head(candidate, max_lines=120)
        if needle in head:
            return candidate
    return None


def _find_markdown_with_heading_id(folder: Path, decision_id: str) -> Path | None:
    import re

    if not folder.exists():
        return None
    pattern = re.compile(rf"^###\\s+{re.escape(decision_id)}\\b", re.MULTILINE)
    for candidate in sorted(folder.glob("*.md")):
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            return candidate
    return None


def resolve_decision_doc(*, ph_data_root: Path, decision_id: str, feature: str) -> Path | None:
    decision_id = (decision_id or "").strip()
    feature = (feature or "").strip()
    if not decision_id:
        return None

    if decision_id.startswith("ADR-"):
        return _find_markdown_with_frontmatter_id(ph_data_root / "adr", decision_id)

    if decision_id.startswith("FDR-"):
        if feature:
            found = _find_markdown_with_frontmatter_id(ph_data_root / "features" / feature / "fdr", decision_id)
            if found:
                return found
        for feature_dir in sorted((ph_data_root / "features").glob("*")):
            if not feature_dir.is_dir() or feature_dir.name == "implemented":
                continue
            found = _find_markdown_with_frontmatter_id(feature_dir / "fdr", decision_id)
            if found:
                return found
        return None

    if decision_id.startswith("DR-"):
        if feature:
            found = _find_markdown_with_heading_id(
                ph_data_root / "features" / feature / "decision-register", decision_id
            )
            if found:
                return found
        found = _find_markdown_with_heading_id(ph_data_root / "decision-register", decision_id)
        if found:
            return found
        for feature_dir in sorted((ph_data_root / "features").glob("*")):
            if not feature_dir.is_dir() or feature_dir.name == "implemented":
                continue
            found = _find_markdown_with_heading_id(feature_dir / "decision-register", decision_id)
            if found:
                return found
        return None

    return None


def relative_markdown_link(*, from_dir: Path, target: Path) -> str:
    rel = os.path.relpath(str(target), str(from_dir))
    return rel.replace(os.sep, "/")


def _feature_doc_links(*, ph_data_root: Path, task_dir: Path, feature: str) -> tuple[str, str]:
    overview = ph_data_root / "features" / feature / "overview.md"
    architecture = ph_data_root / "features" / feature / "architecture" / "ARCHITECTURE.md"
    return (
        relative_markdown_link(from_dir=task_dir, target=overview),
        relative_markdown_link(from_dir=task_dir, target=architecture),
    )


def _load_validation_rules(*, ph_root: Path) -> dict[str, Any]:
    rules_path = ph_root / "process" / "checks" / "validation_rules.json"
    try:
        if rules_path.exists():
            return json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _default_story_points(*, ph_root: Path) -> int:
    rules = _load_validation_rules(ph_root=ph_root)
    try:
        return int(rules.get("story_points", {}).get("default_story_points", 5))
    except Exception:
        return 5


def _task_lane_prefixes_for_system_scope(*, ph_root: Path) -> list[str]:
    config_path = ph_root / "process" / "automation" / "system_scope_config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rules = config.get("routing_rules", {})
    if not isinstance(rules, dict):
        return []
    prefixes = rules.get("task_lane_prefixes_for_system_scope", [])
    if not isinstance(prefixes, list):
        return []
    return [str(p) for p in prefixes if str(p)]


def is_system_scoped_lane(*, ph_root: Path, lane: str) -> bool:
    lane = str(lane)
    return any(lane.startswith(prefix) for prefix in _task_lane_prefixes_for_system_scope(ph_root=ph_root))


def _require_current_sprint_dir(*, ph_data_root: Path) -> Path | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return resolved if resolved.exists() else None


def _get_next_task_id(*, sprint_dir: Path) -> str:
    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        return "TASK-001"

    max_num = 0
    for task_dir in tasks_dir.iterdir():
        if task_dir.is_dir() and task_dir.name.startswith("TASK-"):
            try:
                num_part = task_dir.name.split("-")[1]
                max_num = max(max_num, int(num_part))
            except Exception:
                continue

    return f"TASK-{max_num + 1:03d}"


def _scope_prefix_for_ph_command(*, ctx: Context) -> str:
    return "ph --scope system" if ctx.scope == "system" else "ph"


def _task_cd_path_for_scope(*, ctx: Context, task_dir_name: str) -> str:
    if ctx.scope == "system":
        return f".project-handbook/system/sprints/current/tasks/{task_dir_name}/"
    return f"sprints/current/tasks/{task_dir_name}/"


def run_task_create(
    *,
    ph_root: Path,
    ctx: Context,
    title: str,
    feature: str,
    decision: str,
    points: int | None,
    owner: str,
    prio: str,
    lane: str | None,
    session: str,
    env: dict[str, str],
) -> int:
    sprint_dir = _require_current_sprint_dir(ph_data_root=ctx.ph_data_root)
    if sprint_dir is None:
        print("❌ No current sprint found. Run 'ph sprint plan' first.")
        return 1

    if lane and ctx.scope == "project" and is_system_scoped_lane(ph_root=ph_root, lane=lane):
        print("Use: ph --scope system task create ...")
        return 1

    story_points = int(points) if points is not None else _default_story_points(ph_root=ph_root)

    task_id = _get_next_task_id(sprint_dir=sprint_dir)
    task_slug = slugify(title)
    task_dir_name = f"{task_id}-{task_slug}"
    task_dir = sprint_dir / "tasks" / task_dir_name

    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "source").mkdir(exist_ok=True)

    today = clock_today(env=env)
    due_date = today + dt.timedelta(days=7)

    lane_line = f"lane: {lane}\n" if lane else ""
    session_line = f"session: {session}\n" if session else ""

    task_yaml = (
        f"id: {task_id}\n"
        f"title: {title}\n"
        f"feature: {feature}\n"
        f"{lane_line}"
        f"decision: {decision}\n"
        f"{session_line}"
        f"owner: {owner}\n"
        "status: todo\n"
        f"story_points: {story_points}\n"
        "depends_on: []\n"
        f"prio: {prio}\n"
        f"due: {due_date.strftime('%Y-%m-%d')}\n"
        "acceptance:\n"
        "  - Implementation complete and tested\n"
        "  - Code review passed\n"
        "  - Documentation updated\n"
        "links: []\n"
    )
    (task_dir / "task.yaml").write_text(task_yaml, encoding="utf-8")

    decision_doc = resolve_decision_doc(ph_data_root=ctx.ph_data_root, decision_id=decision, feature=feature)
    if decision_doc:
        decision_link = f"[{decision}]({relative_markdown_link(from_dir=task_dir, target=decision_doc)})"
    else:
        decision_link = f"`{decision}`"

    feature_overview_rel, feature_architecture_rel = _feature_doc_links(
        ph_data_root=ctx.ph_data_root, task_dir=task_dir, feature=feature
    )

    cd_path = _task_cd_path_for_scope(ctx=ctx, task_dir_name=task_dir_name)
    ph_cmd = _scope_prefix_for_ph_command(ctx=ctx)

    readme_content = "\n".join(
        [
            "---",
            f"title: Task {task_id} - {title}",
            "type: task",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            f"feature: {feature}",
            f"session: {session}",
            f"tags: [task, {feature}]",
            f"links: [{feature_overview_rel}]",
            "---",
            "",
            f"# Task {task_id}: {title}",
            "",
            "## Overview",
            f"**Feature**: [{feature}]({feature_overview_rel})",
            f"**Decision**: {decision_link}",
            f"**Story Points**: {story_points}",
            f"**Owner**: {owner}",
            f"**Lane**: {lane or '(unset)'}",
            f"**Session**: `{session}`",
            "",
            "## Agent Navigation Rules",
            '1. **Start work**: Update `task.yaml` status to "doing"',
            "2. **Read first**: `steps.md` for implementation sequence",
            "3. **Use commands**: Copy-paste from `commands.md`",
            "4. **Validate progress**: Follow `validation.md` guidelines",
            "5. **Check completion**: Use `checklist.md` before marking done",
            '6. **Update status**: Set to "review" when ready for review',
            "",
            "## Context & Background",
            f"This task implements the {decision_link} decision for the [{feature}] feature.",
            "",
            "## Quick Start",
            "```bash",
            "# Update status when starting",
            f"cd {cd_path}",
            "# Edit task.yaml: status: doing",
            "",
            "# Follow implementation",
            "cat steps.md              # Read implementation steps",
            "cat commands.md           # Copy-paste commands",
            "cat validation.md         # Validation approach",
            "```",
            "",
            "## Dependencies",
            "Review `task.yaml` for any `depends_on` tasks that must be completed first.",
            "",
            "## Acceptance Criteria",
            "See `task.yaml` acceptance section and `checklist.md` for completion requirements.",
            "",
        ]
    )
    (task_dir / "README.md").write_text(readme_content, encoding="utf-8")

    steps_content = "\n".join(
        [
            "---",
            f"title: {title} - Implementation Steps",
            "type: implementation",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            "tags: [implementation]",
            "links: []",
            "---",
            "",
            f"# Implementation Steps: {title}",
            "",
            "## Overview",
            "Detailed step-by-step implementation guide for this task.",
            "",
            "## Prerequisites",
            "- [ ] All dependent tasks completed (check task.yaml depends_on)",
            "- [ ] Development environment ready",
            "- [ ] Required permissions/access available",
            "",
            "## Step 1: Analysis & Planning",
            "**Estimated Time**: 1-2 hours",
            "",
            "### Actions",
            f"- [ ] Review feature requirements in features/{feature}/",
            f"- [ ] Read decision rationale in {decision_link}",
            "- [ ] Identify implementation approach",
            "- [ ] Plan testing strategy",
            "",
            "### Expected Outcome",
            "- Clear understanding of requirements",
            "- Implementation approach decided",
            "- Test plan outlined",
            "",
            "## Step 2: Core Implementation",
            "**Estimated Time**: 4-6 hours",
            "",
            "### Actions",
            "- [ ] Implement core functionality",
            "- [ ] Add error handling",
            "- [ ] Write unit tests",
            "- [ ] Update documentation",
            "",
            "### Expected Outcome",
            "- Core functionality working",
            "- Tests passing",
            "- Basic documentation updated",
            "",
            "## Step 3: Integration & Validation",
            "**Estimated Time**: 1-2 hours",
            "",
            "### Actions",
            "- [ ] Integration testing",
            "- [ ] Performance validation",
            "- [ ] Security review (if applicable)",
            "- [ ] Final documentation pass",
            "",
            "### Expected Outcome",
            "- All tests passing",
            "- Performance acceptable",
            "- Documentation complete",
            "- Ready for review",
            "",
            "## Notes",
            "- Update task.yaml status as you progress through steps",
            "- Document any blockers or decisions in daily status",
            "- Link any PRs/commits back to this task",
            "",
        ]
    )
    (task_dir / "steps.md").write_text(steps_content, encoding="utf-8")

    commands_content = "\n".join(
        [
            "---",
            f"title: {title} - Commands",
            "type: commands",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            "tags: [commands]",
            "links: []",
            "---",
            "",
            f"# Commands: {title}",
            "",
            "## Task Status Updates",
            "```bash",
            "# When starting work",
            f"cd {cd_path}",
            '# Edit task.yaml: change status from "todo" to "doing"',
            "",
            "# When ready for review",
            '# Edit task.yaml: change status to "review"',
            "",
            "# When complete",
            '# Edit task.yaml: change status to "done"',
            "```",
            "",
            "## Validation Commands",
            "```bash",
            "# Run validation",
            f"{ph_cmd} validate",
            "",
            "# Check sprint status",
            f"{ph_cmd} sprint status",
            "",
            "# Update daily status",
            f"{ph_cmd} daily generate",
            "```",
            "",
            "## Implementation Commands",
            "```bash",
            "# Add specific commands for this task here",
            "# Example:",
            "# npm install package-name",
            "# python3 -m pytest tests/",
            "# docker build -t app .",
            "```",
            "",
            "## Git Integration",
            "```bash",
            "# Commit with task reference",
            (
                f'git commit -m "feat: {title.lower()}\\n\\nImplements {task_id} for {feature} feature.\\n'
                f'Part of sprint: {sprint_dir.name}\\n\\nRefs: #{task_id}"'
            ),
            "",
            "# Link PR to task (in PR description)",
            f"# Closes #{task_id}",
            f"# Implements {decision}",
            "```",
            "",
            "## Quick Copy-Paste",
            "```bash",
            "# Most common commands for this task type",
            'echo "Add task-specific commands here"',
            "```",
            "",
        ]
    )
    (task_dir / "commands.md").write_text(commands_content, encoding="utf-8")

    checklist_content = "\n".join(
        [
            "---",
            f"title: {title} - Completion Checklist",
            "type: checklist",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            "tags: [checklist]",
            "links: []",
            "---",
            "",
            f"# Completion Checklist: {title}",
            "",
            "## Pre-Work",
            "- [ ] Confirm all `depends_on` tasks are `done`",
            "- [ ] Review `README.md`, `steps.md`, `commands.md`",
            "- [ ] Align with the feature owner on acceptance criteria",
            "",
            "## During Execution",
            "- [ ] Capture implementation steps in `steps.md`",
            "- [ ] Record shell commands in `commands.md`",
            "- [ ] Document verification steps in `validation.md`",
            "- [ ] Keep this checklist updated as milestones are completed",
            "",
            "## Before Review",
            f"- [ ] Run `{ph_cmd} validate --quick`",
            "- [ ] Update daily status with progress/blockers",
            "- [ ] Gather artifacts (screenshots, logs, PR links)",
            "- [ ] Set status to `review` via `ph task status`",
            "",
            "## After Completion",
            "- [ ] Peer review approved and merged",
            "- [ ] Update owning feature docs/changelog if needed",
            "- [ ] Move status to `done` with `ph task status`",
            "- [ ] Capture learnings for the sprint retrospective",
            "",
        ]
    )
    (task_dir / "checklist.md").write_text(checklist_content, encoding="utf-8")

    validation_content = "\n".join(
        [
            "---",
            f"title: {title} - Validation Guide",
            "type: validation",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            "tags: [validation]",
            "links: []",
            "---",
            "",
            f"# Validation Guide: {title}",
            "",
            "## Automated Validation",
            "```bash",
            f"{ph_cmd} validate",
            f"{ph_cmd} sprint status",
            "```",
            "",
            "## Manual Validation (Must Be Task-Specific)",
            (
                "This file must be updated during sprint planning so an execution agent can validate "
                "without inventing steps."
            ),
            "",
            "Before the task is marked `review`, add:",
            "- exact copy/paste command(s),",
            "- exact pass/fail success criteria,",
            f"- exact evidence file list (under `status/evidence/{task_id}/`).",
            "",
            "## Sign-off",
            "- [ ] All validation steps completed",
            "- [ ] Evidence documented above",
            '- [ ] Ready to mark task as "done"',
            "",
        ]
    )
    (task_dir / "validation.md").write_text(validation_content, encoding="utf-8")

    references_content = "\n".join(
        [
            "---",
            f"title: {title} - References",
            "type: references",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            "tags: [references]",
            "links: []",
            "---",
            "",
            f"# References: {title}",
            "",
            "## Internal References",
            "",
            "### Decision Context",
            f"- **Decision**: {decision_link}",
            f"- **Feature**: [Feature overview]({feature_overview_rel})",
            f"- **Architecture**: [Feature architecture]({feature_architecture_rel})",
            "",
            "### Sprint Context",
            "- **Sprint Plan**: [Current sprint](../../plan.md)",
            "- **Sprint Tasks**: [All sprint tasks](../)",
            "- **Daily Progress**: [Daily status](../../daily/)",
            "",
            "## Notes",
            "Add concrete links here only when you discover resources during the task (no placeholders).",
            "",
        ]
    )
    (task_dir / "references.md").write_text(references_content, encoding="utf-8")

    print(f"✅ Created task directory: {task_dir.name}")
    print(f"📁 Location: {task_dir}")
    print("📝 Next steps:")
    print(f"   1. Edit {task_dir}/steps.md with implementation details")
    print(f"   2. Update {task_dir}/commands.md with specific commands")
    print(f"   3. Review checklist/logistics in {task_dir}/checklist.md")
    print(f"   4. Run '{ph_cmd} validate --quick' before pushing changes")
    print("   5. Set status to 'doing' when starting work")

    if ctx.scope == "system":
        print("Next steps:")
        print(
            "  - Open .project-handbook/system/sprints/current/tasks/ for the new directory, "
            "update steps.md + commands.md"
        )
        print("  - Set status to 'doing' when work starts and log progress in checklist.md")
        print("  - Run 'ph --scope system validate --quick' once initial scaffolding is filled in")
    else:
        print("Next steps:")
        print("  - Open sprints/current/tasks/ for the new directory, update steps.md + commands.md")
        print("  - Set status to 'doing' when work starts and log progress in checklist.md")
        print("  - Run 'ph validate --quick' once initial scaffolding is filled in")

    return 0
