from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from .clock import today as clock_today
from .context import Context
from .release import get_current_release
from .shell_quote import shell_quote


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


def _load_validation_rules(*, ph_project_root: Path) -> dict[str, Any]:
    rules_path = ph_project_root / "process" / "checks" / "validation_rules.json"
    try:
        if rules_path.exists():
            return json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _default_story_points(*, ph_project_root: Path) -> int:
    rules = _load_validation_rules(ph_project_root=ph_project_root)
    try:
        return int(rules.get("story_points", {}).get("default_story_points", 5))
    except Exception:
        return 5


def _system_scope_enforcement_enabled(*, ph_project_root: Path) -> bool:
    rules = _load_validation_rules(ph_project_root=ph_project_root)
    enforcement = rules.get("system_scope_enforcement")
    if not isinstance(enforcement, dict):
        return False
    return enforcement.get("enabled") is True


def _task_lane_prefixes_for_system_scope(*, ph_project_root: Path) -> list[str]:
    config_path = ph_project_root / "process" / "automation" / "system_scope_config.json"
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


def is_system_scoped_lane(*, ph_project_root: Path, lane: str) -> bool:
    lane = str(lane)
    return any(
        lane.startswith(prefix) for prefix in _task_lane_prefixes_for_system_scope(ph_project_root=ph_project_root)
    )


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
    return f".project-handbook/sprints/current/tasks/{task_dir_name}/"


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
    session_was_provided: bool = True,
    task_type: str | None = None,
    release: str | None = None,
    gate: bool = False,
    env: dict[str, str],
) -> int:
    sprint_dir = _require_current_sprint_dir(ph_data_root=ctx.ph_data_root)
    if sprint_dir is None:
        print("❌ No current sprint found. Run 'ph sprint plan' first.")
        return 1

    if (
        lane
        and ctx.scope == "project"
        and _system_scope_enforcement_enabled(ph_project_root=ctx.ph_project_root)
        and is_system_scoped_lane(ph_project_root=ctx.ph_project_root, lane=lane)
    ):
        print("Use: ph --scope system task create ...")
        return 1

    TASK_TYPE_TO_SESSION: dict[str, str] = {
        "implementation": "task-execution",
        "research-discovery": "research-discovery",
        "sprint-gate": "sprint-gate",
        "feature-research-planning": "feature-research-planning",
        "task-docs-deep-dive": "task-docs-deep-dive",
    }
    SESSION_TO_TASK_TYPE: dict[str, str] = {v: k for k, v in TASK_TYPE_TO_SESSION.items()}
    DEFAULT_TASK_TYPE = "implementation"
    DEFAULT_SESSION = "task-execution"

    normalized_task_type = (str(task_type).strip().lower() if task_type is not None else "") or None
    normalized_session = (str(session).strip() if session is not None else "").strip()

    if normalized_task_type:
        if normalized_task_type not in TASK_TYPE_TO_SESSION:
            allowed = ", ".join(sorted(TASK_TYPE_TO_SESSION.keys()))
            print(f"❌ Unknown task type '{normalized_task_type}'. Allowed: {allowed}")
            return 2
        mapped = TASK_TYPE_TO_SESSION[normalized_task_type]
        if session_was_provided and normalized_session and normalized_session != mapped:
            print(
                "❌ session/task_type mismatch.\n"
                f"  task_type: {normalized_task_type}\n"
                f"  session: {normalized_session}\n"
                f"  expected session for type: {mapped}"
            )
            return 1
        effective_task_type = normalized_task_type
        effective_session = mapped
    else:
        effective_session = normalized_session or DEFAULT_SESSION
        if session_was_provided and effective_session:
            effective_task_type = SESSION_TO_TASK_TYPE.get(effective_session, DEFAULT_TASK_TYPE)
        else:
            effective_task_type = DEFAULT_TASK_TYPE
            effective_session = DEFAULT_SESSION

    TASK_TYPE_TO_DEFAULT_LANE: dict[str, str] = {
        "sprint-gate": "ops/gates",
        "research-discovery": "product/research",
        "feature-research-planning": "product/research",
        "task-docs-deep-dive": "docs/quality",
    }
    effective_lane = lane
    if not effective_lane and effective_task_type in TASK_TYPE_TO_DEFAULT_LANE:
        effective_lane = TASK_TYPE_TO_DEFAULT_LANE[effective_task_type]

    def acceptance_items_for(task_type_value: str, *, task_id_value: str) -> list[str]:
        if task_type_value == "sprint-gate":
            return [
                "Sprint Goal and exit criteria captured in validation.md",
                "Automated validation complete (include secret-scan.txt evidence)",
                f"Evidence recorded under status/evidence/{task_id_value}/",
            ]
        if task_type_value == "research-discovery":
            return [
                "Decision Register entry (DR-XXXX) created/updated with recommendation",
                "Exactly two options documented (Option A / Option B)",
                "Follow-on execution tasks created with unambiguous scope",
            ]
        if task_type_value == "feature-research-planning":
            return [
                "Research plan written with explicit deliverables and timebox",
                "Contract/spec updates captured (as needed)",
                "Execution tasks to create enumerated with titles + owners",
            ]
        if task_type_value == "task-docs-deep-dive":
            return [
                "Task docs updated to be deterministic (no TBD/TODO/ambiguity)",
                "steps.md and validation.md avoid implementation language",
                "Validation steps and evidence paths made explicit",
            ]
        return [
            "Implementation complete and tested",
            "Code review passed",
            "Documentation updated",
        ]

    story_points = int(points) if points is not None else _default_story_points(ph_project_root=ctx.ph_project_root)

    task_id = _get_next_task_id(sprint_dir=sprint_dir)
    task_slug = slugify(title)
    task_dir_name = f"{task_id}-{task_slug}"
    task_dir = sprint_dir / "tasks" / task_dir_name

    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "source").mkdir(exist_ok=True)

    today = clock_today(env=env)
    due_date = today + dt.timedelta(days=7)

    normalized_release: str | None = None
    if release and str(release).strip().lower() not in {"null", "none"}:
        candidate = str(release).strip()
        if candidate.lower() == "current":
            current = get_current_release(ph_root=ctx.ph_project_root)
            if not current:
                print("⚠️  release=current requested but no current release is set; leaving task release=null")
                normalized_release = None
            else:
                normalized_release = str(current)
        else:
            normalized_release = candidate if candidate.startswith("v") else f"v{candidate}"

    release_line = f"release: {normalized_release}\n" if normalized_release else "release: null\n"
    release_gate_line = f"release_gate: {'true' if gate else 'false'}\n"

    lane_line = f"lane: {effective_lane}\n" if effective_lane else ""
    session_line = f"session: {effective_session}\n" if effective_session else ""
    task_type_line = f"task_type: {effective_task_type}\n"

    acceptance_lines = "\n".join(
        [f"  - {item}" for item in acceptance_items_for(effective_task_type, task_id_value=task_id)]
    )

    task_yaml = f"""id: {task_id}
title: {title}
feature: {feature}
{lane_line}decision: {decision}
{session_line}{task_type_line}owner: {owner}
status: todo
story_points: {story_points}
depends_on: []
prio: {prio}
due: {due_date.strftime("%Y-%m-%d")}
{release_line}{release_gate_line}acceptance:
{acceptance_lines}
links: []
"""
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
    evidence_rel = (
        f".project-handbook/status/evidence/{task_id}"
        if ctx.scope == "project"
        else f".project-handbook/system/status/evidence/{task_id}"
    )

    readme_content = "\n".join(
        [
            "---",
            f"title: Task {task_id} - {title}",
            "type: task",
            f"date: {today.strftime('%Y-%m-%d')}",
            f"task_id: {task_id}",
            f"feature: {feature}",
            f"session: {effective_session}",
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
            f"**Lane**: {effective_lane or '(unset)'}",
            f"**Session**: `{effective_session}`",
            f"**Release**: {normalized_release or '(none)'}",
            f"**Release Gate**: `{str(gate).lower()}`",
            "",
            "## Agent Navigation Rules",
            f"1. **Start work**: Run `{ph_cmd} task status --id {task_id} --status doing`",
            "2. **Read first**: `steps.md` for implementation sequence",
            "3. **Use commands**: Copy-paste from `commands.md`",
            "4. **Validate progress**: Follow `validation.md` guidelines",
            "5. **Check completion**: Use `checklist.md` before marking done",
            f"6. **Update status**: Run `{ph_cmd} task status --id {task_id} --status review` when ready for review",
            "",
            "## Context & Background",
            f"This task implements the {decision_link} decision for the [{feature}] feature.",
            "",
            "## Quick Start",
            "```bash",
            "# Update status when starting",
            f"cd {cd_path}",
            f"{ph_cmd} task status --id {task_id} --status doing",
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

    if effective_task_type == "feature-research-planning":
        steps_content = "\n".join(
            [
                "---",
                f"title: {title} - Research Planning Steps",
                "type: planning",
                f"date: {today.strftime('%Y-%m-%d')}",
                f"task_id: {task_id}",
                "tags: [planning, research]",
                "links: []",
                "---",
                "",
                f"# Research Planning Steps: {title}",
                "",
                "## Overview",
                "Produce a crisp research plan and the artifacts needed to turn outcomes into execution tasks.",
                "",
                "## Contract updates",
                "- [ ] Identify any contract/spec documents that must change",
                "- [ ] Record concrete updates with links and exact wording",
                "",
                "## Execution tasks to create",
                "- [ ] List the execution tasks that will be created after this planning completes",
                "- [ ] Include titles, owners, and expected validations/evidence paths",
                "",
            ]
        )
    elif effective_task_type == "task-docs-deep-dive":
        steps_content = "\n".join(
            [
                "---",
                f"title: {title} - Task Docs Deep Dive",
                "type: planning",
                f"date: {today.strftime('%Y-%m-%d')}",
                f"task_id: {task_id}",
                "tags: [docs, planning]",
                "links: []",
                "---",
                "",
                f"# Task Docs Deep Dive: {title}",
                "",
                "## Overview",
                "Improve task docs so they are deterministic and executable without guesswork.",
                "",
                "## Checklist",
                "- [ ] README.md: exact goal + scope boundaries",
                "- [ ] steps.md: numbered, atomic steps with concrete file paths/commands",
                "- [ ] commands.md: copy/paste runnable commands",
                "- [ ] checklist.md: binary checkboxes, not prose",
                "- [ ] validation.md: explicit validations and evidence paths",
                "",
            ]
        )
    elif effective_task_type == "research-discovery":
        steps_content = "\n".join(
            [
                "---",
                f"title: {title} - Research/Discovery Steps",
                "type: discovery",
                f"date: {today.strftime('%Y-%m-%d')}",
                f"task_id: {task_id}",
                "tags: [research, discovery]",
                "links: []",
                "---",
                "",
                f"# Research/Discovery Steps: {title}",
                "",
                "## Overview",
                "Deliverable: a Decision Register entry (DR-XXXX) with exactly two options and a recommendation.",
                "",
                "## Steps",
                "- [ ] Capture problem statement + success criteria",
                "- [ ] Document Option A and Option B",
                "- [ ] Recommend one option with rationale",
                "- [ ] Create follow-on execution tasks with no ambiguity",
                "",
            ]
        )
    elif effective_task_type == "sprint-gate":
        steps_content = "\n".join(
            [
                "---",
                f"title: {title} - Sprint Gate Steps",
                "type: gate",
                f"date: {today.strftime('%Y-%m-%d')}",
                f"task_id: {task_id}",
                "tags: [sprint, gate]",
                "links: []",
                "---",
                "",
                f"# Sprint Gate Steps: {title}",
                "",
                "## Overview",
                "Define a sprint goal and deterministic exit criteria, then record evidence under status/evidence/.",
                "",
                "## Steps",
                "- [ ] Update validation.md with Sprint Goal and Exit criteria",
                f"- [ ] Record evidence under status/evidence/{task_id}/",
                "- [ ] Include secret-scan.txt evidence (or reference it if produced by automation)",
                "",
            ]
        )
    else:
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
                (
                    f"- Update task status via `{ph_cmd} task status --id {task_id} --status "
                    "<todo|doing|review|done|blocked>`"
                ),
                "- Document any blockers or decisions in daily status",
                "- Link any PRs/commits back to this task",
                "",
            ]
        )
    (task_dir / "steps.md").write_text(steps_content, encoding="utf-8")

    if ctx.scope == "project":
        commands_content = f"""---
title: {title} - Commands
type: commands
date: {today.strftime("%Y-%m-%d")}
task_id: {task_id}
tags: [commands]
links: []
---

# Commands: {title}

## Task Status Updates
```bash
# When starting work
cd {cd_path}
{ph_cmd} task status --id {task_id} --status doing

# When ready for review
{ph_cmd} task status --id {task_id} --status review

# When complete
{ph_cmd} task status --id {task_id} --status done
```

## Evidence Paths (Avoid Relative Outputs)
When a tool runs from another working directory (e.g. `pnpm -C ...`), relative `--output` paths can land in the
wrong place. Prefer absolute evidence paths:
```bash
PH_ROOT="$(git rev-parse --show-toplevel)"
EVID_REL="{evidence_rel}"
EVID_ABS="$PH_ROOT/$EVID_REL"
mkdir -p "$EVID_ABS"

# Example usage:
# pnpm -C apps/web exec playwright test --output "$EVID_ABS/playwright"
```

## Validation Commands
```bash
# Run validation
ph validate

# Check sprint status
ph sprint status

# Update daily status
ph daily generate
```

## Implementation Commands
```bash
# Add specific commands for this task here
# Example:
# npm install package-name
# python3 -m pytest tests/
# docker build -t app .
```

## Git Integration
```bash
# Commit with task reference
git commit -m "feat: {title.lower()}

Implements {task_id} for {feature} feature.
Part of sprint: {sprint_dir.name}

Refs: #{task_id}"

# Link PR to task (in PR description)
# Closes #{task_id}
# Implements {decision}
```

## Quick Copy-Paste
```bash
# Most common commands for this task type
echo "Add task-specific commands here"
```
"""
    else:
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
                f"{ph_cmd} task status --id {task_id} --status doing",
                "",
                "# When ready for review",
                f"{ph_cmd} task status --id {task_id} --status review",
                "",
                "# When complete",
                f"{ph_cmd} task status --id {task_id} --status done",
                "```",
                "",
                "## Evidence Paths (Avoid Relative Outputs)",
                (
                    "When a tool runs from another working directory (e.g. `pnpm -C ...`), relative `--output` "
                    "paths can land in the wrong place. Prefer absolute evidence paths:"
                ),
                "```bash",
                'PH_ROOT="$(git rev-parse --show-toplevel)"',
                f'EVID_REL="{evidence_rel}"',
                'EVID_ABS="$PH_ROOT/$EVID_REL"',
                'mkdir -p "$EVID_ABS"',
                "",
                "# Example usage:",
                '# pnpm -C apps/web exec playwright test --output "$EVID_ABS/playwright"',
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

    if ctx.scope == "project":
        checklist_content = f"""---
title: {title} - Completion Checklist
type: checklist
date: {today.strftime("%Y-%m-%d")}
task_id: {task_id}
tags: [checklist]
links: []
---

# Completion Checklist: {title}

## Pre-Work
- [ ] Confirm all `depends_on` tasks are `done`
- [ ] Review `README.md`, `steps.md`, `commands.md`
- [ ] Align with the feature owner on acceptance criteria

## During Execution
- [ ] Capture implementation steps in `steps.md`
- [ ] Record shell commands in `commands.md`
- [ ] Document verification steps in `validation.md`
- [ ] Keep this checklist updated as milestones are completed

## Before Review
- [ ] Run `ph validate --quick`
- [ ] Update daily status with progress/blockers
- [ ] Gather artifacts (screenshots, logs, PR links)
- [ ] Set status to `review` via `ph task status --id {task_id} --status review`

## After Completion
- [ ] Peer review approved and merged
- [ ] Update owning feature docs/changelog if needed
- [ ] Move status to `done` with `ph task status --id {task_id} --status done`
- [ ] Capture learnings for the sprint retrospective
"""
    else:
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

    def default_validation_lines(*, scope_cmd: str, evidence_prefix: str) -> list[str]:
        return [
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
            f"{scope_cmd} validate",
            f"{scope_cmd} sprint status",
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
            f"- exact evidence file list (under `{evidence_prefix}{task_id}/`).",
            "",
            "## Sign-off",
            "- [ ] All validation steps completed",
            "- [ ] Evidence documented above",
            '- [ ] Ready to mark task as "done"' if ctx.scope == "project" else '- [ ] Ready to mark task as "done"',
            "",
        ]

    if ctx.scope == "project":
        scope_cmd = "ph"
        evidence_prefix = ".project-handbook/status/evidence/"
    else:
        scope_cmd = ph_cmd
        evidence_prefix = "status/evidence/"

    if effective_task_type == "sprint-gate":
        validation_content = "\n".join(
            [
                "---",
                f"title: {title} - Sprint Gate Validation",
                "type: validation",
                f"date: {today.strftime('%Y-%m-%d')}",
                f"task_id: {task_id}",
                "tags: [validation, sprint, gate]",
                "links: []",
                "---",
                "",
                f"# Sprint Gate Validation: {title}",
                "",
                "Sprint Goal:",
                "- <fill in>",
                "",
                "Exit criteria:",
                "- [ ] <fill in>",
                "",
                "## Evidence",
                f"- Evidence root: {evidence_prefix}{task_id}/",
                "- Include: secret-scan.txt",
                "",
                "## Sprint plan reference",
                "- See: ../../plan.md",
                "",
                "## Automated Validation",
                "```bash",
                f"{scope_cmd} validate",
                f"{scope_cmd} sprint status",
                "```",
                "",
            ]
        )
    else:
        validation_content = "\n".join(default_validation_lines(scope_cmd=scope_cmd, evidence_prefix=evidence_prefix))
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
    print(f"cd -- {shell_quote(task_dir)}")
    print("📝 Next steps:")
    print(f"   1. Edit {task_dir}/steps.md with implementation details")
    print(f"   2. Update {task_dir}/commands.md with specific commands")
    print(f"   3. Review checklist/logistics in {task_dir}/checklist.md")
    if ctx.scope == "project":
        print("   4. Run 'ph validate --quick' before pushing changes")
    else:
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
        print("  - Open .project-handbook/sprints/current/tasks/ for the new directory, update steps.md + commands.md")
        print("  - Set status to 'doing' when work starts and log progress in checklist.md")
        print("  - Run 'ph validate --quick' once initial scaffolding is filled in")

    return 0
