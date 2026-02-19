from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path

from . import __version__
from .adr import run_adr_add, run_adr_list
from .adr.add import add_adr_add_arguments
from .backlog import (
    run_backlog_add,
    run_backlog_assign,
    run_backlog_list,
    run_backlog_rubric,
    run_backlog_stats,
    run_backlog_triage,
)
from .clean import clean_python_caches
from .config import ConfigError, load_handbook_config, validate_handbook_config
from .context import ScopeError, build_context, resolve_scope
from .daily import check_status as check_daily_status
from .daily import create_daily_status
from .dashboard import run_dashboard
from .doctor import run_doctor
from .dr.add import add_dr_add_arguments, run_dr_add
from .end_session import EndSessionError, run_end_session_codex, run_end_session_skip_codex
from .fdr import run_fdr_add
from .fdr.add import add_fdr_add_arguments
from .feature import run_feature_create, run_feature_list, run_feature_status
from .feature_archive import run_feature_archive
from .feature_status_updater import run_feature_summary, run_feature_update_status
from .git_hooks import install_git_hooks
from .help_text import get_help_text
from .hooks import plan_post_command_hook, run_post_command_hook
from .init_repo import InitError, run_init
from .migrate_system_scope import run_migrate_system_scope
from .onboarding import (
    OnboardingError,
    SessionList,
    list_session_topics,
    read_latest_session_summary,
    render_onboarding,
    render_session_template,
)
from .orchestration import run_check_all, run_test_system
from .parking import run_parking_add, run_parking_list, run_parking_promote, run_parking_review
from .pre_exec import PreExecError, run_pre_exec_audit, run_pre_exec_lint
from .process_refresh import run_process_refresh
from .question import run_question_add, run_question_answer, run_question_close, run_question_list, run_question_show
from .release import (
    run_release_activate,
    run_release_add_feature,
    run_release_clear,
    run_release_close,
    run_release_draft,
    run_release_list,
    run_release_migrate_slot_format,
    run_release_plan,
    run_release_progress,
    run_release_show,
    run_release_status,
    run_release_suggest,
)
from .reset import ResetError, run_reset
from .reset_smoke import run_reset_smoke
from .roadmap import run_roadmap_create, run_roadmap_show, run_roadmap_validate
from .root import RootResolutionError, resolve_ph_root
from .sprint_archive import run_sprint_archive
from .sprint_burndown import run_sprint_burndown
from .sprint_capacity import run_sprint_capacity
from .sprint_close import run_sprint_close
from .sprint_commands import sprint_open, sprint_plan
from .sprint_status import run_sprint_status
from .sprint_tasks import run_sprint_tasks
from .status import run_status
from .task_create import run_task_create
from .task_status import run_task_status
from .task_view import run_task_list, run_task_show
from .validate_docs import run_validate


def _format_cli_preamble(*, ph_root: Path, cmd_args: list[str]) -> str:
    reporter = (
        os.environ.get("npm_config_reporter")
        or os.environ.get("NPM_CONFIG_REPORTER")
        or os.environ.get("PNPM_REPORTER")
    )
    if isinstance(reporter, str) and reporter.strip().lower() == "silent":
        return ""

    pkg = ph_root / "package.json"
    if not pkg.exists():
        return ""

    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""

    name = data.get("name")
    version = data.get("version")
    if not isinstance(name, str) or not name.strip():
        return ""
    if not isinstance(version, str) or not version.strip():
        return ""

    cwd = str(ph_root.resolve())
    args = shlex.join([str(token) for token in cmd_args if str(token)])
    return f"\n> {name}@{version} ph {cwd}\n> ph {args}\n\n"


