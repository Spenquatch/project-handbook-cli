from __future__ import annotations

from pathlib import Path

from . import sprint_status
from .clock import today as clock_today
from .context import Context
from .sprint import get_sprint_dates, sprint_dir_from_id
from .sprint_archive import archive_sprint_directory


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
    tasks = sprint_status.collect_tasks(sprint_dir=sprint_dir)
    metrics = sprint_status.calculate_velocity(tasks)
    mode = sprint_status._get_sprint_mode(ph_root=ph_root, sprint_dir=sprint_dir)
    if mode == "bounded":
        health = sprint_status.get_sprint_health(ph_root=ph_root, tasks=tasks, day_of_sprint=0, mode="bounded")
    else:
        start_date, end_date = get_sprint_dates(sprint_id)
        duration_days = (end_date - start_date).days + 1
        health = sprint_status.get_sprint_health(
            ph_root=ph_root, tasks=tasks, day_of_sprint=duration_days, mode="timeboxed"
        )

    template = "\n".join(
        [
            "---",
            f"title: Sprint Retrospective - {sprint_id}",
            "type: sprint-retrospective",
            f"date: {clock_today(env=env).strftime('%Y-%m-%d')}",
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

    completed = [t for t in tasks if str(t.get("status", "")).lower() == "done"]
    for task in completed:
        template += f"\n- ✅ {task.get('id')}: {task.get('title')}"

    template += "\n\n## Carried Over\n"
    carried = [t for t in tasks if str(t.get("status", "")).lower() != "done"]
    for task in carried[:5]:
        template += f"- ⏩ {task.get('id')}: {task.get('title')} (Status: {task.get('status')})\n"

    return template.rstrip("\n") + "\n"


def run_sprint_close(*, ph_root: Path, ctx: Context, sprint: str | None, env: dict[str, str]) -> int:
    sprint_dir = _resolve_sprint_dir(ctx=ctx, sprint=sprint)
    if sprint_dir is None or not sprint_dir.exists():
        print("No active sprint")
        return 1

    sprint_id = sprint_dir.name

    retro_path = sprint_dir / "retrospective.md"
    retro_path.write_text(_create_retrospective(ph_root=ph_root, sprint_dir=sprint_dir, env=env), encoding="utf-8")
    print(f"Created retrospective: {retro_path}")

    tasks = sprint_status.collect_tasks(sprint_dir=sprint_dir)
    metrics = sprint_status.calculate_velocity(tasks)
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

    if ctx.scope == "project":
        print("Sprint closed! Next steps:")
        print("  1. Share the new retrospective and velocity summary")
        print("  2. Update roadmap/releases with completed scope")
        print("  3. Run 'ph status' so status/current_summary.md reflects the close-out")
        print("  4. Kick off the next sprint via 'ph sprint plan' when ready")
        print("  5. Capture any loose ends inside parking lot or backlog")

    return 0
