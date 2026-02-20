from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .context import Context
from .daily import check_status as check_daily_status
from .feature import run_feature_list
from .roadmap import run_roadmap_show
from .sprint_status import run_sprint_status
from .status import run_status
from .validate_docs import run_validate


class CommandRunner(Protocol):
    def run(self, argv: list[str], *, no_post_hook: bool) -> int:
        ...


@dataclass(frozen=True)
class DefaultCommandRunner:
    ph_root: Path
    ctx: Context
    env: dict[str, str]

    def run(self, argv: list[str], *, no_post_hook: bool) -> int:
        if not argv:
            return 2

        command = argv[0]
        args = argv[1:]

        if command == "validate":
            exit_code, _out_path, message = run_validate(
                ph_root=self.ph_root,
                ph_project_root=self.ctx.ph_project_root,
                ph_data_root=self.ctx.ph_data_root,
                scope=self.ctx.scope,
                quick=False,
                silent_success=False,
            )
            if message:
                print(message, end="")
            return exit_code

        if command == "status":
            status_result = run_status(
                ph_root=self.ph_root,
                ph_project_root=self.ctx.ph_project_root,
                ph_data_root=self.ctx.ph_data_root,
                env=self.env,
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
            return 0

        if command == "daily" and args[:1] == ["check"]:
            verbose = "--verbose" in args
            return check_daily_status(
                ph_root=self.ph_root,
                ph_data_root=self.ctx.ph_data_root,
                verbose=verbose,
                env=self.env,
            )

        if command == "sprint" and args[:1] == ["status"]:
            return run_sprint_status(ph_project_root=self.ctx.ph_project_root, ctx=self.ctx, sprint=None)

        if command == "feature" and args[:1] == ["list"]:
            return run_feature_list(ctx=self.ctx, with_preamble=False)

        if command == "roadmap" and args[:1] == ["show"]:
            return run_roadmap_show(ctx=self.ctx)

        return 2


def _run_sequence(*, runner: CommandRunner, steps: list[list[str]]) -> int:
    for argv in steps:
        exit_code = runner.run(argv, no_post_hook=True)
        if exit_code != 0:
            return exit_code
    return 0


def run_check_all(*, ph_root: Path, ctx: Context, env: dict[str, str], runner: CommandRunner | None = None) -> int:
    if ctx.scope == "system":
        print("check-all is project-scope only. Use: ph --scope project check-all")
        return 1

    if runner is not None:
        runner.run(["validate"], no_post_hook=True)
        status_code = runner.run(["status"], no_post_hook=True)
        if status_code != 0:
            return status_code
        print("✅ All checks complete")
        return 0

    exit_code, _out_path, message = run_validate(
        ph_root=ph_root,
        ph_project_root=ctx.ph_project_root,
        ph_data_root=ctx.ph_data_root,
        scope=ctx.scope,
        quick=False,
        silent_success=False,
    )
    if message:
        print(message, end="")
    if exit_code != 0:
        exit_code = 0

    current_json = ctx.ph_data_root / "status" / "current.json"
    try:
        status_result = run_status(
            ph_root=ph_root,
            ph_project_root=ctx.ph_project_root,
            ph_data_root=ctx.ph_data_root,
            env=env,
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
    except Exception:
        if current_json.exists():
            print(f"Generated: {current_json.resolve()}")
        traceback.print_exc()
        print("ph: *** [status] Error 1", file=sys.stderr)
        print("ph: *** [__ph_dispatch] Error 2", file=sys.stderr)
        print("\u2009ELIFECYCLE\u2009 Command failed with exit code 2.")
        if (ph_root / "package.json").exists() and not (ph_root / "node_modules").exists():
            print("\u2009WARN\u2009  Local package.json exists, but node_modules missing, did you mean to install?")
        return 2

    print("✅ All checks complete")
    return 0


def run_test_system(*, ph_root: Path, ctx: Context, env: dict[str, str], runner: CommandRunner | None = None) -> int:
    if ctx.scope == "system":
        print("test system is project-scope only. Use: ph --scope project test system")
        return 1

    def _print_ph_failure() -> None:
        print("ph: *** [test system] Error 1", file=sys.stderr)
        print("ph: *** [__ph_dispatch] Error 2", file=sys.stderr)
        print("\u2009ELIFECYCLE\u2009 Command failed with exit code 2.")
        if (ph_root / "package.json").exists() and not (ph_root / "node_modules").exists():
            print("\u2009WARN\u2009  Local package.json exists, but node_modules missing, did you mean to install?")

    runner = runner or DefaultCommandRunner(ph_root=ph_root, ctx=ctx, env=env)

    print("Testing validation...")
    exit_code = runner.run(["validate"], no_post_hook=True)
    if exit_code != 0:
        exit_code = 0
    print()

    print("Testing status generation...")
    current_json = ctx.ph_data_root / "status" / "current.json"
    try:
        exit_code = runner.run(["status"], no_post_hook=True)
    except Exception:
        if current_json.exists():
            print(f"Generated: {current_json.resolve()}")
        traceback.print_exc()
        _print_ph_failure()
        return 2
    if exit_code != 0:
        _print_ph_failure()
        return 2
    print()

    print("Testing daily status check...")
    exit_code = runner.run(["daily", "check", "--verbose"], no_post_hook=True)
    if exit_code != 0:
        print("  (Expected - no daily status yet)")
    print()

    print("Testing sprint status...")
    exit_code = runner.run(["sprint", "status"], no_post_hook=True)
    if exit_code != 0:
        _print_ph_failure()
        return 2
    print()

    print("Testing feature management...")
    exit_code = runner.run(["feature", "list"], no_post_hook=True)
    if exit_code != 0:
        _print_ph_failure()
        return 2
    print()

    print("Testing roadmap...")
    exit_code = runner.run(["roadmap", "show"], no_post_hook=True)
    if exit_code != 0:
        _print_ph_failure()
        return 2
    print()

    print("✅ All systems operational")
    return 0
