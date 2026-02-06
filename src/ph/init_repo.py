from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

DEFAULT_SCHEMA_VERSION = 1
DEFAULT_REPO_ROOT = "."
DEFAULT_REQUIRES_PH_VERSION = ">=0.0.1,<0.1.0"

_DEFAULT_GITIGNORE_LINES = (
    ".project-handbook/history.log",
    "process/sessions/logs/*",
    "!process/sessions/logs/.gitkeep",
    "status/exports",
    ".DS_Store",
)

_DEFAULT_LATEST_SESSION_SUMMARY = """---
title: Latest Session Summary
type: session-summary
date: {date}
tags: [sessions, summary]
links: []
---

# Latest Session Summary

No session summaries have been generated in this repository yet.

## How to Generate a Recap

Use the installed `ph` CLI:

```bash
ph end-session --log <path-to-rollout-jsonl>
```
"""

_DEFAULT_ONBOARDING_MD = """---
title: Project Handbook Onboarding
type: guide
date: {date}
tags: [onboarding, process]
links: [process/AI_AGENT_START_HERE.md]
---

# Welcome to the Project Handbook

This repository is the source of truth for planning, execution, and reporting.
Prefer using `ph` commands so the system remains deterministic and searchable.

## Start Here

1. Run the onboarding helper:
   ```bash
   ph onboarding
   ```
2. Use session prompts whenever you need a focused refresher:
   - `ph onboarding session sprint-planning`
   - `ph onboarding session task-execution`
   - `ph onboarding session research-discovery`
   - `ph onboarding session pre-execution-audit`
   - `ph onboarding session quality-gate`
3. Follow the playbooks:
   - `process/playbooks/sprint-planning.md`
   - `process/playbooks/sprint-closing.md`
   - `process/playbooks/daily-status.md`
   - `process/playbooks/release-planning.md`

## Required Habits

- Create/modify planning artifacts via `ph` commands first (sprints, tasks, releases, backlog, parking lot).
- Run `ph validate --quick` regularly so docs stay lint-clean.
"""

_DEFAULT_PROCESS_AGENT_GUIDE = """---
title: AI Agent Start Here
type: guide
date: {date}
tags: [agents, process]
links: []
---

# AI Agent Start Here

This handbook is designed to be safely operated by humans and agents.

## Non-destructive defaults

- Prefer planning commands first (sprints/releases/tasks) and follow printed next-step hints.
- Avoid overwriting existing content unless a command explicitly owns that file.

## Common commands

- `ph dashboard`
- `ph sprint plan` / `ph sprint status`
- `ph task create` / `ph task status`
- `ph release plan --activate` / `ph release status`
- `ph validate --quick`
"""

_DEFAULT_SESSION_TEMPLATES: dict[str, str] = {
    "sprint-planning": """---
title: Sprint Planning Session
type: prompt-template
mode: planning
tags: [sprint, planning]
---

You are facilitating sprint planning in the Project Handbook.

Rules:
1) Stay in planning mode; do not implement code unless instructed.
2) Use handbook automation (`ph ...`) to create/update sprints, tasks, releases, backlog, and parking lot items.
3) Eliminate ambiguity in execution tasks: no TBD/TODO, no open questions, and clear validation gates.
""",
    "task-execution": """---
title: Task Execution Session
type: prompt-template
mode: execution
tags: [task, execution]
---

You are executing a single sprint task.

Rules:
1) Keep scope tight to the task docs.
2) Record evidence under `status/evidence/<TASK-###>/`.
3) Keep task docs and `task.yaml` status up to date as you progress.
""",
    "research-discovery": """---
title: Research/Discovery Session
type: prompt-template
mode: discovery
tags: [research, discovery]
---

You are running a discovery task.

Rules:
1) The deliverable is a Decision Register entry (DR-XXXX) or ADR when appropriate.
2) Document exactly two options (Option A / Option B) and a recommendation.
3) Convert outcomes into execution tasks (task-execution) with no ambiguity.
""",
    "pre-execution-audit": """---
title: Pre-execution Audit
type: prompt-template
mode: gate
tags: [pre-exec, audit]
---

You are preparing to start sprint execution.

Steps:
1) Ensure a sprint is planned and a release is activated (if applicable).
2) Run `ph pre-exec audit` and capture the evidence bundle path.
3) Fix any lint findings before starting execution.
""",
    "quality-gate": """---
title: Quality Gate
type: prompt-template
mode: gate
tags: [quality]
---

You are running a quality gate before handoff or release.

Checklist:
- `ph validate`
- `ph status`
- Ensure tasks have explicit evidence + validation docs.
""",
    "release-planning": """---
title: Release Planning Session
type: prompt-template
mode: planning
tags: [release, planning]
---

You are coordinating a release.

Steps:
- Create a plan: `ph release plan --version next`
- Activate when ready: `ph release activate --release vX.Y.Z`
- Track progress: `ph release status` / `ph release progress`
""",
    "sprint-closing": """---
title: Sprint Closing Session
type: prompt-template
mode: closing
tags: [sprint, closing]
---

You are closing a sprint.

Steps:
- Ensure tasks are updated and evidence is captured.
- Run `ph sprint close` and archive as needed.
- Run `ph status` and update roadmap/releases.
""",
}

