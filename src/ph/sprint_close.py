from __future__ import annotations

from pathlib import Path

from . import sprint_status
from .clock import local_today_from_now as clock_local_today_from_now
from .context import Context
from .release import write_release_progress
from .sprint import get_sprint_dates, sprint_dir_from_id
from .sprint_archive import archive_sprint_directory
from .work_item_archiver import archive_done_tasks_in_sprint


def _get_current_sprint_path(*, ph_data_root: Path) -> Path | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return resolved if resolved.exists() else None


def _resolve_sprint_dir(*, ctx: Context, sprint: str | None) -> Path | None:
    if sprint is None or sprint.strip() in {"", "current"}:
        return _get_current_sprint_path(ph_data_root=ctx.ph_data_root)
    return sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint.strip())


def _read_sprint_plan_metadata(*, sprint_dir: Path) -> dict[str, str]:
    plan_path = sprint_dir / "plan.md"
    if not plan_path.exists():
        return {}
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError:
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:end_idx]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta


def _parse_task_yaml(text: str) -> dict[str, object]:
    task_data: dict[str, object] = {}
    for line in text.splitlines():
        if ":" not in line or line.strip().startswith("-"):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
            task_data[key] = [item for item in items if item]
        else:
            task_data[key] = value
    return task_data


def _collect_tasks_legacy_order(*, sprint_dir: Path) -> list[dict[str, object]]:
    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        return []

    tasks: list[dict[str, object]] = []
    for task_dir in tasks_dir.iterdir():
        if not task_dir.is_dir():
            continue
        task_yaml = task_dir / "task.yaml"
        if not task_yaml.exists():
            continue
        try:
            content = task_yaml.read_text(encoding="utf-8")
        except Exception:
            continue
        tasks.append(_parse_task_yaml(content))
    return tasks


def _rewrite_sprint_current_task_links(*, ph_data_root: Path, sprint_id: str) -> int:
    year = sprint_id.split("-")[1] if "-" in sprint_id else sprint_id
    needle = "sprints/current/tasks/"
    replacement = f"sprints/archive/{year}/{sprint_id}/tasks/"

    roots = [
        ph_data_root / "features",
        ph_data_root / "status" / "evidence",
        ph_data_root / "adr",
    ]

    changed_files = 0
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            if not path.is_file():
                continue
            try:
                before = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if needle not in before:
                continue
            after = before.replace(needle, replacement)
            if after == before:
                continue
            try:
                path.write_text(after, encoding="utf-8")
            except Exception:
                continue
            changed_files += 1
    return changed_files


def _create_retrospective(*, ph_root: Path, sprint_dir: Path, env: dict[str, str]) -> str:
    sprint_id = sprint_dir.name
    tasks = _collect_tasks_legacy_order(sprint_dir=sprint_dir)
    metrics = sprint_status.calculate_velocity(tasks)  # type: ignore[arg-type]
    mode = sprint_status._get_sprint_mode(ph_root=ph_root, sprint_dir=sprint_dir)
    if mode == "bounded":
        health = sprint_status.get_sprint_health(
            ph_root=ph_root, tasks=tasks, day_of_sprint=0, mode="bounded"  # type: ignore[arg-type]
        )
    else:
        start_date, end_date = get_sprint_dates(sprint_id)
        duration_days = (end_date - start_date).days + 1
        health = sprint_status.get_sprint_health(
            ph_root=ph_root, tasks=tasks, day_of_sprint=duration_days, mode="timeboxed"  # type: ignore[arg-type]
        )

    template = "\n".join(
        [
            "---",
            f"title: Sprint Retrospective - {sprint_id}",
            "type: sprint-retrospective",
            f"date: {clock_local_today_from_now(env=env).strftime('%Y-%m-%d')}",
            f"sprint: {sprint_id}",
            "tags: [sprint, retrospective]",
            "---",
            "",
            f"# Sprint Retrospective: {sprint_id}",
            "",
            "## Sprint Metrics",
            f"- **Planned Points**: {metrics['total_points']}",
            f"- **Completed Points**: {metrics['completed_points']}",
            f"- **Velocity**: {metrics['velocity_percentage']}%",
            f"- **Sprint Health**: {health}",
            "",
            "## Velocity Trend",
            f"- This Sprint: {metrics['completed_points']} points",
            "- 3-Sprint Average: (Calculate from previous sprints)",
            "- Trend: ↑ ↓ →",
            "",
            "## What Went Well",
            "- [ ] Item 1",
            "- [ ] Item 2",
            "",
            "## What Could Be Improved",
            "- [ ] Item 1",
            "- [ ] Item 2",
            "",
            "## Action Items",
            "- [ ] Action 1 - Owner: @person - Due: Date",
            "- [ ] Action 2 - Owner: @person - Due: Date",
            "",
            "## Completed Tasks",
        ]
    )

    completed = [t for t in tasks if t.get("status") == "done"]
    for task in completed:
        template += f"\n- ✅ {task.get('id')}: {task.get('title')}"

    template += "\n\n## Carried Over\n"
    carried = [t for t in tasks if t.get("status") != "done"]
    for task in carried[:5]:
        template += f"- ⏩ {task.get('id')}: {task.get('title')} (Status: {task.get('status')})\n"

    return template.rstrip("\n") + "\n"


