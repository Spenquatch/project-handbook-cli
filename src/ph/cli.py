from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .clean import clean_python_caches
from .config import ConfigError, load_handbook_config, validate_handbook_config
from .context import ScopeError, build_context, resolve_scope
from .daily import check_status as check_daily_status
from .daily import create_daily_status
from .dashboard import run_dashboard
from .doctor import run_doctor
from .end_session import EndSessionError, run_end_session_codex, run_end_session_skip_codex
from .git_hooks import install_git_hooks
from .help_text import get_help_text
from .hooks import plan_post_command_hook, run_post_command_hook
from .onboarding import (
    OnboardingError,
    SessionList,
    list_session_topics,
    read_latest_session_summary,
    read_onboarding_markdown,
    read_session_template,
)
from .root import RootResolutionError, resolve_ph_root
from .sprint_commands import sprint_open, sprint_plan
from .sprint_status import run_sprint_status
from .sprint_tasks import run_sprint_tasks
from .status import run_status
from .validate_docs import run_validate


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
    subparsers = parser.add_subparsers(dest="command")

    version_parser = subparsers.add_parser("version", help="Print installed ph version", parents=[sub_common])
    version_parser.set_defaults(_handler=_handle_version)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check repo compatibility and required assets",
        parents=[sub_common],
    )
    doctor_parser.set_defaults(_handler=_handle_doctor)

    help_parser = subparsers.add_parser("help", help="Show help topics", parents=[sub_common])
    help_parser.add_argument("topic", nargs="?", help="Help topic")

    onboarding_parser = subparsers.add_parser(
        "onboarding",
        help="Show onboarding docs and sessions",
        parents=[sub_common],
    )
    onboarding_subparsers = onboarding_parser.add_subparsers(dest="onboarding_command")
    onboarding_session = onboarding_subparsers.add_parser(
        "session",
        help="Show onboarding session templates",
        parents=[sub_common],
    )
    onboarding_session.add_argument("session_topic", nargs="?", help="Session topic (or 'list' / 'continue-session')")

    hooks_parser = subparsers.add_parser("hooks", help="Install repo git hooks", parents=[sub_common])
    hooks_subparsers = hooks_parser.add_subparsers(dest="hooks_command")
    hooks_subparsers.add_parser("install", help="Install repo git hooks", parents=[sub_common])

    end_session_parser = subparsers.add_parser(
        "end-session",
        help="Summarize a Codex session rollout log",
        parents=[sub_common],
    )
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

    subparsers.add_parser("clean", help="Remove Python cache files under PH_ROOT", parents=[sub_common])

    subparsers.add_parser("dashboard", help="Show sprint + validation snapshot", parents=[sub_common])
    subparsers.add_parser("status", help="Generate status rollup", parents=[sub_common])

    sprint_parser = subparsers.add_parser("sprint", help="Manage sprint lifecycle", parents=[sub_common])
    sprint_subparsers = sprint_parser.add_subparsers(dest="sprint_command")
    sprint_plan_parser = sprint_subparsers.add_parser("plan", help="Create sprint plan", parents=[sub_common])
    sprint_plan_parser.add_argument("--sprint", help="Sprint ID (default: computed)")
    sprint_plan_parser.add_argument("--force", action="store_true", help="Overwrite existing plan.md")
    sprint_open_parser = sprint_subparsers.add_parser(
        "open", help="Set current sprint to existing", parents=[sub_common]
    )
    sprint_open_parser.add_argument("--sprint", required=True, help="Sprint ID to open")
    sprint_status_parser = sprint_subparsers.add_parser("status", help="Show sprint status", parents=[sub_common])
    sprint_status_parser.add_argument("--sprint", help="Sprint ID (default: current)")
    sprint_tasks_parser = sprint_subparsers.add_parser("tasks", help="List sprint tasks", parents=[sub_common])
    sprint_tasks_parser.add_argument("--sprint", help="Sprint ID (default: current)")

    daily_parser = subparsers.add_parser("daily", help="Manage daily status cadence", parents=[sub_common])
    daily_subparsers = daily_parser.add_subparsers(dest="daily_command")
    daily_generate = daily_subparsers.add_parser("generate", help="Generate daily status", parents=[sub_common])
    daily_generate.add_argument("--force", action="store_true", help="Generate even on weekends or overwrite")
    daily_check = daily_subparsers.add_parser("check", help="Check daily status freshness", parents=[sub_common])
    daily_check.add_argument("--verbose", action="store_true", help="Verbose output")

    validate_parser = subparsers.add_parser("validate", help="Validate handbook content", parents=[sub_common])
    validate_parser.add_argument("--quick", action="store_true", help="Skip heavyweight checks")
    validate_parser.add_argument(
        "--silent-success", action="store_true", help="Suppress output when there are no issues"
    )
    return parser