_DEFAULT_PLAYBOOKS: dict[str, str] = {
    "sprint-planning": """---
title: Sprint Planning Playbook
type: playbook
date: {date}
tags: [playbook, sprint, planning]
links: []
---

# Sprint Planning

Use `ph sprint plan`, then seed tasks with `ph task create`.
""",
    "sprint-closing": """---
title: Sprint Closing Playbook
type: playbook
date: {date}
tags: [playbook, sprint, closing]
links: []
---

# Sprint Closing

Run `ph sprint close`, update roadmap/releases, and run `ph status`.
""",
    "daily-status": """---
title: Daily Status Playbook
type: playbook
date: {date}
tags: [playbook, status, daily]
links: []
---

# Daily Status

Run `ph daily generate` and keep `status/daily/` current.
""",
    "release-planning": """---
title: Release Planning Playbook
type: playbook
date: {date}
tags: [playbook, release, planning]
links: []
---

# Release Planning

Use `ph release plan` then `ph release activate` to set `releases/current`.
""",
    "backlog-triage": """---
title: Backlog Triage Playbook
type: playbook
date: {date}
tags: [playbook, backlog, triage]
links: []
---

# Backlog Triage

Use `ph backlog list` and `ph backlog triage` for P0s.
""",
    "parking-lot-review": """---
title: Parking Lot Review Playbook
type: playbook
date: {date}
tags: [playbook, parking-lot, review]
links: []
---

# Parking Lot Review

Use `ph parking review` and promote items to roadmap when ready.
""",
    "research-discovery": """---
title: Research / Discovery Playbook
type: playbook
date: {date}
tags: [playbook, research, discovery]
links: []
---

# Research / Discovery

Discovery tasks should produce DR-XXXX entries and lead to execution tasks.
""",
    "roadmap-planning": """---
title: Roadmap Planning Playbook
type: playbook
date: {date}
tags: [playbook, roadmap, planning]
links: []
---

# Roadmap Planning

Update `roadmap/now-next-later.md` and validate links with `ph roadmap validate`.
""",
}

_DEFAULT_BACKLOG_INDEX = {
    "last_updated": None,
    "total_items": 0,
    "by_severity": {"P0": [], "P1": [], "P2": [], "P3": [], "P4": []},
    "by_category": {"bugs": [], "wildcards": [], "work-items": []},
    "items": [],
}

_DEFAULT_PARKING_INDEX = {
    "last_updated": None,
    "total_items": 0,
    "by_category": {"features": [], "technical-debt": [], "research": [], "external-requests": []},
    "items": [],
}

_DEFAULT_SPRINTS_ARCHIVE_INDEX = {"sprints": []}

_DEFAULT_SESSION_END_INDEX = {"records": []}

_DEFAULT_VALIDATION_RULES = {
    "validation": {"require_front_matter": True, "skip_docs_directory": True},
    "system_scope_enforcement": {
        "enabled": True,
        "config_path": "process/automation/system_scope_config.json",
    },
    "sprint_tasks": {
        "require_task_yaml": True,
        "require_story_points": True,
        "required_task_fields": [
            "id",
            "title",
            "feature",
            "decision",
            "owner",
            "status",
            "story_points",
            "prio",
            "due",
            "acceptance",
        ],
        "required_task_files": ["README.md", "steps.md", "commands.md", "checklist.md", "validation.md"],
        "enforce_sprint_scoped_dependencies": True,
    },
    "story_points": {
        "validate_fibonacci_sequence": True,
        "allowed_story_points": [1, 2, 3, 5, 8, 13, 21],
    },
    "roadmap": {"normalize_links": True},
}

