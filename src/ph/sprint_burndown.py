from __future__ import annotations

from pathlib import Path

from . import sprint_status
from .clock import today as clock_today
from .context import Context
from .sprint import sprint_dir_from_id


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


def _generate_ascii_burndown(*, ph_root: Path, sprint_dir: Path, tasks: list[dict]) -> str:
    sprint_id = sprint_dir.name
    mode = sprint_status._get_sprint_mode(ph_root=ph_root, sprint_dir=sprint_dir)
    metrics = sprint_status.calculate_velocity(tasks)

    total = int(metrics.get("total_points", 0))
    completed = int(metrics.get("completed_points", 0))
    remaining = max(total - completed, 0)

    if mode == "bounded":
        lanes = sprint_status._group_tasks_by_lane(tasks)
        lines = [
            f"Sprint Summary: {sprint_id}",
            "=" * 50,
            "",
            "Points by status:",
            f"- Total:      {total}",
            f"- Done:       {metrics['completed_points']} ({metrics['velocity_percentage']}%)",
            f"- Doing/Review:{metrics['in_progress_points']}",
            f"- Blocked:    {metrics['blocked_points']}",
            f"- Todo:       {metrics['todo_points']}",
            "",
            "By lane:",
        ]
        if not lanes:
            lines.append("- (no tasks)")
        else:
            for lane, lane_tasks in lanes.items():
                lane_metrics = sprint_status._summarize_tasks(lane_tasks)
                lines.append(
                    f"- {lane}: {lane_metrics['done']}/{lane_metrics['total_points']} pts done"
                    f" (blocked {lane_metrics['blocked']}, todo {lane_metrics['todo']})"
                )
        return "\n".join(lines).rstrip("\n") + "\n"

    total_bar = "█" * 20
    remaining_bar = "█" * int(20 * remaining / total) if total > 0 else ""
    chart = f"""
Sprint Burndown: {sprint_id}
{"=" * 50}

Points Remaining (illustrative):
{total:3d} |{total_bar} Day 1
    |{"█" * int(20 * 0.8)} Day 2
    |{"█" * int(20 * 0.6)} Day 3
    |{remaining_bar} Today
  0 |{"_" * 20}

Current Status:
- Total Points: {total}
- Completed: {completed} ({metrics["velocity_percentage"]}%)
- In Progress: {metrics["in_progress_points"]}
- Blocked: {metrics["blocked_points"]}
- Todo: {metrics["todo_points"]}
"""
    return chart.lstrip("\n")


def run_sprint_burndown(*, ph_root: Path, ctx: Context, sprint: str | None, env: dict[str, str]) -> int:
    sprint_dir = _resolve_sprint_dir(ctx=ctx, sprint=sprint)
    if sprint_dir is None or not sprint_dir.exists():
        print("No active sprint")
        return 1

    tasks = sprint_status.collect_tasks(sprint_dir=sprint_dir)
    burndown = _generate_ascii_burndown(ph_root=ph_root, sprint_dir=sprint_dir, tasks=tasks)
    print(burndown, end="")

    burndown_file = sprint_dir / "burndown.md"
    today = clock_today(env=env).isoformat()
    burndown_file.write_text(
        "\n".join(
            [
                "---",
                f"title: Sprint Burndown - {sprint_dir.name}",
                "type: sprint-burndown",
                f"date: {today}",
                f"sprint: {sprint_dir.name}",
                "tags: [sprint, burndown]",
                "---",
                "",
                "# Burndown Chart",
                "",
                "```",
                burndown.rstrip("\n"),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"\nSaved to: {burndown_file}")
    return 0
