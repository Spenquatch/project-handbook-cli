from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from .context import Context
from .sprint import create_sprint_plan_template, get_sprint_id, sprint_dir_from_id, update_current_symlink
from .task_create import run_task_create


def sprint_plan(*, ph_root: Path, ctx: Context, sprint_id: str | None, force: bool, env: dict[str, str]) -> int:
    def _task_yaml_indicates_sprint_gate(text: str) -> bool:
        for line in text.splitlines():
            raw = line.strip()
            if raw.lower() == "task_type: sprint-gate":
                return True
        return False

    def _sprint_has_gate_task(tasks_dir: Path) -> bool:
        if not tasks_dir.exists():
            return False
        for task_dir in sorted(tasks_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_yaml = task_dir / "task.yaml"
            if not task_yaml.exists():
                continue
            try:
                if _task_yaml_indicates_sprint_gate(task_yaml.read_text(encoding="utf-8")):
                    return True
            except Exception:
                continue
        return False

    def _find_first_sprint_gate_task_dir(tasks_dir: Path) -> Path | None:
        if not tasks_dir.exists():
            return None
        for task_dir in sorted(tasks_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_yaml = task_dir / "task.yaml"
            if not task_yaml.exists():
                continue
            try:
                if _task_yaml_indicates_sprint_gate(task_yaml.read_text(encoding="utf-8")):
                    return task_dir
            except Exception:
                continue
        return None

    resolved_id = sprint_id or get_sprint_id(
        ph_project_root=ctx.ph_project_root, ph_data_root=ctx.ph_data_root, env=env
    )
    sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=resolved_id)
    sprint_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "tasks").mkdir(exist_ok=True)

    plan_file = sprint_dir / "plan.md"
    if ctx.scope == "system":
        if not plan_file.exists() or force:
            plan_file.write_text(
                create_sprint_plan_template(
                    ph_project_root=ctx.ph_project_root,
                    ph_data_root=ctx.ph_data_root,
                    scope=ctx.scope,
                    sprint_id=resolved_id,
                    env=env,
                ),
                encoding="utf-8",
            )

        update_current_symlink(ph_data_root=ctx.ph_data_root, sprint_id=resolved_id)
        print("System-scope sprint scaffold ready:")
        print("  1. Edit .project-handbook/system/sprints/current/plan.md with goals, lanes, and integration tasks")
        print("  2. Seed tasks via 'ph --scope system task create --title ... --feature ... --decision ADR-###'")
        print("  3. Re-run 'ph --scope system sprint status' to confirm health + next-up ordering")
        print("  4. Run 'ph --scope system validate --quick' before handing off to another agent")
    else:
        wrote_or_regenerated = False
        if plan_file.exists() and not force:
            print(f"⚠️  Sprint plan already exists (not overwriting): {plan_file}")
            print("Re-run with --force to regenerate the template.")
        else:
            try:
                template = create_sprint_plan_template(
                    ph_project_root=ctx.ph_project_root,
                    ph_data_root=ctx.ph_data_root,
                    scope=ctx.scope,
                    sprint_id=resolved_id,
                    env=env,
                )
            except ValueError as exc:
                print(f"❌ Sprint plan generation blocked:\n{exc}")
                return 1

            plan_file.write_text(template, encoding="utf-8")
            wrote_or_regenerated = True
            print(f"Created sprint plan: {plan_file}")

        update_current_symlink(ph_data_root=ctx.ph_data_root, sprint_id=resolved_id)

        tasks_dir = sprint_dir / "tasks"
        has_gate = _sprint_has_gate_task(tasks_dir)
        if wrote_or_regenerated and not has_gate:
            buf = StringIO()
            with redirect_stdout(buf):
                exit_code = run_task_create(
                    ph_root=ph_root,
                    ctx=ctx,
                    title=f"Sprint Gate: {resolved_id}",
                    feature="sprint",
                    decision="N/A",
                    points=3,
                    owner="@owner",
                    prio="P2",
                    lane=None,
                    task_type="sprint-gate",
                    release=None,
                    gate=False,
                    env=env,
                )
            if exit_code != 0:
                print("❌ Failed to scaffold required sprint gate task.")
                captured = buf.getvalue().strip()
                if captured:
                    print(captured)
                print(
                    "Remediation: ph task create --title 'Sprint Gate: <goal>' --feature sprint "
                    "--decision N/A --type sprint-gate"
                )
                return exit_code

            gate_dir = _find_first_sprint_gate_task_dir(tasks_dir)
            print("✅ Sprint gate task scaffolded (must exist Day 0; expected to close last).")
            if gate_dir is not None:
                print(f"  - Fill exit criteria + evidence in: {gate_dir / 'validation.md'}")
                print("  - Pre-exec lint will fail until Sprint Goal/Exit criteria/evidence are explicit.")
        elif (not wrote_or_regenerated) and (not has_gate):
            print("⚠️  No sprint gate task found (required per sprint).")
            print("Sprint gate must exist from Day 0; it is expected to close last.")
            print(
                "Remediation: ph task create --title 'Sprint Gate: <goal>' --feature sprint "
                "--decision N/A --type sprint-gate"
            )

        print("Sprint structure seeded:")
        print(f"  📁 {sprint_dir}/")
        print(f"  📁 {sprint_dir}/tasks/ (ready for task creation)")
        print("Next steps:")
        print("  1. Edit plan.md with goals, lanes, and integration tasks")
        print("  2. Create tasks via `ph task create ...`")
        print("  3. Review `status/current_summary.md` after generating status")
        print("  4. Re-run `ph onboarding session sprint-planning` for facilitation tips")

        print("Sprint scaffold ready:")
        print("  1. Edit .project-handbook/sprints/current/plan.md with goals, lanes, and integration tasks")
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