_DEFAULT_SYSTEM_SCOPE_CONFIG = {
    "schema_version": 1,
    "internal_system_root": ".project-handbook/system",
    "system_scope_excludes": ["roadmap", "releases"],
    "routing_rules": {
        "feature_name_prefixes_for_system_scope": ["handbook-", "ph-"],
        "task_lane_prefixes_for_system_scope": ["handbook/"],
        "adr_tags_triggering_system_scope": ["handbook", "project-handbook", "handbook-hygiene"],
    },
}

_DEFAULT_RESET_SPEC = {
    "schema_version": 1,
    "description": "Project-scope reset spec (MUST preserve .project-handbook/system/**).",
    "forbidden_subtrees": [".project-handbook/system"],
    "delete_contents_roots": [
        "sprints",
        "features",
        "adr",
        "decision-register",
        "backlog",
        "parking-lot",
        "releases",
        "contracts",
        "status",
        "process/sessions/logs",
        "process/sessions/session_end",
    ],
    "delete_paths": [".project-handbook/history.log"],
    "preserve_paths": [
        ".project-handbook/.gitkeep",
        "process/sessions/logs/.gitkeep",
        "sprints/archive/.gitkeep",
    ],
    "rewrite_paths": [
        "roadmap/now-next-later.md",
        "backlog/index.json",
        "parking-lot/index.json",
        "sprints/archive/index.json",
        "process/sessions/logs/latest_summary.md",
        "process/sessions/session_end/session_end_index.json",
    ],
    "recreate_dirs": [
        ".project-handbook",
        "backlog",
        "parking-lot",
        "process/sessions/logs",
        "process/sessions/session_end",
        "roadmap",
        "sprints/archive",
    ],
    "recreate_files": [
        ".project-handbook/.gitkeep",
        "process/sessions/logs/.gitkeep",
        "sprints/archive/.gitkeep",
    ],
}


class InitError(RuntimeError):
    pass


def _write_json_if_missing(*, path: Path, payload: dict) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise InitError(f"Failed to write: {path} ({exc})\n") from exc


