from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .context import Context
from .sprint import get_sprint_dates, load_sprint_config, sprint_dir_from_id


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


def _parse_task_yaml(text: str) -> dict[str, Any]:
    task_data: dict[str, Any] = {}
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


def collect_tasks(*, sprint_dir: Path) -> list[dict[str, Any]]:
    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        return []

    tasks: list[dict[str, Any]] = []
    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        task_yaml = task_dir / "task.yaml"
        if not task_yaml.exists():
            continue
        try:
            content = task_yaml.read_text(encoding="utf-8")
        except Exception:
            continue
        task_data = _parse_task_yaml(content)
        tasks.append(task_data)
    return tasks


def sort_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tasks, key=lambda t: str(t.get("id", "TASK-999")))


def describe_task(task: dict[str, Any]) -> str:
    task_id = task.get("id", "TASK-???")
    title = task.get("title", "<untitled>")
    owner = task.get("owner", "@owner")
    status = task.get("status", "todo")
    points = task.get("story_points", "?")
    session = task.get("session")
    session_info = f" | session {session}" if session else ""
    return f"- {task_id} [{status} | {points} pts | owner {owner}{session_info}] {title}"


def pick_task_by_status(tasks: list[dict[str, Any]], statuses: Sequence[str]) -> dict[str, Any] | None:
    for status in statuses:
        for task in tasks:
            if str(task.get("status", "todo")).lower() == status:
                return task
    return None


def normalize_dependencies(task: dict[str, Any]) -> list[str]:
    deps = task.get("depends_on", [])
    if isinstance(deps, str):
        return [d.strip() for d in deps.strip("[]").split(",") if d.strip()]
    if isinstance(deps, list):
        return [str(d).strip() for d in deps if str(d).strip()]
    return []


