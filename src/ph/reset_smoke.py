from __future__ import annotations

import os
import sys
from pathlib import Path

from .context import Context, build_context
from .feature import run_feature_create
from .reset import run_reset
from .sprint_commands import sprint_plan
from .task_create import run_task_create
from .validate_docs import run_validate


def _assert_exists(path: Path, label: str) -> int:
    if path.exists():
        return 0
    print(f"❌ Reset smoke failed: expected to exist: {label} ({path})", file=sys.stderr)
    return 1


def _assert_not_exists(path: Path, label: str) -> int:
    if not path.exists():
        return 0
    print(f"❌ Reset smoke failed: expected to be absent: {label} ({path})", file=sys.stderr)
    return 1


def run_reset_smoke(*, ph_root: Path, ctx: Context, include_system: bool) -> int:
    if ctx.scope == "system":
        print("reset-smoke is project-scope only. Use: ph --scope project reset-smoke ...")
        return 1

    env = dict(os.environ)
    system_ctx = build_context(ph_root=ph_root, scope="system")

    print("Running reset smoke verification: docs/RESET_SMOKE.md")

    # Step 1: Create system-scope artifacts.
    sys_feature_dir = system_ctx.ph_data_root / "features" / "handbook-reset-smoke"
    if not sys_feature_dir.exists():
        rc = run_feature_create(
            ph_root=ph_root,
            ctx=system_ctx,
            name="handbook-reset-smoke",
            epic=False,
            owner="@owner",
            stage="proposed",
            env=env,
        )
        if rc != 0:
            return rc

    rc = sprint_plan(ph_root=ph_root, ctx=system_ctx, sprint_id="SPRINT-2099-01-01", force=False, env=env)
    if rc != 0:
        return rc

    rc = run_task_create(
        ph_root=ph_root,
        ctx=system_ctx,
        title="Smoke: system artifacts survive reset",
        feature="handbook-reset-smoke",
        decision="ADR-0000",
        points=1,
        owner="@owner",
        prio="P2",
        lane="ops/automation",
        session="task-execution",
        env=env,
    )
    if rc != 0:
        return rc

    # Step 2: Create project-scope artifacts.
    proj_feature_dir = ctx.ph_data_root / "features" / "reset-smoke-project"
    if not proj_feature_dir.exists():
        rc = run_feature_create(
            ph_root=ph_root,
            ctx=ctx,
            name="reset-smoke-project",
            epic=False,
            owner="@owner",
            stage="proposed",
            env=env,
        )
        if rc != 0:
            return rc

    rc = sprint_plan(ph_root=ph_root, ctx=ctx, sprint_id="SPRINT-2099-01-02", force=False, env=env)
    if rc != 0:
        return rc

    rc = run_task_create(
        ph_root=ph_root,
        ctx=ctx,
        title="Smoke: project artifacts are wiped",
        feature="reset-smoke-project",
        decision="ADR-0000",
        points=1,
        owner="@owner",
        prio="P2",
        lane="ops",
        session="task-execution",
        env=env,
    )
    if rc != 0:
        return rc

    # Step 3: Execute reset.
    rc = run_reset(
        ctx=ctx,
        spec=".project-handbook/process/automation/reset_spec.json",
        include_system=include_system,
        confirm="RESET",
        force="true",
    )
    if rc != 0:
        return rc

    # Step 4: Verify separation (filesystem asserts).
    checks: list[tuple[int, str]] = []

    checks.append(
        (_assert_not_exists(ctx.ph_data_root / "features" / "reset-smoke-project", "project feature"), "proj_feature")
    )
    checks.append(
        (
            _assert_not_exists(ctx.ph_data_root / "sprints" / "2099" / "SPRINT-2099-01-02", "project sprint"),
            "proj_sprint",
        )
    )
    checks.append(
        (_assert_not_exists(ctx.ph_data_root / "sprints" / "current", "project current sprint symlink"), "proj_current")
    )
    checks.append(
        (
            _assert_exists(
                system_ctx.ph_data_root / "features" / "handbook-reset-smoke",
                "system feature",
            ),
            "sys_feature",
        )
    )
    checks.append(
        (
            _assert_exists(
                system_ctx.ph_data_root / "sprints" / "2099" / "SPRINT-2099-01-01",
                "system sprint",
            ),
            "sys_sprint",
        )
    )
    if include_system:
        checks[-2] = (
            _assert_not_exists(
                system_ctx.ph_data_root / "features" / "handbook-reset-smoke",
                "system feature",
            ),
            "sys_feature",
        )
        checks[-1] = (
            _assert_not_exists(
                system_ctx.ph_data_root / "sprints" / "2099" / "SPRINT-2099-01-01",
                "system sprint",
            ),
            "sys_sprint",
        )

    for code, _name in checks:
        if code != 0:
            return code

    # Step 5: Confirm repo health.
    validate_exit, _out_path, message = run_validate(
        ph_root=ph_root,
        ph_project_root=ctx.ph_project_root,
        ph_data_root=ctx.ph_data_root,
        scope=ctx.scope,
        quick=True,
        silent_success=False,
    )
    if message:
        print(message, end="")
    if validate_exit != 0:
        return validate_exit

    rc = sprint_plan(ph_root=ph_root, ctx=ctx, sprint_id="SPRINT-2099-01-03", force=False, env=env)
    if rc != 0:
        return rc

    if include_system:
        print("✅ reset-smoke complete (project + system scopes wiped).")
    else:
        print("✅ reset-smoke complete (project scope wiped; system scope preserved).")
    return 0
