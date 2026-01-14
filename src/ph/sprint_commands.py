from __future__ import annotations

from pathlib import Path

from .context import Context
from .sprint import create_sprint_plan_template, get_sprint_id, sprint_dir_from_id, update_current_symlink


def sprint_plan(*, ph_root: Path, ctx: Context, sprint_id: str | None, force: bool, env: dict[str, str]) -> int:
    resolved_id = sprint_id or get_sprint_id(ph_root=ph_root, ph_data_root=ctx.ph_data_root, env=env)
    sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=resolved_id)
    sprint_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "tasks").mkdir(exist_ok=True)

    plan_file = sprint_dir / "plan.md"
    if not plan_file.exists() or force:
        plan_file.write_text(
            create_sprint_plan_template(
                ph_root=ph_root,
                ph_data_root=ctx.ph_data_root,
                scope=ctx.scope,
                sprint_id=resolved_id,
                env=env,
            ),
            encoding="utf-8",
        )

    update_current_symlink(ph_data_root=ctx.ph_data_root, sprint_id=resolved_id)

    if ctx.scope == "system":
        print("System-scope sprint scaffold ready:")
        print("  1. Edit .project-handbook/system/sprints/current/plan.md with goals, lanes, and integration tasks")
        print("  2. Seed tasks via 'ph --scope system task create --title ... --feature ... --decision ADR-###'")
        print("  3. Re-run 'ph --scope system sprint status' to confirm health + next-up ordering")
        print("  4. Run 'ph --scope system validate --quick' before handing off to another agent")
    else:
        print("Sprint scaffold ready:")
        print("  1. Edit sprints/current/plan.md with goals, lanes, and integration tasks")
        print("  2. Seed tasks via 'ph task create --title ... --feature ... --decision ADR-###'")
        print("  3. Re-run 'ph sprint status' to confirm health + next-up ordering")
        print("  4. Run 'ph validate --quick' before handing off to another agent")
        print("  5. Need facilitation tips? 'ph onboarding session sprint-planning'")

    return 0


def sprint_open(*, ph_root: Path, ctx: Context, sprint_id: str) -> int:
    sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
    if not sprint_dir.exists():
        print(f"❌ Sprint does not exist: {sprint_id} ({sprint_dir})")
        return 1

    update_current_symlink(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
    print(f"✅ Current sprint set to: {sprint_id}")
    return 0