def validate_dependencies(tasks: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = {t.get("id") for t in tasks}
    sentinel_count = 0
    for task in tasks:
        tid = task.get("id", "<unknown>")
        deps = normalize_dependencies(task)
        if not deps:
            errors.append(f"{tid} missing depends_on; use FIRST_TASK or at least one task id")
            continue
        sentinel_count += deps.count("FIRST_TASK")
        if "FIRST_TASK" in deps and len(deps) > 1:
            errors.append(f"{tid} mixes FIRST_TASK with other dependencies")
        for dep in deps:
            if dep == "FIRST_TASK":
                continue
            if dep not in ids:
                errors.append(f"{tid} depends_on unknown task id {dep}")
    if sentinel_count == 0:
        warnings.append("No FIRST_TASK defined; ensure at least one task is explicitly first")
    if sentinel_count > 1:
        errors.append("FIRST_TASK used more than once")
    return errors, warnings


def dependency_ready(task: dict[str, Any], task_map: dict[str, dict[str, Any]]) -> bool:
    deps = normalize_dependencies(task)
    if "FIRST_TASK" in deps and len(deps) == 1:
        return True
    for dep in deps:
        if dep == "FIRST_TASK":
            continue
        dep_status = str(task_map.get(dep, {}).get("status", "todo")).lower()
        if dep_status != "done":
            return False
    return True


def _task_points(task: dict[str, Any]) -> int:
    try:
        return int(task.get("story_points", 0))
    except Exception:
        return 0


def calculate_velocity(tasks: list[dict[str, Any]]) -> dict[str, int]:
    metrics = {
        "total_points": 0,
        "completed_points": 0,
        "in_progress_points": 0,
        "blocked_points": 0,
        "todo_points": 0,
        "velocity_percentage": 0,
    }

    for task in tasks:
        points = _task_points(task)
        status = str(task.get("status", "todo")).lower()

        metrics["total_points"] += points

        if status == "done":
            metrics["completed_points"] += points
        elif status in ["doing", "in_progress", "review", "in-progress"]:
            metrics["in_progress_points"] += points
        elif status == "blocked":
            metrics["blocked_points"] += points
        else:
            metrics["todo_points"] += points

    if metrics["total_points"] > 0:
        metrics["velocity_percentage"] = int(metrics["completed_points"] * 100 / metrics["total_points"])

    return metrics


def get_sprint_health(*, ph_root: Path, tasks: list[dict[str, Any]], day_of_sprint: int, mode: str) -> str:
    config = load_sprint_config(ph_root=ph_root)
    thresholds = config.get("sprint_management", {}).get("health_check_thresholds", {})
    red_blocked = thresholds.get("blocked_percentage_red", 30)
    red_progress = thresholds.get("progress_percentage_red", 50)
    check_day = thresholds.get("progress_check_day", 3)

    metrics = calculate_velocity(tasks)
    total = metrics["total_points"]
    blocked_pct = metrics["blocked_points"] * 100 / total if total else 0
    progress_pct = (metrics["completed_points"] + metrics["in_progress_points"]) * 100 / total if total else 0

    if mode == "bounded":
        if blocked_pct > red_blocked:
            return f"🔴 RED - Too many blockers ({blocked_pct:.0f}% > {red_blocked}%)"
        if blocked_pct > red_blocked / 2:
            return f"🟡 YELLOW - Some blockers need attention ({blocked_pct:.0f}%)"
        return "🟢 GREEN - Flowing"

    if blocked_pct > red_blocked:
        return f"🔴 RED - Too many blockers ({blocked_pct:.0f}% > {red_blocked}%)"
    if day_of_sprint >= check_day and progress_pct < red_progress:
        return f"🔴 RED - Behind schedule ({progress_pct:.0f}% < {red_progress}% by day {check_day})"

    if blocked_pct > red_blocked / 2:
        return f"🟡 YELLOW - Some blockers need attention ({blocked_pct:.0f}%)"
    if day_of_sprint >= check_day - 1 and progress_pct < red_progress * 0.8:
        return f"🟡 YELLOW - Slightly behind schedule ({progress_pct:.0f}%)"

    return "🟢 GREEN - On track"


def _read_sprint_plan_metadata(*, sprint_dir: Path) -> dict[str, str]:
    plan_path = sprint_dir / "plan.md"
    if not plan_path.exists():
        return {}

    text = plan_path.read_text(encoding="utf-8")
    lines = text.splitlines()
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


def _get_sprint_mode(*, ph_root: Path, sprint_dir: Path) -> str:
    config = load_sprint_config(ph_root=ph_root)
    meta = _read_sprint_plan_metadata(sprint_dir=sprint_dir)
    if meta.get("mode"):
        mode = (meta.get("mode") or "").strip().lower()
    elif meta.get("start") and meta.get("end"):
        mode = "timeboxed"
    else:
        mode = (config.get("sprint_management", {}).get("mode") or "timeboxed").strip().lower()
    if mode in {"bounded", "boundary", "work-bounded", "workbounded"}:
        return "bounded"
    return "timeboxed"


def _resolve_sprint_created_date(*, sprint_dir: Path) -> dt.date | None:
    meta = _read_sprint_plan_metadata(sprint_dir=sprint_dir)
    raw = meta.get("date") or meta.get("created") or meta.get("start")
    if raw:
        try:
            return dt.datetime.strptime(raw.strip(), "%Y-%m-%d").date()
        except Exception:
            pass
    plan_path = sprint_dir / "plan.md"
    if plan_path.exists():
        try:
            return dt.datetime.fromtimestamp(plan_path.stat().st_mtime).date()
        except Exception:
            return None
    return None


def _task_lane(task: dict[str, Any]) -> str:
    lane = str(task.get("lane", "") or "").strip()
    if lane:
        return lane
    feature = str(task.get("feature", "") or "").strip()
    if feature:
        return f"feature/{feature}"
    return "unassigned"


def _summarize_tasks(tasks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total_points": 0, "done": 0, "doing": 0, "review": 0, "blocked": 0, "todo": 0}
    for task in tasks:
        points = _task_points(task)
        status = str(task.get("status", "todo") or "todo").lower().strip()
        summary["total_points"] += points
        if status == "done":
            summary["done"] += points
        elif status == "doing":
            summary["doing"] += points
        elif status == "review":
            summary["review"] += points
        elif status == "blocked":
            summary["blocked"] += points
        else:
            summary["todo"] += points
    return summary


def _group_tasks_by_lane(tasks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    lanes: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        lanes.setdefault(_task_lane(task), []).append(task)
    for lane, lane_tasks in lanes.items():
        lanes[lane] = sort_tasks(lane_tasks)
    return dict(sorted(lanes.items(), key=lambda kv: kv[0]))


def run_sprint_status(*, ph_root: Path, ctx: Context, sprint: str | None) -> int:
    sprint_dir = _resolve_sprint_dir(ctx=ctx, sprint=sprint)
    if sprint_dir is None or not sprint_dir.exists():
        print("No active sprint")
        return 0

    sprint_id = sprint_dir.name
    tasks = sort_tasks(collect_tasks(sprint_dir=sprint_dir))
    metrics = calculate_velocity(tasks)

    today = dt.date.today()
    mode = _get_sprint_mode(ph_root=ph_root, sprint_dir=sprint_dir)

    day_of_sprint = 0
    timeline_line = ""
    ended_days_ago: int | None = None

    if mode == "bounded":
        created = _resolve_sprint_created_date(sprint_dir=sprint_dir)
        age_days = (today - created).days if created else None
        timeline_line = f"Mode: bounded | Age: {age_days} days" if age_days is not None else "Mode: bounded"
        health = get_sprint_health(ph_root=ph_root, tasks=tasks, day_of_sprint=day_of_sprint, mode="bounded")
    else:
        start_date, end_date = get_sprint_dates(sprint_id)
        duration_days = (end_date - start_date).days + 1
        if today < start_date:
            days_until = (start_date - today).days
            timeline_line = (
                "Mode: timeboxed | "
                f"Starts in {days_until} days ({start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')})"
            )
            health = "🟦 SCHEDULED"
        elif today > end_date:
            days_ago = (today - end_date).days
            ended_days_ago = days_ago
            day_of_sprint = duration_days
            timeline_line = (
                "Mode: timeboxed | "
                f"Ended {days_ago} days ago ({start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')})"
            )
            health = get_sprint_health(ph_root=ph_root, tasks=tasks, day_of_sprint=day_of_sprint, mode="timeboxed")
        else:
            day_of_sprint = (today - start_date).days + 1
            timeline_line = (
                "Mode: timeboxed | "
                f"Day {day_of_sprint} of {duration_days} ({start_date.strftime('%Y-%m-%d')} → "
                f"{end_date.strftime('%Y-%m-%d')})"
            )
            health = get_sprint_health(ph_root=ph_root, tasks=tasks, day_of_sprint=day_of_sprint, mode="timeboxed")

    task_map = {str(t.get("id")): t for t in tasks if t.get("id")}
    dep_errors, dep_warnings = validate_dependencies(tasks)

    print(f"Sprint: {sprint_id}")
    if timeline_line:
        print(timeline_line)
    print(f"Health: {health}")
    print(
        f"Progress: {metrics['completed_points']}/{metrics['total_points']} points ({metrics['velocity_percentage']}%)"
    )

    active_task = pick_task_by_status(tasks, ["doing", "review"])
    upcoming_task = None
    for task in tasks:
        if str(task.get("status", "todo")).lower() in ["todo", "planned"] and dependency_ready(task, task_map):
            upcoming_task = task
            break

    print("\nCurrent focus:")
    if active_task:
        print(describe_task(active_task))
    else:
        print("- No active tasks. Pull the next planned item.")

    print("Next up:")
    if upcoming_task:
        print(describe_task(upcoming_task))
    else:
        print("- No planned backlog entries remaining in this sprint.")

    lanes = _group_tasks_by_lane(tasks)
    if lanes:
        print("\nLanes:")
        for lane, lane_tasks in list(lanes.items())[:8]:
            lane_metrics = _summarize_tasks(lane_tasks)
            print(
                f"- {lane}: {lane_metrics['done']}/{lane_metrics['total_points']} pts done "
                f"(blocked {lane_metrics['blocked']})"
            )
        if len(lanes) > 8:
            print(f"- (+{len(lanes) - 8} more)")

    if ended_days_ago is not None:
        print(
            "\n⚠️  Sprint is past its end date. Consider closing it (`ph sprint close`) "
            "or opening a new sprint (`ph sprint plan`)."
        )

    if dep_errors or dep_warnings:
        print("\nDependency checks:")
        for err in dep_errors:
            print(f"❌ {err}")
        for warn in dep_warnings:
            print(f"⚠️  {warn}")

    print("\nTip: use `ph onboarding session task-execution` (alias: `implement`) for detailed hand-off guidance.")
    return 0
