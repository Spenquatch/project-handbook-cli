from __future__ import annotations

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
    def run(self, argv: list[str], *, no_post_hook: bool) -> int: ...


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
                ph_data_root=self.ctx.ph_data_root,
                scope=self.ctx.scope,
                quick=False,
                silent_success=False,
            )
            if message:
                print(message, end="")
            return exit_code

        if command == "status":
            out_json, out_summary = run_status(ph_root=self.ph_root, ph_data_root=self.ctx.ph_data_root)
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
            return run_sprint_status(ph_root=self.ph_root, ctx=self.ctx, sprint=None)

        if command == "feature" and args[:1] == ["list"]:
            return run_feature_list(ctx=self.ctx)

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

    runner = runner or DefaultCommandRunner(ph_root=ph_root, ctx=ctx, env=env)
    return _run_sequence(runner=runner, steps=[["validate"], ["status"]])


def run_test_system(*, ph_root: Path, ctx: Context, env: dict[str, str], runner: CommandRunner | None = None) -> int:
    if ctx.scope == "system":
        print("test system is project-scope only. Use: ph --scope project test system")
        return 1

    runner = runner or DefaultCommandRunner(ph_root=ph_root, ctx=ctx, env=env)
    return _run_sequence(
        runner=runner,
        steps=[
            ["validate"],
            ["status"],
            ["daily", "check", "--verbose"],
            ["sprint", "status"],
            ["feature", "list"],
            ["roadmap", "show"],
        ],
    )