def build_parser() -> argparse.ArgumentParser:
    def _add_common_args(p: argparse.ArgumentParser, *, suppress_defaults: bool) -> None:
        default = argparse.SUPPRESS if suppress_defaults else None
        p.add_argument("--root", default=default, help="Path to the handbook instance repo root")
        p.add_argument(
            "--scope",
            choices=["project", "system"],
            default=default,
            help="Select data scope (default: project)",
        )
        p.add_argument(
            "--no-post-hook",
            action="store_true",
            default=argparse.SUPPRESS if suppress_defaults else False,
            help="Disable post-command hook (history + validate)",
        )
        p.add_argument(
            "--no-history",
            action="store_true",
            default=argparse.SUPPRESS if suppress_defaults else False,
            help="Disable history logging",
        )
        p.add_argument(
            "--no-validate",
            action="store_true",
            default=argparse.SUPPRESS if suppress_defaults else False,
            help="Disable post-command validate-quick",
        )

    main_common = argparse.ArgumentParser(add_help=False)
    _add_common_args(main_common, suppress_defaults=False)
    sub_common = argparse.ArgumentParser(add_help=False)
    _add_common_args(sub_common, suppress_defaults=True)

    parser = argparse.ArgumentParser(prog="ph", description="Project Handbook CLI", parents=[main_common])
    parser.set_defaults(_post_validate="never")
    subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="<command>")

    version_parser = subparsers.add_parser("version", help="Print installed ph version", parents=[sub_common])
    version_parser.set_defaults(_post_validate="never")
    version_parser.set_defaults(_handler=_handle_version)

    init_parser = subparsers.add_parser("init", help="Initialize a new handbook instance repo", parents=[sub_common])
    init_parser.set_defaults(_post_validate="never")
    init_gitignore_group = init_parser.add_mutually_exclusive_group()
    init_gitignore_group.add_argument(
        "--gitignore",
        dest="gitignore",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Update/create .gitignore with recommended handbook ignores (default)",
    )
    init_gitignore_group.add_argument(
        "--no-gitignore",
        dest="gitignore",
        action="store_false",
        default=argparse.SUPPRESS,
        help="Do not read or write .gitignore",
    )
    init_parser.set_defaults(gitignore=True)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check repo compatibility and required assets",
        parents=[sub_common],
    )
    doctor_parser.set_defaults(_post_validate="quick")
    doctor_parser.set_defaults(_handler=_handle_doctor)

    help_parser = subparsers.add_parser("help", help="Show help topics", parents=[sub_common])
    help_parser.set_defaults(_post_validate="never")
    help_parser.add_argument("topic", nargs="?", help="Help topic")

    onboarding_parser = subparsers.add_parser(
        "onboarding",
        help="Show onboarding docs and sessions",
        parents=[sub_common],
    )
    onboarding_parser.set_defaults(_post_validate="never")
    onboarding_subparsers = onboarding_parser.add_subparsers(
        dest="onboarding_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    onboarding_session = onboarding_subparsers.add_parser(
        "session",
        help="Show onboarding session templates",
        parents=[sub_common],
    )
    onboarding_session.set_defaults(_post_validate="never")
    onboarding_session.add_argument("session_topic", nargs="?", help="Session topic (or 'list' / 'continue-session')")

    hooks_parser = subparsers.add_parser("hooks", help="Install repo git hooks", parents=[sub_common])
    hooks_parser.set_defaults(_post_validate="never")
    hooks_subparsers = hooks_parser.add_subparsers(
        dest="hooks_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    hooks_install = hooks_subparsers.add_parser("install", help="Install repo git hooks", parents=[sub_common])
    hooks_install.set_defaults(_post_validate="never")

    end_session_parser = subparsers.add_parser(
        "end-session",
        help="Summarize a Codex session rollout log",
        parents=[sub_common],
    )
    end_session_parser.set_defaults(_post_validate="never")
    end_session_parser.add_argument("--log", required=True, help="Path to rollout log file")
    end_session_parser.add_argument(
        "--force", action="store_true", help="Process the provided --log even if cwd mismatches"
    )
    end_session_parser.add_argument("--session-id", help="Explicit session id to match")
    end_session_parser.add_argument(
        "--session-end-mode",
        choices=["none", "continue-task", "sprint-hand-off"],
        default="none",
        help="Emit a lightweight session-end recap",
    )
    end_session_parser.add_argument(
        "--session-end-codex", action="store_true", help="Use Codex enrichment for session-end"
    )
    end_session_parser.add_argument("--session-end-codex-model", help="Model to use for session-end Codex enrichment")
    end_session_parser.add_argument("--skip-codex", action="store_true", help="Skip Codex calls (offline mode)")
    end_session_parser.add_argument("--workstream", help="Workstream identifier for session_end artifacts")
    end_session_parser.add_argument("--task-ref", help="Optional task identifier for session_end artifacts")
    end_session_parser.add_argument("--codex-model", help="Model used for headless summarization")
    end_session_parser.add_argument(
        "--reasoning-effort",
        choices=["minimal", "low", "medium", "high"],
        help="Override Codex reasoning effort for compression prompts.",
    )
    end_session_parser.add_argument(
        "--reasoning-summary",
        choices=["auto", "concise", "detailed", "none"],
        help="Override Codex reasoning summary style.",
    )
    end_session_parser.add_argument(
        "--model-verbosity",
        choices=["low", "medium", "high"],
        help="Override Codex model verbosity (experimental).",
    )

    clean_parser = subparsers.add_parser("clean", help="Remove Python cache files under PH_ROOT", parents=[sub_common])
    clean_parser.set_defaults(_post_validate="never")

    reset_parser = subparsers.add_parser(
        "reset",
        help="Reset project scope (dry-run by default)",
        parents=[sub_common],
    )
    reset_parser.set_defaults(_post_validate="never")
    reset_parser.add_argument(
        "--spec",
        default=".project-handbook/process/automation/reset_spec.json",
        help="Repo-relative path to reset spec JSON",
    )
    reset_parser.add_argument("--confirm", default="", help="Must be exactly RESET to execute")
    reset_parser.add_argument("--force", default="", help="Must be exactly true to execute")

    reset_smoke_parser = subparsers.add_parser(
        "reset-smoke",
        help="Run reset smoke verification (destructive to project scope)",
        parents=[sub_common],
    )
    reset_smoke_parser.set_defaults(_post_validate="never")

    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate artifacts between scopes",
        parents=[sub_common],
    )
    migrate_parser.set_defaults(_post_validate="never")
    migrate_subparsers = migrate_parser.add_subparsers(
        dest="migrate_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    migrate_system = migrate_subparsers.add_parser(
        "system-scope",
        help="Migrate system-scoped artifacts out of project scope",
        parents=[sub_common],
    )
    migrate_system.set_defaults(_post_validate="quick")
    migrate_system.add_argument("--confirm", default="", help="Must be exactly RESET to run")
    migrate_system.add_argument("--force", default="", help="Must be exactly true to run")

    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Show sprint + validation snapshot",
        parents=[sub_common],
    )
    dashboard_parser.set_defaults(_post_validate="never")
    status_parser = subparsers.add_parser("status", help="Generate status rollup", parents=[sub_common])
    status_parser.set_defaults(_post_validate="never")
    check_all_parser = subparsers.add_parser("check-all", help="Run validate + status", parents=[sub_common])
    check_all_parser.set_defaults(_post_validate="never")

    test_parser = subparsers.add_parser("test", help="Run automation smoke suites", parents=[sub_common])
    test_parser.set_defaults(_post_validate="never")
    test_subparsers = test_parser.add_subparsers(
        dest="test_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    test_system_parser = test_subparsers.add_parser(
        "system",
        help="Run handbook system smoke suite",
        parents=[sub_common],
    )
    test_system_parser.set_defaults(_post_validate="never")

    sprint_parser = subparsers.add_parser("sprint", help="Manage sprint lifecycle", parents=[sub_common])
    sprint_parser.set_defaults(_post_validate="never")
    sprint_subparsers = sprint_parser.add_subparsers(
        dest="sprint_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    sprint_plan_parser = sprint_subparsers.add_parser("plan", help="Create sprint plan", parents=[sub_common])
    sprint_plan_parser.set_defaults(_post_validate="quick")
    sprint_plan_parser.add_argument("--sprint", help="Sprint ID (default: computed)")
    sprint_plan_parser.add_argument("--force", action="store_true", help="Overwrite existing plan.md")
    sprint_open_parser = sprint_subparsers.add_parser(
        "open", help="Set current sprint to existing", parents=[sub_common]
    )
    sprint_open_parser.set_defaults(_post_validate="quick")
    sprint_open_parser.add_argument("--sprint", required=True, help="Sprint ID to open")
    sprint_status_parser = sprint_subparsers.add_parser("status", help="Show sprint status", parents=[sub_common])
    sprint_status_parser.set_defaults(_post_validate="never")
    sprint_status_parser.add_argument("--sprint", help="Sprint ID (default: current)")
    sprint_tasks_parser = sprint_subparsers.add_parser("tasks", help="List sprint tasks", parents=[sub_common])
    sprint_tasks_parser.set_defaults(_post_validate="never")
    sprint_tasks_parser.add_argument("--sprint", help="Sprint ID (default: current)")
    sprint_burndown_parser = sprint_subparsers.add_parser(
        "burndown", help="Generate sprint burndown", parents=[sub_common]
    )
    sprint_burndown_parser.set_defaults(_post_validate="never")
    sprint_burndown_parser.add_argument("--sprint", help="Sprint ID (default: current)")
    sprint_capacity_parser = sprint_subparsers.add_parser(
        "capacity", help="Show sprint capacity allocation", parents=[sub_common]
    )
    sprint_capacity_parser.set_defaults(_post_validate="never")
    sprint_capacity_parser.add_argument("--sprint", help="Sprint ID (default: current)")
    sprint_archive_parser = sprint_subparsers.add_parser(
        "archive", help="Archive sprint into sprints/archive", parents=[sub_common]
    )
    sprint_archive_parser.set_defaults(_post_validate="quick")
    sprint_archive_parser.add_argument("--sprint", help="Sprint ID (default: current)")
    sprint_close_parser = sprint_subparsers.add_parser(
        "close", help="Close sprint and archive it", parents=[sub_common]
    )
    sprint_close_parser.set_defaults(_post_validate="quick")
    sprint_close_parser.add_argument("--sprint", help="Sprint ID (default: current)")

    task_parser = subparsers.add_parser("task", help="Manage sprint tasks", parents=[sub_common])
    task_parser.set_defaults(_post_validate="never")
    task_subparsers = task_parser.add_subparsers(
        dest="task_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    task_create_parser = task_subparsers.add_parser(
        "create", help="Create a new task in current sprint", parents=[sub_common]
    )
    task_create_parser.set_defaults(_post_validate="quick")
    task_create_parser.add_argument("--title", required=True, help="Task title")
    task_create_parser.add_argument("--feature", required=True, help="Feature name")
    task_create_parser.add_argument("--decision", required=True, help="Decision id (ADR-XXX, FDR-XXX, DR-XXX)")
    task_create_parser.add_argument("--points", type=int, help="Story points (default: 5)")
    task_create_parser.add_argument("--owner", default="@owner", help="Task owner (default: @owner)")
    task_create_parser.add_argument("--prio", default="P2", help="Priority (default: P2)")
    task_create_parser.add_argument("--lane", help="Optional lane/workstream label")
    task_create_parser.add_argument(
        "--type",
        "--task-type",
        dest="task_type",
        default=None,
        help="Task taxonomy (e.g. implementation, research-discovery, sprint-gate)",
    )
    task_create_parser.add_argument("--session", default="task-execution", help="Recommended session template")
    task_create_parser.add_argument(
        "--release",
        help='Optional release tag (vX.Y.Z or "current") to attribute work to a release',
    )
    task_create_parser.add_argument(
        "--gate",
        action="store_true",
        help="Mark this task as a release gate (counts toward release burn-up)",
    )
    task_list_parser = task_subparsers.add_parser("list", help="List tasks in current sprint", parents=[sub_common])
    task_list_parser.set_defaults(_post_validate="never")
    task_show_parser = task_subparsers.add_parser("show", help="Show a task", parents=[sub_common])
    task_show_parser.set_defaults(_post_validate="never")
    task_show_parser.add_argument("--id", required=True, help="Task id (e.g. TASK-001)")
    task_status_parser = task_subparsers.add_parser("status", help="Update task status", parents=[sub_common])
    task_status_parser.set_defaults(_post_validate="quick")
    task_status_parser.add_argument("--id", required=True, help="Task id (e.g. TASK-001)")
    task_status_parser.add_argument("--status", required=True, help="New status (e.g. doing)")
    task_status_parser.add_argument(
        "--force",
        action="store_true",
        help="Force update despite unresolved dependencies (requires explicit user approval)",
    )

    feature_parser = subparsers.add_parser("feature", help="Manage features", parents=[sub_common])
    feature_parser.set_defaults(_post_validate="never")
    feature_subparsers = feature_parser.add_subparsers(
        dest="feature_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    feature_list_parser = feature_subparsers.add_parser("list", help="List features", parents=[sub_common])
    feature_list_parser.set_defaults(_post_validate="never")
    feature_create_parser = feature_subparsers.add_parser("create", help="Create a new feature", parents=[sub_common])
    feature_create_parser.set_defaults(_post_validate="quick")
    feature_create_parser.add_argument("--name", required=True, help="Feature name (kebab-case)")
    feature_create_parser.add_argument("--epic", action="store_true", help="Mark feature as an epic")
    feature_create_parser.add_argument("--owner", default="@owner", help="Owner (default: @owner)")
    feature_create_parser.add_argument("--stage", default="proposed", help="Initial stage (default: proposed)")
    feature_status_parser = feature_subparsers.add_parser("status", help="Update feature stage", parents=[sub_common])
    feature_status_parser.set_defaults(_post_validate="quick")
    feature_status_parser.add_argument("--name", required=True, help="Feature name (kebab-case)")
    feature_status_parser.add_argument("--stage", required=True, help="New stage")
    feature_update_status_parser = feature_subparsers.add_parser(
        "update-status", help="Update status.md files from sprint tasks", parents=[sub_common]
    )
    feature_update_status_parser.set_defaults(_post_validate="quick")
    feature_summary_parser = feature_subparsers.add_parser(
        "summary",
        help="Show feature summary with sprint data",
        parents=[sub_common],
    )
    feature_summary_parser.set_defaults(_post_validate="never")
    feature_archive_parser = feature_subparsers.add_parser(
        "archive", help="Archive a feature into features/implemented", parents=[sub_common]
    )
    feature_archive_parser.set_defaults(_post_validate="quick")
    feature_archive_parser.add_argument("--name", required=True, help="Feature name (kebab-case)")
    feature_archive_parser.add_argument(
        "--force", action="store_true", help="Force archive despite warnings (requires explicit approval)"
    )

    adr_parser = subparsers.add_parser("adr", help="Manage ADRs", parents=[sub_common])
    adr_parser.set_defaults(_post_validate="never")
    adr_subparsers = adr_parser.add_subparsers(
        dest="adr_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    adr_add_parser = adr_subparsers.add_parser("add", help="Create an ADR file", parents=[sub_common])
    adr_add_parser.set_defaults(_post_validate="quick")
    add_adr_add_arguments(adr_add_parser)
    adr_list_parser = adr_subparsers.add_parser("list", help="List ADRs", parents=[sub_common])
    adr_list_parser.set_defaults(_post_validate="never")

    dr_parser = subparsers.add_parser("dr", help="Manage Decision Register entries", parents=[sub_common])
    dr_parser.set_defaults(_post_validate="never")
    dr_subparsers = dr_parser.add_subparsers(
        dest="dr_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    dr_add_parser = dr_subparsers.add_parser("add", help="Create a DR file", parents=[sub_common])
    dr_add_parser.set_defaults(_post_validate="quick")
    add_dr_add_arguments(dr_add_parser)

    fdr_parser = subparsers.add_parser("fdr", help="Manage Feature Decision Records", parents=[sub_common])
    fdr_parser.set_defaults(_post_validate="never")
    fdr_subparsers = fdr_parser.add_subparsers(
        dest="fdr_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    fdr_add_parser = fdr_subparsers.add_parser("add", help="Create an FDR file", parents=[sub_common])
    fdr_add_parser.set_defaults(_post_validate="quick")
    add_fdr_add_arguments(fdr_add_parser)

    backlog_parser = subparsers.add_parser("backlog", help="Manage issue backlog", parents=[sub_common])
    backlog_parser.set_defaults(_post_validate="never")
    backlog_subparsers = backlog_parser.add_subparsers(
        dest="backlog_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    backlog_add_parser = backlog_subparsers.add_parser("add", help="Create a backlog entry", parents=[sub_common])
    backlog_add_parser.set_defaults(_post_validate="quick")
    backlog_add_parser.add_argument(
        "--type",
        dest="issue_type",
        required=True,
        help="bug|wildcards|work-items (accepts v0 synonyms)",
    )
    backlog_add_parser.add_argument("--title", required=True, help="Issue title")
    backlog_add_parser.add_argument("--severity", required=True, help="P0|P1|P2|P3|P4")
    backlog_add_parser.add_argument("--desc", default="", help="Description")
    backlog_add_parser.add_argument("--owner", default="", help="Owner handle (e.g. @alice)")
    backlog_add_parser.add_argument("--impact", default="", help="Impact summary")
    backlog_add_parser.add_argument("--workaround", default="", help="Workaround summary")
    backlog_list_parser = backlog_subparsers.add_parser("list", help="List backlog entries", parents=[sub_common])
    backlog_list_parser.set_defaults(_post_validate="never")
    backlog_list_parser.add_argument("--severity", help="Filter by severity (P0..P4)")
    backlog_list_parser.add_argument("--category", help="Filter by category (bugs|wildcards|work-items)")
    backlog_list_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format (default: table)"
    )
    backlog_triage_parser = backlog_subparsers.add_parser(
        "triage", help="Show or create triage analysis", parents=[sub_common]
    )
    backlog_triage_parser.set_defaults(_post_validate="quick")
    backlog_triage_parser.add_argument("--issue", dest="issue_id", required=True, help="Issue id (e.g. BUG-P1-...)")
    backlog_assign_parser = backlog_subparsers.add_parser(
        "assign", help="Assign a backlog issue to a sprint", parents=[sub_common]
    )
    backlog_assign_parser.set_defaults(_post_validate="quick")
    backlog_assign_parser.add_argument("--issue", dest="issue_id", required=True, help="Issue id (e.g. BUG-P1-...)")
    backlog_assign_parser.add_argument("--sprint", default="current", help="current|next|SPRINT-... (default: current)")
    backlog_rubric_parser = backlog_subparsers.add_parser("rubric", help="Show severity rubric", parents=[sub_common])
    backlog_rubric_parser.set_defaults(_post_validate="never")
    backlog_stats_parser = backlog_subparsers.add_parser("stats", help="Show backlog statistics", parents=[sub_common])
    backlog_stats_parser.set_defaults(_post_validate="never")

    parking_parser = subparsers.add_parser("parking", help="Manage parking lot items", parents=[sub_common])
    parking_parser.set_defaults(_post_validate="never")
    parking_subparsers = parking_parser.add_subparsers(
        dest="parking_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    parking_add_parser = parking_subparsers.add_parser("add", help="Create a parking lot item", parents=[sub_common])
    parking_add_parser.set_defaults(_post_validate="quick")
    parking_add_parser.add_argument(
        "--type",
        dest="parking_type",
        required=True,
        choices=["features", "technical-debt", "research", "external-requests"],
        help="features|technical-debt|research|external-requests",
    )
    parking_add_parser.add_argument("--title", required=True, help="Item title")
    parking_add_parser.add_argument("--desc", default="", help="Description")
    parking_add_parser.add_argument("--owner", default="", help="Owner handle (e.g. @alice)")
    parking_add_parser.add_argument("--tags", default="", help="Comma-separated tags")

    parking_list_parser = parking_subparsers.add_parser("list", help="List parking lot items", parents=[sub_common])
    parking_list_parser.set_defaults(_post_validate="never")
    parking_list_parser.add_argument(
        "--category",
        choices=["features", "technical-debt", "research", "external-requests"],
        help="Filter by category",
    )
    parking_list_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format (default: table)"
    )

    parking_review_parser = parking_subparsers.add_parser(
        "review",
        help="Review parking lot items",
        parents=[sub_common],
    )
    parking_review_parser.set_defaults(_post_validate="never")
    parking_review_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parking_promote_parser = parking_subparsers.add_parser(
        "promote", help="Promote item to roadmap", parents=[sub_common]
    )
    parking_promote_parser.set_defaults(_post_validate="quick")
    parking_promote_parser.add_argument("--item", required=True, help="Item id (e.g. FEAT-...)")
    parking_promote_parser.add_argument(
        "--target",
        choices=["now", "next", "later"],
        default="later",
        help="now|next|later (default: later)",
    )

    process_parser = subparsers.add_parser("process", help="Manage process templates/playbooks", parents=[sub_common])
    process_parser.set_defaults(_post_validate="never")
    process_subparsers = process_parser.add_subparsers(
        dest="process_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    process_refresh = process_subparsers.add_parser(
        "refresh",
        help="Refresh seeded session templates and playbooks",
        parents=[sub_common],
    )
    process_refresh.set_defaults(_post_validate="quick")
    process_refresh.add_argument("--templates", action="store_true", help="Refresh session templates only")
    process_refresh.add_argument("--playbooks", action="store_true", help="Refresh playbooks only")
    process_refresh.add_argument("--force", action="store_true", help="Overwrite modified seed-owned files")

    question_parser = subparsers.add_parser("question", help="Manage operator questions", parents=[sub_common])
    question_parser.set_defaults(_post_validate="never")
    question_subparsers = question_parser.add_subparsers(
        dest="question_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    question_add = question_subparsers.add_parser("add", help="Add a question for the operator", parents=[sub_common])
    question_add.set_defaults(_post_validate="quick")
    question_add.add_argument("--title", required=True, help="Question title")
    question_add.add_argument("--severity", required=True, help="blocking|non-blocking")
    question_add.add_argument(
        "--q-scope",
        dest="question_scope",
        required=True,
        help="Question scope: sprint|task|release|project (NOT the system/project CLI scope)",
    )
    question_add.add_argument("--sprint", help="Sprint id (required for scope sprint|task)")
    question_add.add_argument("--task-id", help="Task id (required for scope task)")
    question_add.add_argument("--release", help="Optional release id (vX.Y.Z or current)")
    question_add.add_argument("--asked-by", help="Who asked (agent/human)")
    question_add.add_argument("--owner", help="Owner handle (e.g. @spenser)")
    question_add.add_argument("--body", default="", help="Question body/details")

    question_list = question_subparsers.add_parser("list", help="List questions", parents=[sub_common])
    question_list.set_defaults(_post_validate="never")
    question_list.add_argument("--status", default="open", help="open|answered|closed|all (default: open)")
    question_list.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    question_show = question_subparsers.add_parser("show", help="Show a question", parents=[sub_common])
    question_show.set_defaults(_post_validate="never")
    question_show.add_argument("--id", required=True, help="Question id (e.g. Q-0001)")

    question_answer = question_subparsers.add_parser("answer", help="Record an answer", parents=[sub_common])
    question_answer.set_defaults(_post_validate="quick")
    question_answer.add_argument("--id", required=True, help="Question id (e.g. Q-0001)")
    question_answer.add_argument("--answer", required=True, help="Answer text")
    question_answer.add_argument("--by", help="Answerer handle (e.g. @user)")

    question_close = question_subparsers.add_parser("close", help="Close a question", parents=[sub_common])
    question_close.set_defaults(_post_validate="quick")
    question_close.add_argument("--id", required=True, help="Question id (e.g. Q-0001)")
    question_close.add_argument("--resolution", required=True, help="answered|not-needed|superseded")

    roadmap_parser = subparsers.add_parser("roadmap", help="Manage the project roadmap", parents=[sub_common])
    roadmap_parser.set_defaults(_post_validate="never")
    roadmap_subparsers = roadmap_parser.add_subparsers(
        dest="roadmap_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    roadmap_show_parser = roadmap_subparsers.add_parser(
        "show",
        help="Show roadmap now/next/later",
        parents=[sub_common],
    )
    roadmap_show_parser.set_defaults(_post_validate="never")
    roadmap_create_parser = roadmap_subparsers.add_parser(
        "create",
        help="Create roadmap template",
        parents=[sub_common],
    )
    roadmap_create_parser.set_defaults(_post_validate="quick")
    roadmap_validate_parser = roadmap_subparsers.add_parser(
        "validate",
        help="Validate roadmap links",
        parents=[sub_common],
    )
    roadmap_validate_parser.set_defaults(_post_validate="never")

    release_parser = subparsers.add_parser("release", help="Manage project releases", parents=[sub_common])
    release_parser.set_defaults(_post_validate="never")
    release_subparsers = release_parser.add_subparsers(
        dest="release_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    release_plan_parser = release_subparsers.add_parser("plan", help="Create a release plan", parents=[sub_common])
    release_plan_parser.set_defaults(_post_validate="quick")
    release_plan_parser.add_argument("--version", help="Release version (vX.Y.Z or 'next')")
    release_plan_parser.add_argument("--activate", action="store_true", help="Activate this release as current")
    release_plan_parser.add_argument("--bump", choices=["patch", "minor", "major"], default="patch")
    release_plan_parser.add_argument("--sprints", type=int, default=3, help="Number of sprints (default: 3)")
    release_plan_parser.add_argument("--start-sprint", help="Starting sprint id (SPRINT-...)")
    release_plan_parser.add_argument("--sprint-ids", help="Comma-separated sprint ids (overrides --sprints)")
    release_activate = release_subparsers.add_parser("activate", help="Set the current release", parents=[sub_common])
    release_activate.set_defaults(_post_validate="quick")
    release_activate.add_argument("--release", required=True, help="Release version (vX.Y.Z)")
    release_clear_parser = release_subparsers.add_parser(
        "clear",
        help="Clear the current release pointer",
        parents=[sub_common],
    )
    release_clear_parser.set_defaults(_post_validate="quick")
    release_list_parser = release_subparsers.add_parser("list", help="List release folders", parents=[sub_common])
    release_list_parser.set_defaults(_post_validate="never")
    release_status = release_subparsers.add_parser("status", help="Show release status", parents=[sub_common])
    release_status.set_defaults(_post_validate="never")
    release_status.add_argument("--release", help="Release version (vX.Y.Z or 'current'; default: current)")
    release_show = release_subparsers.add_parser(
        "show",
        help="Print release plan + computed status",
        parents=[sub_common],
    )
    release_show.set_defaults(_post_validate="never")
    release_show.add_argument("--release", help="Release version (vX.Y.Z or 'current'; default: current)")
    release_progress = release_subparsers.add_parser(
        "progress", help="Regenerate releases/<release>/progress.md", parents=[sub_common]
    )
    release_progress.set_defaults(_post_validate="never")
    release_progress.add_argument("--release", help="Release version (vX.Y.Z or 'current'; default: current)")
    release_draft = release_subparsers.add_parser(
        "draft",
        help="Draft a release composition (local-only; creates no files)",
        parents=[sub_common],
    )
    release_draft.set_defaults(_post_validate="never")
    release_draft.add_argument("--version", default="next", help="Release version (vX.Y.Z or 'next')")
    release_draft.add_argument("--sprints", type=int, default=3, help="Number of planned sprints (default: 3)")
    release_draft.add_argument(
        "--base",
        default="latest-delivered",
        help="Draft base (latest-delivered|current|vX.Y.Z)",
    )
    release_draft.add_argument("--format", default="text", help="Output format (text|json)")
    release_draft.add_argument("--schema", action="store_true", help="Print JSON schema for --format json and exit")
    release_add_feature = release_subparsers.add_parser(
        "add-feature", help="Assign a feature to a release", parents=[sub_common]
    )
    release_add_feature.set_defaults(_post_validate="quick")
    release_add_feature.add_argument("--release", required=True, help="Release version (vX.Y.Z)")
    release_add_feature.add_argument("--feature", required=True, help="Feature name")
    release_add_feature.add_argument("--slot", required=True, type=int, help="Sprint slot number (1..planned_sprints)")
    release_add_feature.add_argument(
        "--commitment",
        required=True,
        choices=["committed", "stretch"],
        help="Scope commitment for this release",
    )
    release_add_feature.add_argument(
        "--intent",
        required=True,
        choices=["deliver", "decide", "enable"],
        help="Slot intent for this feature",
    )
    release_add_feature.add_argument("--priority", default="P1", help="Priority (default: P1)")
    release_add_feature.add_argument("--epic", action="store_true", help="Mark feature as epic")
    release_add_feature.add_argument("--critical", action="store_true", help="Mark as critical path")
    release_suggest = release_subparsers.add_parser(
        "suggest", help="Suggest features for a release", parents=[sub_common]
    )
    release_suggest.set_defaults(_post_validate="never")
    release_suggest.add_argument("--version", required=True, help="Release version (vX.Y.Z)")
    release_close = release_subparsers.add_parser("close", help="Close a release", parents=[sub_common])
    release_close.set_defaults(_post_validate="quick")
    release_close.add_argument("--version", required=True, help="Release version (vX.Y.Z)")
    release_migrate = release_subparsers.add_parser(
        "migrate-slot-format",
        help="Migrate legacy release slot plans to strict slot sections",
        parents=[sub_common],
    )
    release_migrate.set_defaults(_post_validate="quick")
    release_migrate.add_argument("--release", required=True, help="Release version (vX.Y.Z)")
    release_migrate.add_argument("--diff", action="store_true", help="Print unified diff only")
    release_migrate.add_argument("--write-back", action="store_true", help="Write changes to plan.md and validate")

    daily_parser = subparsers.add_parser("daily", help="Manage daily status cadence", parents=[sub_common])
    daily_parser.set_defaults(_post_validate="never")
    daily_subparsers = daily_parser.add_subparsers(
        dest="daily_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    daily_generate = daily_subparsers.add_parser("generate", help="Generate daily status", parents=[sub_common])
    daily_generate.set_defaults(_post_validate="quick")
    daily_generate.add_argument("--force", action="store_true", help="Generate even on weekends or overwrite")
    daily_check = daily_subparsers.add_parser("check", help="Check daily status freshness", parents=[sub_common])
    daily_check.set_defaults(_post_validate="never")
    daily_check.add_argument("--verbose", action="store_true", help="Verbose output")

    validate_parser = subparsers.add_parser("validate", help="Validate handbook content", parents=[sub_common])
    validate_parser.set_defaults(_post_validate="never")
    validate_parser.add_argument("--quick", action="store_true", help="Skip heavyweight checks")
    validate_parser.add_argument(
        "--silent-success", action="store_true", help="Suppress output when there are no issues"
    )

    pre_exec_parser = subparsers.add_parser("pre-exec", help="Pre-execution lint/audit gate", parents=[sub_common])
    pre_exec_parser.set_defaults(_post_validate="never")
    pre_exec_subparsers = pre_exec_parser.add_subparsers(
        dest="pre_exec_command",
        title="Subcommands",
        metavar="<subcommand>",
    )
    pre_exec_lint = pre_exec_subparsers.add_parser("lint", help="Strict task-doc lint gate", parents=[sub_common])
    pre_exec_lint.set_defaults(_post_validate="never")
    pre_exec_audit = pre_exec_subparsers.add_parser(
        "audit",
        help="Capture evidence bundle + lint",
        parents=[sub_common],
    )
    pre_exec_audit.set_defaults(_post_validate="never")
    pre_exec_audit.add_argument("--sprint", help="Override sprint id (default: from sprints/current/plan.md)")
    pre_exec_audit.add_argument("--date", help="Override evidence date (default: today YYYY-MM-DD)")
    pre_exec_audit.add_argument("--evidence-dir", help="Override evidence directory path")
    return parser


def _handle_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    raise RuntimeError("doctor is dispatched by main()")


def main(argv: list[str] | None = None) -> int:
    invocation_args = list(argv) if argv is not None else sys.argv[1:]
    if invocation_args in (["--version"], ["-V"]):
        print(__version__)
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        return _handle_version(args)

    if args.command == "init":
        target_root = Path(getattr(args, "root", None) or Path.cwd()).resolve()
        try:
            exit_code = run_init(target_root=target_root, update_gitignore=bool(getattr(args, "gitignore", True)))
        except InitError as exc:
            print(str(exc), file=sys.stderr, end="")
            return 2

        return run_post_command_hook(
            ph_root=target_root,
            ctx=None,
            command="init",
            invocation_args=invocation_args,
            exit_code=exit_code,
            no_post_hook=bool(getattr(args, "no_post_hook", False)),
            no_history=bool(getattr(args, "no_history", False)),
            no_validate=bool(getattr(args, "no_validate", False)),
            post_validate_mode=str(getattr(args, "_post_validate", "quick")),
            env=os.environ,
        )

    try:
        ph_root = resolve_ph_root(override=getattr(args, "root", None))
    except RootResolutionError as exc:
        print(str(exc), file=sys.stderr, end="")
        return 2

    exit_code = 0
    ctx = None

    def _build_ctx() -> None:
        nonlocal ctx
        config = load_handbook_config(ph_root)
        validate_handbook_config(config)
        scope = resolve_scope(cli_scope=getattr(args, "scope", None))
        ctx = build_context(ph_root=ph_root, scope=scope)

    if args.command == "doctor":
        result = run_doctor(ph_root)
        stream = sys.stdout if result.exit_code == 0 else sys.stderr
        print(result.output, file=stream, end="")
        exit_code = result.exit_code
    else:
        try:
            if args.command != "help":
                _build_ctx()

            if args.command is None:
                parser.print_help()
                exit_code = 0
            elif args.command == "help":
                topic = str(args.topic).strip().lower() if args.topic is not None else None
                text = get_help_text(topic)
                if text is None:
                    print(f"Unknown help topic: {args.topic}\n", file=sys.stderr, end="")
                    exit_code = 2
                else:
                    cmd_args = ["help"]
                    if topic:
                        cmd_args.append(topic)
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    sys.stdout.write(text)
            elif args.command == "onboarding":
                if args.onboarding_command is None:
                    sys.stdout.write(render_onboarding(ph_data_root=ctx.ph_data_root))
                    exit_code = 0
                elif args.onboarding_command == "session":
                    session_topic = str(args.session_topic).strip() if args.session_topic is not None else ""
                    if session_topic == "list":
                        topics = list_session_topics(ph_data_root=ctx.ph_data_root)
                        print(SessionList(topics=topics).render(), end="")
                        print("ph: Nothing to be done for `list`.")
                        exit_code = 0
                    elif session_topic == "continue-session":
                        summary = read_latest_session_summary(ph_data_root=ctx.ph_data_root)
                        header = "SESSION CONTINUITY SUMMARY"
                        underline = "=" * len(header)
                        sys.stdout.write(f"{header}\n{underline}\n{summary}\n")
                        sys.stdout.write("ph: Nothing to be done for `continue-session`.\n")
                        exit_code = 0
                    else:
                        sys.stdout.write(render_session_template(ph_data_root=ctx.ph_data_root, topic=session_topic))
                        exit_code = 0
            elif args.command == "hooks":
                if args.hooks_command == "install":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["hooks", "install"]))
                    install_git_hooks(ph_root=ph_root)
                    sys.stdout.write("Git hooks installed!\n")
                    exit_code = 0
                else:
                    print("Unknown hooks command.\nUse: ph hooks install\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "reset":
                exit_code = run_reset(
                    ctx=ctx,
                    spec=str(getattr(args, "spec")),
                    confirm=str(getattr(args, "confirm")),
                    force=str(getattr(args, "force")),
                )
            elif args.command == "reset-smoke":
                exit_code = run_reset_smoke(ph_root=ph_root, ctx=ctx)
            elif args.command == "migrate":
                if getattr(args, "migrate_command", None) is None:
                    print("Usage: ph migrate <system-scope>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.migrate_command == "system-scope":
                    exit_code = run_migrate_system_scope(
                        ph_root=ph_root,
                        confirm=str(getattr(args, "confirm")),
                        force=str(getattr(args, "force")),
                    )
                else:
                    print("Usage: ph migrate <system-scope>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "end-session":
                _ = args.session_id  # parsed for parity; log selection is explicit in v1
                _ = args.session_end_codex  # parsed for parity; not exercised in tests
                _ = args.session_end_codex_model  # parsed for parity; not exercised in tests

                overrides: dict[str, str] = {}
                if getattr(args, "reasoning_effort", None):
                    overrides["model_reasoning_effort"] = args.reasoning_effort
                if getattr(args, "reasoning_summary", None):
                    overrides["model_reasoning_summary"] = args.reasoning_summary
                if getattr(args, "model_verbosity", None):
                    overrides["model_verbosity"] = args.model_verbosity

                if args.skip_codex:
                    run_end_session_skip_codex(
                        ph_root=ph_root,
                        log_path=Path(args.log),
                        force=bool(args.force),
                        session_end_mode=str(args.session_end_mode),
                        workstream=getattr(args, "workstream", None),
                        task_ref=getattr(args, "task_ref", None),
                    )
                    exit_code = 0
                else:
                    run_end_session_codex(
                        ph_root=ph_root,
                        log_path=Path(args.log),
                        model=getattr(args, "codex_model", None),
                        overrides=overrides,
                        force=bool(args.force),
                        session_end_mode=str(args.session_end_mode),
                        workstream=getattr(args, "workstream", None),
                        task_ref=getattr(args, "task_ref", None),
                    )
                    exit_code = 0
            elif args.command == "clean":
                if ctx.scope == "project":
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["clean"]))
                    sys.stdout.flush()
                clean_python_caches(ph_root=ph_root)
                print("Cleaned Python cache files\n", end="")
                exit_code = 0
            elif args.command == "status":
                if ctx.scope == "project":
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["status"]))
                    sys.stdout.flush()

                status_result = run_status(
                    ph_root=ph_root,
                    ph_project_root=ctx.ph_project_root,
                    ph_data_root=ctx.ph_data_root,
                    env=os.environ,
                )
                print(f"Generated: {status_result.json_path.resolve()}")
                print(f"Updated: {status_result.summary_path.resolve()}")

                summary_text = status_result.summary_path.read_text(encoding="utf-8").rstrip("\n")
                if summary_text.strip():
                    print()
                    print("===== status/current_summary.md =====")
                    print()
                    print(summary_text)
                    print()
                    print("====================================")
                    print()
                if status_result.feature_update_message:
                    print(status_result.feature_update_message)
            elif args.command == "dashboard":
                if ctx.scope == "project":
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["dashboard"]))
                    sys.stdout.flush()
                exit_code = run_dashboard(ph_root=ph_root, ctx=ctx)
            elif args.command == "process":
                if getattr(args, "process_command", None) is None:
                    print("Usage: ph process <refresh>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.process_command == "refresh":
                    if ctx.scope == "project":
                        cmd_args = ["process", "refresh"]
                        if bool(getattr(args, "templates", False)):
                            cmd_args.append("--templates")
                        if bool(getattr(args, "playbooks", False)):
                            cmd_args.append("--playbooks")
                        if bool(getattr(args, "force", False)):
                            cmd_args.append("--force")
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                        sys.stdout.flush()
                    exit_code = run_process_refresh(
                        ctx=ctx,
                        templates=bool(getattr(args, "templates", False)),
                        playbooks=bool(getattr(args, "playbooks", False)),
                        force=bool(getattr(args, "force", False)),
                        env=os.environ,
                    )
                else:
                    print("Usage: ph process <refresh>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "question":
                if getattr(args, "question_command", None) is None:
                    print("Usage: ph question <add|list|show|answer|close>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.question_command == "add":
                    exit_code = run_question_add(
                        ctx=ctx,
                        title=str(getattr(args, "title")),
                        severity=str(getattr(args, "severity")),
                        scope=str(getattr(args, "question_scope")),
                        sprint=getattr(args, "sprint", None),
                        task_id=getattr(args, "task_id", None),
                        release=getattr(args, "release", None),
                        asked_by=getattr(args, "asked_by", None),
                        owner=getattr(args, "owner", None),
                        body=str(getattr(args, "body", "")),
                        env=os.environ,
                    )
                elif args.question_command == "list":
                    exit_code = run_question_list(
                        ctx=ctx,
                        status=str(getattr(args, "status", "open")),
                        format=str(getattr(args, "format", "table")),
                        env=os.environ,
                    )
                elif args.question_command == "show":
                    exit_code = run_question_show(ctx=ctx, qid=str(getattr(args, "id")), env=os.environ)
                elif args.question_command == "answer":
                    exit_code = run_question_answer(
                        ctx=ctx,
                        qid=str(getattr(args, "id")),
                        answer=str(getattr(args, "answer")),
                        by=getattr(args, "by", None),
                        env=os.environ,
                    )
                elif args.question_command == "close":
                    exit_code = run_question_close(
                        ctx=ctx,
                        qid=str(getattr(args, "id")),
                        resolution=str(getattr(args, "resolution")),
                        env=os.environ,
                    )
                else:
                    print("Usage: ph question <add|list|show|answer|close>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "check-all":
                if ctx.scope == "project":
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["check-all"]))
                    sys.stdout.flush()
                exit_code = run_check_all(ph_root=ph_root, ctx=ctx, env=os.environ)
            elif args.command == "test":
                if getattr(args, "test_command", None) is None:
                    print("Usage: ph test <system>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.test_command == "system":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["test", "system"]))
                        sys.stdout.flush()
                    exit_code = run_test_system(ph_root=ph_root, ctx=ctx, env=os.environ)
                else:
                    print("Usage: ph test <system>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "sprint":
                if args.sprint_command is None:
                    print(
                        "Usage: ph sprint <plan|open|status|tasks|burndown|capacity|archive|close>\n",
                        file=sys.stderr,
                        end="",
                    )
                    exit_code = 2
                elif args.sprint_command == "plan":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "plan"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        if bool(getattr(args, "force", False)):
                            cmd_args.append("--force")
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = sprint_plan(
                        ph_root=ph_root,
                        ctx=ctx,
                        sprint_id=getattr(args, "sprint", None),
                        force=bool(getattr(args, "force", False)),
                        env=os.environ,
                    )
                elif args.sprint_command == "open":
                    sprint_id = str(args.sprint)
                    if ctx.scope == "project":
                        sys.stdout.write(
                            _format_cli_preamble(
                                ph_root=ph_root,
                                cmd_args=["sprint", "open", "--sprint", sprint_id],
                            )
                        )
                    exit_code = sprint_open(ph_root=ph_root, ctx=ctx, sprint_id=sprint_id)
                elif args.sprint_command == "status":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "status"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_sprint_status(
                        ph_project_root=ctx.ph_project_root, ctx=ctx, sprint=getattr(args, "sprint", None)
                    )
                elif args.sprint_command == "tasks":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "tasks"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_sprint_tasks(ctx=ctx, sprint=getattr(args, "sprint", None))
                elif args.sprint_command == "burndown":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "burndown"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_sprint_burndown(
                        ph_project_root=ctx.ph_project_root,
                        ctx=ctx,
                        sprint=getattr(args, "sprint", None),
                        env=os.environ,
                    )
                elif args.sprint_command == "capacity":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "capacity"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_sprint_capacity(
                        ph_root=ph_root,
                        ctx=ctx,
                        sprint=getattr(args, "sprint", None),
                        env=os.environ,
                    )
                elif args.sprint_command == "archive":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "archive"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_sprint_archive(
                        ph_root=ph_root,
                        ctx=ctx,
                        sprint=getattr(args, "sprint", None),
                        env=os.environ,
                    )
                elif args.sprint_command == "close":
                    if ctx.scope == "project":
                        cmd_args = ["sprint", "close"]
                        sprint_id = getattr(args, "sprint", None)
                        if sprint_id:
                            cmd_args.extend(["--sprint", str(sprint_id)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_sprint_close(
                        ph_project_root=ctx.ph_project_root,
                        ctx=ctx,
                        sprint=getattr(args, "sprint", None),
                        env=os.environ,
                    )
                else:
                    print(
                        "Usage: ph sprint <plan|open|status|tasks|burndown|capacity|archive|close>\n",
                        file=sys.stderr,
                        end="",
                    )
                    exit_code = 2
            elif args.command == "task":
                if args.task_command is None:
                    print("Usage: ph task <create|list|show|status>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.task_command == "create":
                    if ctx.scope == "project":
                        cmd_args = [
                            "task",
                            "create",
                            "--title",
                            str(args.title),
                            "--feature",
                            str(args.feature),
                            "--decision",
                            str(args.decision),
                        ]
                        if "--points" in invocation_args and getattr(args, "points", None) is not None:
                            cmd_args.extend(["--points", str(args.points)])
                        if "--owner" in invocation_args:
                            cmd_args.extend(["--owner", str(args.owner)])
                        if "--prio" in invocation_args:
                            cmd_args.extend(["--prio", str(args.prio)])
                        if "--lane" in invocation_args and getattr(args, "lane", None) is not None:
                            cmd_args.extend(["--lane", str(args.lane)])
                        if "--type" in invocation_args or "--task-type" in invocation_args:
                            cmd_args.extend(["--type", str(getattr(args, "task_type", ""))])
                        if "--session" in invocation_args:
                            cmd_args.extend(["--session", str(args.session)])
                        if "--release" in invocation_args and getattr(args, "release", None) is not None:
                            cmd_args.extend(["--release", str(args.release)])
                        if "--gate" in invocation_args and bool(getattr(args, "gate", False)):
                            cmd_args.append("--gate")

                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))

                    exit_code = run_task_create(
                        ph_root=ph_root,
                        ctx=ctx,
                        title=str(args.title),
                        feature=str(args.feature),
                        decision=str(args.decision),
                        points=getattr(args, "points", None),
                        owner=str(args.owner),
                        prio=str(args.prio),
                        lane=getattr(args, "lane", None),
                        session=str(args.session),
                        session_was_provided=("--session" in invocation_args),
                        task_type=getattr(args, "task_type", None),
                        release=getattr(args, "release", None),
                        gate=bool(getattr(args, "gate", False)),
                        env=os.environ,
                    )
                elif args.task_command == "list":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["task", "list"]))
                    exit_code = run_task_list(ctx=ctx)
                elif args.task_command == "show":
                    if ctx.scope == "project":
                        sys.stdout.write(
                            _format_cli_preamble(
                                ph_root=ph_root,
                                cmd_args=["task", "show", "--id", str(args.id)],
                            )
                        )
                    exit_code = run_task_show(ctx=ctx, task_id=str(args.id))
                elif args.task_command == "status":
                    if ctx.scope == "project":
                        cmd_args = [
                            "task",
                            "status",
                            "--id",
                            str(args.id),
                            "--status",
                            str(args.status),
                        ]
                        if "--force" in invocation_args and bool(getattr(args, "force", False)):
                            cmd_args.append("--force")

                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))

                    exit_code = run_task_status(
                        ctx=ctx,
                        task_id=str(args.id),
                        new_status=str(args.status),
                        force=bool(getattr(args, "force", False)),
                    )
                else:
                    print("Usage: ph task <create|list|show|status>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "feature":
                if args.feature_command is None:
                    print(
                        "Usage: ph feature <create|list|status|update-status|summary|archive>\n",
                        file=sys.stderr,
                        end="",
                    )
                    exit_code = 2
                elif args.feature_command == "create":
                    if ctx.scope == "project":
                        cmd_args = ["feature", "create", "--name", str(args.name)]
                        if "--epic" in invocation_args and bool(getattr(args, "epic", False)):
                            cmd_args.append("--epic")
                        if "--owner" in invocation_args:
                            cmd_args.extend(["--owner", str(args.owner)])
                        if "--stage" in invocation_args:
                            cmd_args.extend(["--stage", str(args.stage)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_feature_create(
                        ph_root=ph_root,
                        ctx=ctx,
                        name=str(args.name),
                        epic=bool(getattr(args, "epic", False)),
                        owner=str(args.owner),
                        stage=str(args.stage),
                        env=os.environ,
                    )
                elif args.feature_command == "list":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["feature", "list"]))
                    exit_code = run_feature_list(ctx=ctx)
                elif args.feature_command == "status":
                    if ctx.scope == "project":
                        sys.stdout.write(
                            _format_cli_preamble(
                                ph_root=ph_root,
                                cmd_args=["feature", "status", "--name", str(args.name), "--stage", str(args.stage)],
                            )
                        )
                    exit_code = run_feature_status(
                        ctx=ctx,
                        name=str(args.name),
                        stage=str(args.stage),
                        env=os.environ,
                    )
                elif args.feature_command == "update-status":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["feature", "update-status"]))
                    exit_code = run_feature_update_status(ctx=ctx, env=os.environ)
                elif args.feature_command == "summary":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["feature", "summary"]))
                    exit_code = run_feature_summary(ctx=ctx, env=os.environ)
                elif args.feature_command == "archive":
                    if ctx.scope == "project":
                        cmd_args = ["feature", "archive", "--name", str(args.name)]
                        if bool(getattr(args, "force", False)):
                            cmd_args.append("--force")
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_feature_archive(
                        ctx=ctx,
                        name=str(args.name),
                        force=bool(getattr(args, "force", False)),
                    )
                else:
                    print(
                        "Usage: ph feature <create|list|status|update-status|summary|archive>\n",
                        file=sys.stderr,
                        end="",
                    )
                    exit_code = 2
            elif args.command == "adr":
                if getattr(args, "adr_command", None) is None:
                    print("Usage: ph adr <add|list>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.adr_command == "add":
                    if ctx.scope == "project":
                        cmd_args = [
                            "adr",
                            "add",
                            "--id",
                            str(getattr(args, "id")),
                            "--title",
                            str(getattr(args, "title")),
                        ]
                        for dr_id in list(getattr(args, "dr", []) or []):
                            cmd_args.extend(["--dr", str(dr_id)])
                        if "--status" in invocation_args:
                            cmd_args.extend(["--status", str(getattr(args, "status"))])
                        if "--superseded-by" in invocation_args and getattr(args, "superseded_by", None) is not None:
                            cmd_args.extend(["--superseded-by", str(getattr(args, "superseded_by"))])
                        if "--date" in invocation_args and getattr(args, "date", None) is not None:
                            cmd_args.extend(["--date", str(getattr(args, "date"))])
                        if "--force" in invocation_args and bool(getattr(args, "force", False)):
                            cmd_args.append("--force")
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))

                    exit_code = run_adr_add(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        adr_id=str(getattr(args, "id")),
                        title=str(getattr(args, "title")),
                        dr=[str(value) for value in list(getattr(args, "dr", []) or [])],
                        status=str(getattr(args, "status")),
                        date=getattr(args, "date", None),
                        superseded_by=getattr(args, "superseded_by", None),
                        force=bool(getattr(args, "force", False)),
                    )
                elif args.adr_command == "list":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["adr", "list"]))
                    exit_code = run_adr_list(ph_data_root=ctx.ph_data_root)
                else:
                    print("Usage: ph adr <add|list>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "dr":
                if getattr(args, "dr_command", None) is None:
                    print("Usage: ph dr <add>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.dr_command == "add":
                    if ctx.scope == "project":
                        cmd_args = [
                            "dr",
                            "add",
                            "--id",
                            str(getattr(args, "id")),
                            "--title",
                            str(getattr(args, "title")),
                        ]
                        if "--feature" in invocation_args and getattr(args, "feature", None) is not None:
                            cmd_args.extend(["--feature", str(getattr(args, "feature"))])
                        if "--date" in invocation_args and getattr(args, "date", None) is not None:
                            cmd_args.extend(["--date", str(getattr(args, "date"))])
                        if "--force" in invocation_args and bool(getattr(args, "force", False)):
                            cmd_args.append("--force")
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))

                    exit_code = run_dr_add(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        dr_id=str(getattr(args, "id")),
                        title=str(getattr(args, "title")),
                        feature=getattr(args, "feature", None),
                        date=getattr(args, "date", None),
                        force=bool(getattr(args, "force", False)),
                    )
                else:
                    print("Usage: ph dr <add>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "fdr":
                if getattr(args, "fdr_command", None) is None:
                    print("Usage: ph fdr <add>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.fdr_command == "add":
                    if ctx.scope == "project":
                        cmd_args = [
                            "fdr",
                            "add",
                            "--feature",
                            str(getattr(args, "feature")),
                            "--id",
                            str(getattr(args, "id")),
                            "--title",
                            str(getattr(args, "title")),
                        ]
                        for dr_id in list(getattr(args, "dr", []) or []):
                            cmd_args.extend(["--dr", str(dr_id)])
                        if "--date" in invocation_args and getattr(args, "date", None) is not None:
                            cmd_args.extend(["--date", str(getattr(args, "date"))])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))

                    exit_code = run_fdr_add(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        feature=str(getattr(args, "feature")),
                        fdr_id=str(getattr(args, "id")),
                        title=str(getattr(args, "title")),
                        dr=[str(value) for value in list(getattr(args, "dr", []) or [])],
                        date=getattr(args, "date", None),
                    )
                else:
                    print("Usage: ph fdr <add>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "backlog":
                if args.backlog_command is None:
                    print("Usage: ph backlog <add|list|triage|assign|rubric|stats>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.backlog_command == "add":
                    if ctx.scope == "project":
                        cmd_args = [
                            "backlog",
                            "add",
                            "--type",
                            str(args.issue_type),
                            "--title",
                            str(args.title),
                            "--severity",
                            str(args.severity),
                        ]
                        if "--desc" in invocation_args and str(getattr(args, "desc", "") or "") != "":
                            cmd_args.extend(["--desc", str(args.desc)])
                        if "--owner" in invocation_args and str(getattr(args, "owner", "") or "") != "":
                            cmd_args.extend(["--owner", str(args.owner)])
                        if "--impact" in invocation_args and str(getattr(args, "impact", "") or "") != "":
                            cmd_args.extend(["--impact", str(args.impact)])
                        if "--workaround" in invocation_args and str(getattr(args, "workaround", "") or "") != "":
                            cmd_args.extend(["--workaround", str(args.workaround)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_backlog_add(
                        ctx=ctx,
                        issue_type=str(args.issue_type),
                        title=str(args.title),
                        severity=str(args.severity),
                        desc=str(args.desc),
                        owner=str(args.owner),
                        impact=str(args.impact),
                        workaround=str(args.workaround),
                        env=os.environ,
                    )
                elif args.backlog_command == "list":
                    if ctx.scope == "project" and str(args.format) != "json":
                        cmd_args = ["backlog", "list"]
                        if "--severity" in invocation_args and getattr(args, "severity", None) is not None:
                            cmd_args.extend(["--severity", str(args.severity)])
                        if "--category" in invocation_args and getattr(args, "category", None) is not None:
                            cmd_args.extend(["--category", str(args.category)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_backlog_list(
                        ctx=ctx,
                        severity=getattr(args, "severity", None),
                        category=getattr(args, "category", None),
                        format=str(args.format),
                        env=os.environ,
                    )
                elif args.backlog_command == "triage":
                    issue_id = str(args.issue_id)
                    if ctx.scope == "project":
                        sys.stdout.write(
                            _format_cli_preamble(
                                ph_root=ph_root,
                                cmd_args=["backlog", "triage", "--issue", issue_id],
                            )
                        )
                    exit_code = run_backlog_triage(
                        ctx=ctx,
                        issue_id=issue_id,
                        env=os.environ,
                        print_index_summary=ctx.scope == "project",
                    )
                elif args.backlog_command == "assign":
                    issue_id = str(args.issue_id)
                    sprint = str(getattr(args, "sprint", "current") or "current")
                    if ctx.scope == "project":
                        sys.stdout.write(
                            _format_cli_preamble(
                                ph_root=ph_root,
                                cmd_args=["backlog", "assign", "--issue", issue_id, "--sprint", sprint],
                            )
                        )
                    exit_code = run_backlog_assign(
                        ctx=ctx,
                        issue_id=issue_id,
                        sprint=sprint,
                        env=os.environ,
                    )
                elif args.backlog_command == "rubric":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["backlog", "rubric"]))
                    exit_code = run_backlog_rubric(ctx=ctx, env=os.environ)
                elif args.backlog_command == "stats":
                    if ctx.scope == "project":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["backlog", "stats"]))
                    exit_code = run_backlog_stats(ctx=ctx, env=os.environ)
                else:
                    print("Usage: ph backlog <add|list|triage|assign|rubric|stats>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "parking":
                if args.parking_command is None:
                    print("Usage: ph parking <add|list|review|promote>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.parking_command == "add":
                    if ctx.scope == "project":
                        cmd_args = [
                            "parking",
                            "add",
                            "--type",
                            str(args.parking_type),
                            "--title",
                            str(args.title),
                        ]
                        if "--desc" in invocation_args and str(getattr(args, "desc", "") or "") != "":
                            cmd_args.extend(["--desc", str(args.desc)])
                        if "--owner" in invocation_args and str(getattr(args, "owner", "") or "") != "":
                            cmd_args.extend(["--owner", str(args.owner)])
                        if "--tags" in invocation_args and str(getattr(args, "tags", "") or "") != "":
                            cmd_args.extend(["--tags", str(args.tags)])

                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))

                    exit_code = run_parking_add(
                        ctx=ctx,
                        item_type=str(args.parking_type),
                        title=str(args.title),
                        desc=str(args.desc),
                        owner=str(args.owner),
                        tags=str(getattr(args, "tags", "")),
                        env=os.environ,
                    )
                elif args.parking_command == "list":
                    if ctx.scope == "project" and str(args.format) != "json":
                        cmd_args = ["parking", "list"]
                        if "--category" in invocation_args and getattr(args, "category", None) is not None:
                            cmd_args.extend(["--category", str(args.category)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_parking_list(
                        ctx=ctx,
                        category=getattr(args, "category", None),
                        format=str(args.format),
                        env=os.environ,
                    )
                elif args.parking_command == "review":
                    output_format = str(getattr(args, "format", "text"))
                    if ctx.scope == "project" and output_format != "json":
                        cmd_args = ["parking", "review"]
                        if "--format" in invocation_args and getattr(args, "format", None) is not None:
                            cmd_args.extend(["--format", str(args.format)])
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    exit_code = run_parking_review(ctx=ctx, format=output_format, env=os.environ)
                elif args.parking_command == "promote":
                    if ctx.scope == "project":
                        sys.stdout.write(
                            _format_cli_preamble(
                                ph_root=ph_root,
                                cmd_args=[
                                    "parking",
                                    "promote",
                                    "--item",
                                    str(args.item),
                                    "--target",
                                    str(args.target),
                                ],
                            )
                        )
                    exit_code = run_parking_promote(
                        ctx=ctx,
                        item_id=str(args.item),
                        target=str(args.target),
                        env=os.environ,
                    )
                else:
                    print("Usage: ph parking <add|list|review|promote>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "roadmap":
                if ctx.scope == "project":
                    if getattr(args, "roadmap_command", None) in (None, "show"):
                        if getattr(args, "roadmap_command", None) is None:
                            cmd_args = ["roadmap"]
                        else:
                            cmd_args = ["roadmap", "show"]
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    elif args.roadmap_command == "create":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["roadmap", "create"]))
                    elif args.roadmap_command == "validate":
                        sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["roadmap", "validate"]))

                if args.roadmap_command is None:
                    exit_code = run_roadmap_show(ctx=ctx)
                elif args.roadmap_command == "show":
                    exit_code = run_roadmap_show(ctx=ctx)
                elif args.roadmap_command == "create":
                    exit_code = run_roadmap_create(ctx=ctx)
                elif args.roadmap_command == "validate":
                    exit_code = run_roadmap_validate(ctx=ctx)
                else:
                    print("Usage: ph roadmap <show|create|validate>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "release":
                if args.release_command is None:
                    print(
                        "Usage: ph release <plan|activate|clear|status|show|progress|draft|"
                        "list|add-feature|suggest|close|migrate-slot-format>\n",
                        file=sys.stderr,
                        end="",
                    )
                    exit_code = 2
                elif args.release_command == "plan":
                    exit_code = run_release_plan(
                        ctx=ctx,
                        version=getattr(args, "version", None),
                        bump=str(getattr(args, "bump", "patch")),
                        sprints=int(getattr(args, "sprints", 3)),
                        start_sprint=getattr(args, "start_sprint", None),
                        sprint_ids=getattr(args, "sprint_ids", None),
                        activate=bool(getattr(args, "activate", False)),
                        env=os.environ,
                    )
                elif args.release_command == "activate":
                    exit_code = run_release_activate(ctx=ctx, release=str(getattr(args, "release")), env=os.environ)
                elif args.release_command == "clear":
                    exit_code = run_release_clear(ctx=ctx)
                elif args.release_command == "list":
                    exit_code = run_release_list(ctx=ctx)
                elif args.release_command == "status":
                    exit_code = run_release_status(ctx=ctx, release=getattr(args, "release", None), env=os.environ)
                elif args.release_command == "show":
                    exit_code = run_release_show(ctx=ctx, release=getattr(args, "release", None), env=os.environ)
                elif args.release_command == "progress":
                    exit_code = run_release_progress(ctx=ctx, release=getattr(args, "release", None), env=os.environ)
                elif args.release_command == "draft":
                    exit_code = run_release_draft(
                        ctx=ctx,
                        version=str(getattr(args, "version", "next")),
                        sprints=int(getattr(args, "sprints", 3)),
                        base=str(getattr(args, "base", "latest-delivered")),
                        format=str(getattr(args, "format", "text")),
                        schema=bool(getattr(args, "schema", False)),
                    )
                elif args.release_command == "add-feature":
                    exit_code = run_release_add_feature(
                        ctx=ctx,
                        release=str(getattr(args, "release")),
                        feature=str(getattr(args, "feature")),
                        slot=int(getattr(args, "slot")),
                        commitment=str(getattr(args, "commitment")),
                        intent=str(getattr(args, "intent")),
                        priority=str(getattr(args, "priority", "P1")),
                        epic=bool(getattr(args, "epic", False)),
                        critical=bool(getattr(args, "critical", False)),
                    )
                elif args.release_command == "suggest":
                    exit_code = run_release_suggest(ctx=ctx, version=str(getattr(args, "version")))
                elif args.release_command == "close":
                    exit_code = run_release_close(ctx=ctx, version=str(getattr(args, "version")), env=os.environ)
                elif args.release_command == "migrate-slot-format":
                    exit_code = run_release_migrate_slot_format(
                        ctx=ctx,
                        release=str(getattr(args, "release")),
                        diff=bool(getattr(args, "diff", False)),
                        write_back=bool(getattr(args, "write_back", False)),
                        env=os.environ,
                    )
                else:
                    print(
                        "Usage: ph release <plan|activate|clear|status|show|progress|draft|"
                        "list|add-feature|suggest|close|migrate-slot-format>\n",
                        file=sys.stderr,
                        end="",
                    )
                    exit_code = 2
            elif args.command == "validate":
                cmd_args = ["validate"]
                if bool(args.quick):
                    cmd_args.append("--quick")
                if "--silent-success" in invocation_args and bool(args.silent_success):
                    cmd_args.append("--silent-success")
                exit_code, _out_path, message = run_validate(
                    ph_root=ph_root,
                    ph_project_root=ctx.ph_project_root,
                    ph_data_root=ctx.ph_data_root,
                    scope=ctx.scope,
                    quick=bool(args.quick),
                    silent_success=bool(args.silent_success),
                )
                if message:
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    print(message, end="")
            elif args.command == "pre-exec":
                if getattr(args, "pre_exec_command", None) is None:
                    print("Usage: ph pre-exec <lint|audit>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.pre_exec_command == "lint":
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=["pre-exec", "lint"]))
                    exit_code = run_pre_exec_lint(ctx=ctx)
                elif args.pre_exec_command == "audit":
                    cmd_args = ["pre-exec", "audit"]
                    sprint = getattr(args, "sprint", None)
                    date = getattr(args, "date", None)
                    evidence_dir = getattr(args, "evidence_dir", None)
                    if sprint:
                        cmd_args.extend(["--sprint", str(sprint)])
                    if date:
                        cmd_args.extend(["--date", str(date)])
                    if evidence_dir:
                        cmd_args.extend(["--evidence-dir", str(evidence_dir)])
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    try:
                        exit_code = run_pre_exec_audit(
                            ph_root=ph_root,
                            ctx=ctx,
                            sprint=sprint,
                            date=date,
                            evidence_dir=evidence_dir,
                        )
                    except PreExecError as exc:
                        print(f"\n❌ PRE-EXEC AUDIT FAILED: {exc}")
                        exit_code = 1
                else:
                    print("Usage: ph pre-exec <lint|audit>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "daily":
                if args.daily_command is None:
                    print("Usage: ph daily <generate|check>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.daily_command == "generate":
                    cmd_args = ["daily", "generate"]
                    if bool(getattr(args, "force", False)):
                        cmd_args.append("--force")
                    sys.stdout.write(_format_cli_preamble(ph_root=ph_root, cmd_args=cmd_args))
                    created = create_daily_status(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        force=bool(args.force),
                        env=os.environ,
                    )
                    exit_code = 0 if created else 1
                elif args.daily_command == "check":
                    if bool(getattr(args, "verbose", False)):
                        sys.stdout.write(
                            _format_cli_preamble(ph_root=ph_root, cmd_args=["daily", "check", "--verbose"])
                        )

                    exit_code = check_daily_status(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        verbose=bool(args.verbose),
                        env=os.environ,
                    )
                    if bool(getattr(args, "verbose", False)) and exit_code != 0:
                        sys.stdout.write("\u2009ELIFECYCLE\u2009 Command failed with exit code 2.\n")
                        exit_code = 2
                else:
                    print("Usage: ph daily <generate|check>\n", file=sys.stderr, end="")
                    exit_code = 2
            else:
                print(f"Unknown command: {args.command}\n", file=sys.stderr, end="")
                exit_code = 2
        except (ConfigError, ScopeError, OnboardingError, EndSessionError, ResetError) as exc:
            print(str(exc), file=sys.stderr, end="")
            exit_code = 2

    try:
        plan = plan_post_command_hook(
            command=args.command,
            exit_code=exit_code,
            no_post_hook=bool(getattr(args, "no_post_hook", False)),
            no_history=bool(getattr(args, "no_history", False)),
            no_validate=bool(getattr(args, "no_validate", False)),
            post_validate_mode=str(getattr(args, "_post_validate", "quick")),
            env=os.environ,
        )
        if plan.run_validation and ctx is None:
            _build_ctx()
    except (ConfigError, ScopeError) as exc:
        print(str(exc), file=sys.stderr, end="")
        exit_code = 2
        ctx = None

    return run_post_command_hook(
        ph_root=ph_root,
        ctx=ctx,
        command=args.command,
        invocation_args=invocation_args,
        exit_code=exit_code,
        no_post_hook=bool(getattr(args, "no_post_hook", False)),
        no_history=bool(getattr(args, "no_history", False)),
        no_validate=bool(getattr(args, "no_validate", False)),
        post_validate_mode=str(getattr(args, "_post_validate", "quick")),
        env=os.environ,
    )