def _handle_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    raise RuntimeError("doctor is dispatched by main()")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    invocation_args = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(argv)

    if args.command == "version":
        return _handle_version(args)

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
                    print(text, end="")
            elif args.command == "onboarding":
                if args.onboarding_command is None:
                    print(read_onboarding_markdown(ph_root=ph_root), end="")
                    exit_code = 0
                elif args.onboarding_command == "session":
                    session_topic = str(args.session_topic).strip() if args.session_topic is not None else ""
                    if session_topic == "list":
                        topics = list_session_topics(ph_root=ph_root)
                        print(SessionList(topics=topics).render(), end="")
                        exit_code = 0
                    elif session_topic == "continue-session":
                        print(read_latest_session_summary(ph_root=ph_root), end="")
                        exit_code = 0
                    else:
                        print(read_session_template(ph_root=ph_root, topic=session_topic), end="")
                        exit_code = 0
            elif args.command == "hooks":
                if args.hooks_command == "install":
                    install_git_hooks(ph_root=ph_root)
                    exit_code = 0
                else:
                    print("Unknown hooks command.\nUse: ph hooks install\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "end-session":
                _ = args.force  # parsed for parity; skip-codex mode does not enforce cwd matching
                _ = args.session_id  # parsed for parity; log selection is explicit in v1
                _ = args.task_ref  # parsed for parity; session_end artifacts are minimal in v1
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
                        session_end_mode=str(args.session_end_mode),
                        workstream=getattr(args, "workstream", None),
                    )
                    exit_code = 0
                else:
                    run_end_session_codex(
                        ph_root=ph_root,
                        log_path=Path(args.log),
                        model=getattr(args, "codex_model", None),
                        overrides=overrides,
                        session_end_mode=str(args.session_end_mode),
                        workstream=getattr(args, "workstream", None),
                    )
                    exit_code = 0
            elif args.command == "clean":
                clean_python_caches(ph_root=ph_root)
                print("Cleaned Python cache files\n", end="")
                exit_code = 0
            elif args.command == "status":
                out_json, out_summary = run_status(ph_root=ph_root, ph_data_root=ctx.ph_data_root)
                print(f"Generated: {out_json.resolve()}")
                print(f"Updated: {out_summary.resolve()}")

                summary_text = out_summary.read_text(encoding="utf-8").rstrip("\n")
                if summary_text.strip():
                    print()
                    print("===== status/current_summary.md =====")
                    print()
                    print(summary_text)
                    print()
                    print("====================================")
                    print()
            elif args.command == "dashboard":
                exit_code = run_dashboard(ph_root=ph_root, ctx=ctx)
            elif args.command == "sprint":
                if args.sprint_command is None:
                    print("Usage: ph sprint <plan|open|status|tasks>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.sprint_command == "plan":
                    exit_code = sprint_plan(
                        ph_root=ph_root,
                        ctx=ctx,
                        sprint_id=getattr(args, "sprint", None),
                        force=bool(getattr(args, "force", False)),
                        env=os.environ,
                    )
                elif args.sprint_command == "open":
                    exit_code = sprint_open(ph_root=ph_root, ctx=ctx, sprint_id=str(args.sprint))
                elif args.sprint_command == "status":
                    exit_code = run_sprint_status(ph_root=ph_root, ctx=ctx, sprint=getattr(args, "sprint", None))
                elif args.sprint_command == "tasks":
                    exit_code = run_sprint_tasks(ctx=ctx, sprint=getattr(args, "sprint", None))
                else:
                    print("Usage: ph sprint <plan|open|status|tasks>\n", file=sys.stderr, end="")
                    exit_code = 2
            elif args.command == "validate":
                exit_code, _out_path, message = run_validate(
                    ph_root=ph_root,
                    ph_data_root=ctx.ph_data_root,
                    scope=ctx.scope,
                    quick=bool(args.quick),
                    silent_success=bool(args.silent_success),
                )
                if message:
                    print(message, end="")
            elif args.command == "daily":
                if args.daily_command is None:
                    print("Usage: ph daily <generate|check>\n", file=sys.stderr, end="")
                    exit_code = 2
                elif args.daily_command == "generate":
                    created = create_daily_status(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        force=bool(args.force),
                        env=os.environ,
                    )
                    exit_code = 0 if created else 1
                elif args.daily_command == "check":
                    exit_code = check_daily_status(
                        ph_root=ph_root,
                        ph_data_root=ctx.ph_data_root,
                        verbose=bool(args.verbose),
                        env=os.environ,
                    )
                else:
                    print("Usage: ph daily <generate|check>\n", file=sys.stderr, end="")
                    exit_code = 2
            else:
                print(f"Unknown command: {args.command}\n", file=sys.stderr, end="")
                exit_code = 2
        except (ConfigError, ScopeError, OnboardingError, EndSessionError) as exc:
            print(str(exc), file=sys.stderr, end="")
            exit_code = 2

    try:
        plan = plan_post_command_hook(
            command=args.command,
            exit_code=exit_code,
            no_post_hook=bool(getattr(args, "no_post_hook", False)),
            no_history=bool(getattr(args, "no_history", False)),
            no_validate=bool(getattr(args, "no_validate", False)),
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
        env=os.environ,
    )
