from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .context import Context
from .history import append_history, format_history_entry
from .validate_docs import run_validate


@dataclass(frozen=True)
class PostCommandHookPlan:
    append_history: bool
    run_validation: bool


def plan_post_command_hook(
    *,
    command: str | None,
    exit_code: int,
    no_post_hook: bool,
    no_history: bool,
    no_validate: bool,
    env: Mapping[str, str] | None = None,
) -> PostCommandHookPlan:
    env = env or os.environ

    if no_post_hook or env.get("PH_SKIP_POST_HOOK") == "1":
        return PostCommandHookPlan(append_history=False, run_validation=False)

    if command == "init" and exit_code == 0:
        return PostCommandHookPlan(append_history=False, run_validation=False)

    if exit_code == 0 and command in {"reset", "reset-smoke"}:
        return PostCommandHookPlan(append_history=False, run_validation=False)

    if exit_code == 0 and command == "help":
        return PostCommandHookPlan(append_history=not no_history, run_validation=False)

    append = not no_history

    if exit_code != 0:
        return PostCommandHookPlan(append_history=append, run_validation=False)

    if no_validate or command in {"validate", "reset", "reset-smoke"}:
        return PostCommandHookPlan(append_history=append, run_validation=False)

    return PostCommandHookPlan(append_history=append, run_validation=True)


def run_post_command_hook(
    *,
    ph_root: Path,
    ctx: Context | None,
    command: str | None,
    invocation_args: list[str],
    exit_code: int,
    no_post_hook: bool,
    no_history: bool,
    no_validate: bool,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> int:
    plan = plan_post_command_hook(
        command=command,
        exit_code=exit_code,
        no_post_hook=no_post_hook,
        no_history=no_history,
        no_validate=no_validate,
        env=env,
    )

    history_entry = format_history_entry(command=command, invocation_args=invocation_args)

    if plan.append_history:
        append_history(ph_root=ph_root, entry=history_entry, now=now)

    if not plan.run_validation:
        return exit_code

    if ctx is None:
        raise ValueError("ctx is required to run post-command validate-quick")

    validate_exit, _out_path, message = run_validate(
        ph_root=ctx.ph_root,
        ph_data_root=ctx.ph_data_root,
        scope=ctx.scope,
        quick=True,
        silent_success=True,
    )
    if message and command != "migrate":
        print(message, end="")

    return validate_exit
