from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SCHEMA_VERSION = 1
DEFAULT_REPO_ROOT = "."
DEFAULT_REQUIRES_PH_VERSION = ">=0.1.0,<0.2.0"

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


def run_init(*, target_root: Path) -> int:
    target_root = target_root.resolve()
    if target_root.exists() and not target_root.is_dir():
        raise InitError(f"--root must be a directory: {target_root}\n")
    target_root.mkdir(parents=True, exist_ok=True)

    config_path = target_root / "project_handbook.config.json"

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