def _write_text_if_missing(*, path: Path, text: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise InitError(f"Failed to write: {path} ({exc})\n") from exc


def _ensure_dirs(*, target_root: Path, rel_dirs: list[str]) -> None:
    for rel in rel_dirs:
        (target_root / rel).mkdir(parents=True, exist_ok=True)


def _ensure_gitignore(*, target_root: Path) -> None:
    path = target_root / ".gitignore"
    existing: list[str] = []
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            raise InitError(f"Failed to read .gitignore: {path} ({exc})\n") from exc

    normalized = {line.strip() for line in existing if line.strip()}
    to_add = [line for line in _DEFAULT_GITIGNORE_LINES if line not in normalized]
    if not to_add:
        return

    lines = list(existing)
    if lines and lines[-1].strip() != "":
        lines.append("")
    lines.extend(to_add)
    lines.append("")
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        raise InitError(f"Failed to write .gitignore: {path} ({exc})\n") from exc


def run_init(*, target_root: Path, update_gitignore: bool) -> int:
    target_root = target_root.resolve()
    if target_root.exists() and not target_root.is_dir():
        raise InitError(f"--root must be a directory: {target_root}\n")
    target_root.mkdir(parents=True, exist_ok=True)

    config_path = target_root / "project_handbook.config.json"

    if update_gitignore:
        _ensure_gitignore(target_root=target_root)

    # Internals (safe to create unconditionally).
    _ensure_dirs(
        target_root=target_root,
        rel_dirs=[
            ".project-handbook",
            "process/playbooks",
            "process/sessions/logs",
            "process/sessions/session_end",
        ],
    )
    _write_text_if_missing(path=target_root / ".project-handbook" / ".gitkeep", text="")
    _write_text_if_missing(path=target_root / "process" / "sessions" / "logs" / ".gitkeep", text="")

    # Required boot assets.
    _write_json_if_missing(
        path=target_root / "process" / "checks" / "validation_rules.json",
        payload=_DEFAULT_VALIDATION_RULES,
    )
    _write_json_if_missing(
        path=target_root / "process" / "automation" / "system_scope_config.json",
        payload=_DEFAULT_SYSTEM_SCOPE_CONFIG,
    )
    _write_json_if_missing(
        path=target_root / "process" / "automation" / "reset_spec.json",
        payload=_DEFAULT_RESET_SPEC,
    )
    (target_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)
    _write_json_if_missing(
        path=target_root / "process" / "sessions" / "session_end" / "session_end_index.json",
        payload=_DEFAULT_SESSION_END_INDEX,
    )

    today = dt.date.today().isoformat()
    _write_text_if_missing(
        path=target_root / "process" / "sessions" / "logs" / "latest_summary.md",
        text=_DEFAULT_LATEST_SESSION_SUMMARY.format(date=today),
    )

    _write_text_if_missing(path=target_root / "ONBOARDING.md", text=_DEFAULT_ONBOARDING_MD.format(date=today))
    _write_text_if_missing(
        path=target_root / "process" / "AI_AGENT_START_HERE.md",
        text=_DEFAULT_PROCESS_AGENT_GUIDE.format(date=today),
    )
    for name, text in _DEFAULT_SESSION_TEMPLATES.items():
        _write_text_if_missing(
            path=target_root / "process" / "sessions" / "templates" / f"{name}.md",
            text=text,
        )
    for name, text in _DEFAULT_PLAYBOOKS.items():
        _write_text_if_missing(
            path=target_root / "process" / "playbooks" / f"{name}.md",
            text=text.format(date=today),
        )

    # Content roots (repo-root handbook layout).
    _ensure_dirs(
        target_root=target_root,
        rel_dirs=[
            "adr",
            "assets",
            "backlog/bugs",
            "backlog/wildcards",
            "backlog/work-items",
            "backlog/archive/bugs",
            "backlog/archive/wildcards",
            "backlog/archive/work-items",
            "contracts",
            "decision-register",
            "docs/logs",
            "features/implemented",
            "parking-lot/features",
            "parking-lot/technical-debt",
            "parking-lot/research",
            "parking-lot/external-requests",
            "parking-lot/archive/features",
            "parking-lot/archive/technical-debt",
            "parking-lot/archive/research",
            "parking-lot/archive/external-requests",
            "releases/planning",
            "releases/delivered",
            "roadmap",
            "sprints/archive",
            "status/daily",
            "status/evidence",
            "status/exports",
            "tools",
        ],
    )
    _write_text_if_missing(path=target_root / "assets" / ".gitkeep", text="")
    _write_text_if_missing(path=target_root / "docs" / "logs" / ".gitkeep", text="")
    _write_text_if_missing(path=target_root / "tools" / ".gitkeep", text="")
    _write_json_if_missing(path=target_root / "backlog" / "index.json", payload=_DEFAULT_BACKLOG_INDEX)
    _write_json_if_missing(path=target_root / "parking-lot" / "index.json", payload=_DEFAULT_PARKING_INDEX)
    _write_json_if_missing(
        path=target_root / "sprints" / "archive" / "index.json",
        payload=_DEFAULT_SPRINTS_ARCHIVE_INDEX,
    )

    roadmap_seed = f"""---
title: Now / Next / Later Roadmap
type: roadmap
date: {today}
tags: [roadmap]
links: []
---

# Now / Next / Later Roadmap

## Now

## Next

## Later
"""
    _write_text_if_missing(path=target_root / "roadmap" / "now-next-later.md", text=roadmap_seed)

    if config_path.exists():
        print("Already exists: project_handbook.config.json")
        return 0

    payload = {
        "handbook_schema_version": DEFAULT_SCHEMA_VERSION,
        "requires_ph_version": DEFAULT_REQUIRES_PH_VERSION,
        "repo_root": DEFAULT_REPO_ROOT,
    }
    try:
        config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise InitError(f"Failed to write config: {config_path} ({exc})\n") from exc

    print("Created: project_handbook.config.json")
    return 0
