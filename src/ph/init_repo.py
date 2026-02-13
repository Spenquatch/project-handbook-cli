from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .process_refresh import inject_seed_id_and_hash
from .root import PH_CONFIG_RELATIVE_PATH
from .seed_assets import load_seed_markdown_dir, render_date_placeholder

DEFAULT_SCHEMA_VERSION = 1
DEFAULT_REPO_ROOT = "."
DEFAULT_REQUIRES_PH_VERSION = ">=0.0.1,<0.1.0"

_DEFAULT_GITIGNORE_LINES = (
    ".project-handbook/history.log",
    ".project-handbook/process/sessions/logs/*",
    "!.project-handbook/process/sessions/logs/.gitkeep",
    ".project-handbook/status/exports",
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
   - `ph onboarding session research-planning`
   - `ph onboarding session task-docs-deep-dive`
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

_DEFAULT_AGENT_MD = """---
title: Project Handbook Agent Context
type: guide
date: {date}
tags: [agents, context]
links: []
---

# Agent Context

Use this file to capture stable, repo-specific context that agents should load before planning or execution.

## Defaults
- Source of truth for process artifacts is `.project-handbook/`.
- Prefer `ph ...` commands over ad-hoc edits when a command exists.
"""


_FALLBACK_SESSION_TEMPLATES: dict[str, str] = {
    "sprint-planning": "---\ntitle: Sprint Planning Session\n---\n",
    "task-execution": "---\ntitle: Task Execution Session\n---\n",
    "research-discovery": "---\ntitle: Research/Discovery Session\n---\n",
    "research-planning": "---\ntitle: Research Planning Session\n---\n",
    "task-docs-deep-dive": "---\ntitle: Task Docs Deep Dive\n---\n",
    "pre-execution-audit": "---\ntitle: Pre-execution Audit\n---\n",
    "quality-gate": "---\ntitle: Quality Gate Session\n---\n",
    "release-planning": "---\ntitle: Release Planning Session\n---\n",
    "sprint-closing": "---\ntitle: Sprint Closing Session\n---\n",
}


_FALLBACK_PLAYBOOKS: dict[str, str] = {
    "sprint-planning": "---\ntitle: Sprint Planning Playbook\ndate: {date}\n---\n",
    "sprint-closing": "---\ntitle: Sprint Closing Playbook\ndate: {date}\n---\n",
    "daily-status": "---\ntitle: Daily Status Playbook\ndate: {date}\n---\n",
    "release-planning": "---\ntitle: Release Planning Playbook\ndate: {date}\n---\n",
    "backlog-triage": "---\ntitle: Backlog Triage Playbook\ndate: {date}\n---\n",
    "parking-lot-review": "---\ntitle: Parking Lot Review Playbook\ndate: {date}\n---\n",
    "research-discovery": "---\ntitle: Research / Discovery Playbook\ndate: {date}\n---\n",
    "roadmap-planning": "---\ntitle: Roadmap Planning Playbook\ndate: {date}\n---\n",
}


def _load_session_templates() -> dict[str, str]:
    templates = load_seed_markdown_dir(rel_dir="process/sessions/templates")
    return templates or dict(_FALLBACK_SESSION_TEMPLATES)


def _load_playbooks() -> dict[str, str]:
    playbooks = load_seed_markdown_dir(rel_dir="process/playbooks")
    return playbooks or dict(_FALLBACK_PLAYBOOKS)


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
    "sprint_management": {
        "mode": "bounded",
        "health_check_thresholds": {
            "blocked_percentage_red": 30,
            "progress_percentage_red": 50,
            "progress_check_day": 3,
        },
        "sprint_duration_days": 5,
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
        ".project-handbook/sprints",
        ".project-handbook/features",
        ".project-handbook/adr",
        ".project-handbook/decision-register",
        ".project-handbook/backlog",
        ".project-handbook/parking-lot",
        ".project-handbook/releases",
        ".project-handbook/contracts",
        ".project-handbook/status",
        ".project-handbook/process/sessions/logs",
        ".project-handbook/process/sessions/session_end",
    ],
    "delete_paths": [".project-handbook/history.log"],
    "preserve_paths": [
        ".project-handbook/.gitkeep",
        ".project-handbook/process/sessions/logs/.gitkeep",
        ".project-handbook/sprints/archive/.gitkeep",
    ],
    "rewrite_paths": [
        ".project-handbook/roadmap/now-next-later.md",
        ".project-handbook/backlog/index.json",
        ".project-handbook/parking-lot/index.json",
        ".project-handbook/sprints/archive/index.json",
        ".project-handbook/process/sessions/logs/latest_summary.md",
        ".project-handbook/process/sessions/session_end/session_end_index.json",
    ],
    "recreate_dirs": [
        ".project-handbook",
        ".project-handbook/backlog",
        ".project-handbook/parking-lot",
        ".project-handbook/process/sessions/logs",
        ".project-handbook/process/sessions/session_end",
        ".project-handbook/roadmap",
        ".project-handbook/sprints/archive",
    ],
    "recreate_files": [
        ".project-handbook/.gitkeep",
        ".project-handbook/process/sessions/logs/.gitkeep",
        ".project-handbook/sprints/archive/.gitkeep",
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

    config_path = target_root / PH_CONFIG_RELATIVE_PATH
    data_root = config_path.parent

    if update_gitignore:
        _ensure_gitignore(target_root=target_root)

    # Handbook root (safe to create unconditionally).
    _ensure_dirs(
        target_root=target_root,
        rel_dirs=[
            ".project-handbook",
            ".project-handbook/system",
            ".project-handbook/process/playbooks",
            ".project-handbook/process/sessions/logs",
            ".project-handbook/process/sessions/session_end",
        ],
    )
    _write_text_if_missing(path=data_root / ".gitkeep", text="")
    _write_text_if_missing(path=data_root / "process" / "sessions" / "logs" / ".gitkeep", text="")

    # Required boot assets.
    _write_json_if_missing(
        path=data_root / "process" / "checks" / "validation_rules.json",
        payload=_DEFAULT_VALIDATION_RULES,
    )
    _write_json_if_missing(
        path=data_root / "process" / "automation" / "system_scope_config.json",
        payload=_DEFAULT_SYSTEM_SCOPE_CONFIG,
    )
    _write_json_if_missing(
        path=data_root / "process" / "automation" / "reset_spec.json",
        payload=_DEFAULT_RESET_SPEC,
    )
    (data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)
    _write_json_if_missing(
        path=data_root / "process" / "sessions" / "session_end" / "session_end_index.json",
        payload=_DEFAULT_SESSION_END_INDEX,
    )

    today = dt.date.today().isoformat()
    _write_text_if_missing(
        path=data_root / "process" / "sessions" / "logs" / "latest_summary.md",
        text=_DEFAULT_LATEST_SESSION_SUMMARY.format(date=today),
    )

    _write_text_if_missing(path=data_root / "ONBOARDING.md", text=_DEFAULT_ONBOARDING_MD.format(date=today))
    _write_text_if_missing(path=data_root / "AGENT.md", text=_DEFAULT_AGENT_MD.format(date=today))
    _write_text_if_missing(
        path=data_root / "process" / "AI_AGENT_START_HERE.md",
        text=_DEFAULT_PROCESS_AGENT_GUIDE.format(date=today),
    )
    for name, text in _load_session_templates().items():
        seeded = inject_seed_id_and_hash(text=text, seed_id=f"process/sessions/templates/{name}.md")
        _write_text_if_missing(
            path=data_root / "process" / "sessions" / "templates" / f"{name}.md",
            text=seeded,
        )
    for name, text in _load_playbooks().items():
        rendered = render_date_placeholder(text, date=today)
        seeded = inject_seed_id_and_hash(text=rendered, seed_id=f"process/playbooks/{name}.md")
        _write_text_if_missing(
            path=data_root / "process" / "playbooks" / f"{name}.md",
            text=seeded,
        )

    # Content roots (handbook layout under .project-handbook/).
    _ensure_dirs(
        target_root=data_root,
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
            "status/questions",
            "tools",
        ],
    )
    _write_text_if_missing(path=data_root / "assets" / ".gitkeep", text="")
    _write_text_if_missing(path=data_root / "docs" / "logs" / ".gitkeep", text="")
    _write_text_if_missing(path=data_root / "tools" / ".gitkeep", text="")
    _write_json_if_missing(path=data_root / "backlog" / "index.json", payload=_DEFAULT_BACKLOG_INDEX)
    _write_json_if_missing(path=data_root / "parking-lot" / "index.json", payload=_DEFAULT_PARKING_INDEX)
    _write_json_if_missing(
        path=data_root / "sprints" / "archive" / "index.json",
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
    _write_text_if_missing(path=data_root / "roadmap" / "now-next-later.md", text=roadmap_seed)

    if config_path.exists():
        print(f"Already exists: {PH_CONFIG_RELATIVE_PATH.as_posix()}")
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

    print(f"Created: {PH_CONFIG_RELATIVE_PATH.as_posix()}")
    return 0