def run_sprint_close(*, ph_root: Path, ctx: Context, sprint: str | None, env: dict[str, str]) -> int:
    sprint_dir = _resolve_sprint_dir(ctx=ctx, sprint=sprint)
    if sprint_dir is None or not sprint_dir.exists():
        print("No active sprint")
        return 1

    sprint_id = sprint_dir.name

    sprint_meta = _read_sprint_plan_metadata(sprint_dir=sprint_dir)
    sprint_release = (sprint_meta.get("release") or "").strip()
    if sprint_release.lower() in {"", "null", "none"}:
        sprint_release = ""

    try:
        work_item_errors = archive_done_tasks_in_sprint(
            sprint_dir=sprint_dir,
            sprint_id=sprint_id,
            ph_data_root=ctx.ph_data_root,
            strict=True,
            env=env,
        )
        if work_item_errors:
            print("❌ Sprint close blocked: failed to archive referenced backlog/parking-lot items.")
            for err in work_item_errors:
                print(f"  - {err}")
            print("Resolve the issues above, then rerun: ph sprint close")
            return 1
    except Exception as exc:
        print(f"⚠️  Work-item archiving guardrail skipped: {exc}")

    retro_path = sprint_dir / "retrospective.md"
    retro_path.write_text(_create_retrospective(ph_root=ph_root, sprint_dir=sprint_dir, env=env), encoding="utf-8")
    print(f"Created retrospective: {retro_path}")

    tasks = _collect_tasks_legacy_order(sprint_dir=sprint_dir)
    metrics = sprint_status.calculate_velocity(tasks)  # type: ignore[arg-type]
    print(
        "Sprint velocity: "
        f"{metrics['completed_points']}/{metrics['total_points']} points ({metrics['velocity_percentage']}%)"
    )

    try:
        archived_dir = archive_sprint_directory(ctx=ctx, sprint_dir=sprint_dir, env=env)
    except FileExistsError as exc:
        print(f"⚠️  {exc}")
        return 1

    changed = _rewrite_sprint_current_task_links(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
    _ = changed  # reserved for future telemetry output

    print(f"📦 Archived sprint {sprint_id} to {archived_dir}")

    if sprint_release:
        try:
            progress_path = write_release_progress(ph_root=ph_root, version=sprint_release, env=env)
            print(f"📝 Updated: {progress_path}")
            print(f"📦 Release progress refreshed for {sprint_release}.")
        except Exception:
            print(f"⚠️  Release progress refresh failed for {sprint_release}.")

    if ctx.scope == "project":
        print("Sprint closed! Next steps:")
        print("  1. Share the new retrospective and velocity summary")
        print("  2. Update roadmap/releases with completed scope")
        print("  3. Run 'ph status' so status/current_summary.md reflects the close-out")
        print("  4. Kick off the next sprint via 'ph sprint plan' when ready")
        print("  5. Capture any loose ends inside parking lot or backlog")

    return 0
