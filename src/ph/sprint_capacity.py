from __future__ import annotations

import json
import sys
from pathlib import Path

from . import sprint_status
from .context import Context
from .remediation_hints import next_commands_no_active_sprint, print_next_commands
from .sprint import load_sprint_config, sprint_dir_from_id


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


def _p0_p1_backlog_count(*, ph_data_root: Path) -> int:
    backlog_index = ph_data_root / "backlog" / "index.json"
    if not backlog_index.exists():
        return 0
    try:
        backlog_data = json.loads(backlog_index.read_text(encoding="utf-8"))
    except Exception:
        return 0
    count = 0
    for item in backlog_data.get("items", []):
        if isinstance(item, dict) and item.get("severity") in ["P0", "P1"]:
            count += 1
    return count


def run_sprint_capacity(*, ph_root: Path, ctx: Context, sprint: str | None, env: dict[str, str]) -> int:
    _ = env  # parity with other commands; capacity currently ignores clock

    sprint_dir = _resolve_sprint_dir(ctx=ctx, sprint=sprint)
    if sprint_dir is None or not sprint_dir.exists():
        print("❌ No active sprint", file=sys.stderr)
        print_next_commands(commands=next_commands_no_active_sprint(ctx=ctx), file=sys.stderr)
        return 1

    sprint_id = sprint_dir.name
    config = load_sprint_config(ph_project_root=ctx.ph_project_root)
    capacity_config = config.get("sprint_management", {}).get("capacity_allocation", {})
    planned_pct = int(capacity_config.get("default_planned_percentage", 80) or 80)
    reactive_pct = int(capacity_config.get("default_reactive_percentage", 20) or 20)

    p0_p1_count = _p0_p1_backlog_count(ph_data_root=ctx.ph_data_root)

    tasks = sprint_status.collect_tasks(sprint_dir=sprint_dir)
    metrics = sprint_status.calculate_velocity(tasks)
    mode = sprint_status._get_sprint_mode(ph_project_root=ctx.ph_project_root, sprint_dir=sprint_dir)

    total_points = int(metrics.get("total_points", 0))
    completed_points = int(metrics.get("completed_points", 0))
    blocked_points = int(metrics.get("blocked_points", 0))
    in_progress_points = int(metrics.get("in_progress_points", 0))

    if mode == "bounded":
        lanes = sprint_status._group_tasks_by_lane(tasks)
        print("\n📊 SPRINT METRICS (BOUNDED)")
        print("=" * 80)
        print(f"\n🎯 Sprint: {sprint_id}")
        print("-" * 40)
        print("\nPoints by status (telemetry; not a scope cap):")
        print(f"Total Points:      {total_points}")
        if total_points > 0:
            print(f"Completed:         {completed_points} ({(completed_points / total_points * 100):.1f}%)")
            print(f"In Progress:       {in_progress_points} ({(in_progress_points / total_points * 100):.1f}%)")
            print(f"Blocked:           {blocked_points} ({(blocked_points / total_points * 100):.1f}%)")
        else:
            print("No tasks in current sprint")

        print(f"\n🚨 Backlog Pressure (P0/P1 count): {p0_p1_count}")
        print("\n🧵 Lanes:")
        if not lanes:
            print("- (no tasks)")
        else:
            for lane, lane_tasks in lanes.items():
                lane_metrics = sprint_status._summarize_tasks(lane_tasks)
                print(
                    f"- {lane:24} {lane_metrics['done']:3d}/{lane_metrics['total_points']:3d} "
                    f"pts done (blocked {lane_metrics['blocked']})"
                )

        print("\n" + "=" * 80)
        return 0

    print("\n📊 SPRINT CAPACITY ALLOCATION")
    print("=" * 80)
    print(f"\n🎯 Sprint: {sprint_id}")
    print("-" * 40)
    print("\n📈 Capacity Model (80/20)")
    print("-" * 40)
    print(f"Planned Work:   {planned_pct}% of capacity")
    print(f"Reactive Work:  {reactive_pct}% of capacity")
    print("\n💼 Current Usage")
    print("-" * 40)
    if total_points > 0:
        print(f"Total Points:      {total_points}")
        print(f"Completed:         {completed_points} ({(completed_points / total_points * 100):.1f}%)")
        print(f"In Progress:       {in_progress_points} ({(in_progress_points / total_points * 100):.1f}%)")
        print(f"Blocked:           {blocked_points} ({(blocked_points / total_points * 100):.1f}%)")
    else:
        print("No tasks in current sprint")
    print("\n🚨 Reactive Pressure")
    print("-" * 40)
    if p0_p1_count > 0:
        print(f"P0/P1 Issues:      {p0_p1_count}")
        if p0_p1_count > 3:
            print("⚠️  WARNING: High reactive load - consider adjusting capacity")
        else:
            print("✅ Reactive load within normal range")
    else:
        print("✅ No P0/P1 issues - full planned capacity available")
    print("\n💡 Recommendations")
    print("-" * 40)
    if p0_p1_count > 5:
        print("🔴 Consider high-incident mode (60/40 allocation)")
    elif p0_p1_count > 3:
        print("🟠 Monitor reactive capacity usage closely")
    elif total_points == 0:
        print("🟡 Add tasks to sprint to utilize capacity")
    else:
        print("✅ Capacity allocation is balanced")

    if capacity_config.get("allow_dynamic_adjustment"):
        presets = capacity_config.get("adjustment_presets", {})
        if presets:
            print("\n🔧 Available Capacity Modes")
            print("-" * 40)
            for mode_name, allocation in presets.items():
                if not isinstance(allocation, dict):
                    continue
                planned = allocation.get("planned")
                reactive = allocation.get("reactive")
                print(f"{mode_name:20} {planned}% planned / {reactive}% reactive")

    print("\n" + "=" * 80)
    return 0
