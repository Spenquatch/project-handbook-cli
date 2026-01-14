from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .clock import today as clock_today
from .context import Context


def iter_sprint_dirs(*, sprints_dir: Path) -> Iterable[Path]:
    if not sprints_dir.exists():
        return

    for year_dir in sprints_dir.iterdir():
        if not year_dir.is_dir() or year_dir.name == "current":
            continue

        if year_dir.name == "archive":
            for archived_year_dir in year_dir.iterdir():
                if not archived_year_dir.is_dir():
                    continue
                for sprint_dir in archived_year_dir.iterdir():
                    if sprint_dir.is_dir() and sprint_dir.name.startswith("SPRINT-"):
                        yield sprint_dir
            continue

        for sprint_dir in year_dir.iterdir():
            if sprint_dir.is_dir() and sprint_dir.name.startswith("SPRINT-"):
                yield sprint_dir


def collect_all_sprint_tasks(*, sprints_dir: Path) -> dict[str, list[dict[str, object]]]:
    tasks_by_feature: dict[str, list[dict[str, object]]] = {}

    if not sprints_dir.exists():
        return tasks_by_feature

    for sprint_dir in iter_sprint_dirs(sprints_dir=sprints_dir):
        tasks_dir = sprint_dir / "tasks"
        if not tasks_dir.exists():
            continue

        sprint_id = sprint_dir.name

        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            task_yaml = task_dir / "task.yaml"
            if not task_yaml.exists():
                continue

            try:
                content = task_yaml.read_text(encoding="utf-8")
                task_data: dict[str, object] = {"sprint": sprint_id}

                for line in content.splitlines():
                    if ":" in line and not line.strip().startswith("-"):
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        if value.isdigit():
                            task_data[key] = int(value)
                        elif value.startswith("[") and value.endswith("]"):
                            items = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
                            task_data[key] = [item for item in items if item]
                        else:
                            task_data[key] = value

                feature = task_data.get("feature", "unknown")
                tasks_by_feature.setdefault(str(feature), []).append(task_data)
            except Exception as exc:
                print(f"Error parsing {task_yaml}: {exc}")

    return tasks_by_feature


def calculate_feature_metrics(*, tasks: list[dict[str, object]], env: dict[str, str]) -> dict[str, object]:
    if not tasks:
        return {}

    by_status: dict[str, list[dict[str, object]]] = {
        "done": [],
        "doing": [],
        "review": [],
        "todo": [],
        "blocked": [],
    }

    total_points = 0
    completed_points = 0

    for task in tasks:
        status = str(task.get("status", "todo"))
        try:
            points = int(task.get("story_points", 0) or 0)
        except Exception:
            points = 0
        total_points += points

        if status in ["done", "completed"]:
            by_status["done"].append(task)
            completed_points += points
        elif status in ["doing", "in_progress", "in-progress"]:
            by_status["doing"].append(task)
        elif status == "review":
            by_status["review"].append(task)
        elif status == "blocked":
            by_status["blocked"].append(task)
        else:
            by_status["todo"].append(task)

    completion_percentage = int(completed_points * 100 / total_points) if total_points > 0 else 0

    remaining_points = total_points - completed_points
    avg_velocity = 21
    estimated_sprints = max(1, remaining_points // avg_velocity)

    today = clock_today(env=env)
    week_num = today.isocalendar()[1]
    estimated_completion_week = week_num + estimated_sprints
    year = today.year
    estimated_sprint = f"SPRINT-{year}-W{estimated_completion_week:02d}"

    return {
        "total_points": total_points,
        "completed_points": completed_points,
        "completion_percentage": completion_percentage,
        "remaining_points": remaining_points,
        "estimated_completion": estimated_sprint,
        "avg_velocity": avg_velocity,
        "by_status": by_status,
    }


def get_current_sprint(*, ph_data_root: Path, env: dict[str, str]) -> str:
    current_path = ph_data_root / "sprints" / "current"
    try:
        if current_path.exists():
            resolved = current_path.resolve()
            if resolved.is_dir() and resolved.name.startswith("SPRINT-"):
                return resolved.name
    except Exception:
        pass

    today = clock_today(env=env)
    week_num = today.isocalendar()[1]
    year = today.year
    return f"SPRINT-{year}-W{week_num:02d}"


def format_active_work_section(
    *,
    ph_data_root: Path,
    feature: str,
    tasks: list[dict[str, object]],
    metrics: dict[str, object],
    env: dict[str, str],
) -> str:
    current_sprint = get_current_sprint(ph_data_root=ph_data_root, env=env)

    current_tasks = [t for t in tasks if t.get("sprint") == current_sprint]
    recent_completed = [t for t in tasks if t.get("status") == "done"][-5:]
    blocked_tasks = [t for t in tasks if t.get("status") == "blocked"]

    section = "## Active Work (auto-generated)\n"
    section += f"*Last updated: {clock_today(env=env).strftime('%Y-%m-%d')}*\n\n"

    if current_tasks:
        section += f"### Current Sprint ({current_sprint})\n"
        for task in current_tasks:
            status_emoji = {
                "todo": "⭕",
                "doing": "🔄",
                "review": "👀",
                "done": "✅",
                "blocked": "🚫",
            }.get(task.get("status"), "❓")

            points = task.get("story_points", 0)
            owner = task.get("owner", "@unassigned")
            title = task.get("title", "Untitled")
            task_id = task.get("id", "UNKNOWN")

            section += f"- {status_emoji} {task_id}: {title} ({points}pts, {owner})\n"
        section += "\n"
    else:
        section += f"### Current Sprint ({current_sprint})\n"
        section += "- No active tasks in current sprint\n\n"

    if recent_completed:
        section += "### Recent Completed (last 5 tasks)\n"
        for task in recent_completed:
            points = task.get("story_points", 0)
            sprint = task.get("sprint", "UNKNOWN")
            title = task.get("title", "Untitled")
            task_id = task.get("id", "UNKNOWN")
            section += f"- ✅ {task_id}: {title} ({points}pts) - {sprint}\n"
        section += "\n"

    if blocked_tasks:
        section += "### Blocked Items\n"
        for task in blocked_tasks:
            points = task.get("story_points", 0)
            title = task.get("title", "Untitled")
            task_id = task.get("id", "UNKNOWN")
            section += f"- 🚫 {task_id}: {title} ({points}pts)\n"
        section += "\n"

    section += "### Metrics\n"
    section += f"- **Total Story Points**: {metrics['total_points']} (planned)\n"
    section += f"- **Completed Points**: {metrics['completed_points']} ({metrics['completion_percentage']}%)\n"
    section += f"- **Remaining Points**: {metrics['remaining_points']}\n"
    section += f"- **Estimated Completion**: {metrics['estimated_completion']}\n"
    section += f"- **Average Velocity**: {metrics['avg_velocity']} points/sprint\n\n"

    return section


def update_feature_status_file(
    *,
    ph_data_root: Path,
    feature: str,
    tasks: list[dict[str, object]],
    env: dict[str, str],
) -> bool:
    features_dir = ph_data_root / "features"
    feature_dir = features_dir / feature
    status_file = feature_dir / "status.md"

    if not status_file.exists():
        print(f"⚠️  Feature status file not found: {status_file}")
        return False

    try:
        content = status_file.read_text(encoding="utf-8")
        metrics = calculate_feature_metrics(tasks=tasks, env=env)

        manual_lines: list[str] = []
        for line in content.splitlines():
            if line.startswith("## Active Work (auto-generated)"):
                break
            if line.startswith("Active Work (generated)"):
                break
            manual_lines.append(line)

        manual_content = "\n".join(manual_lines).rstrip()
        auto_section = format_active_work_section(
            ph_data_root=ph_data_root,
            feature=feature,
            tasks=tasks,
            metrics=metrics,
            env=env,
        )
        updated_content = manual_content + "\n\n" + auto_section

        status_file.write_text(updated_content, encoding="utf-8")
        print(f"✅ Updated {feature} status with {len(tasks)} tasks, {metrics['completion_percentage']}% complete")
        return True
    except Exception as exc:
        print(f"❌ Error updating {feature} status: {exc}")
        return False


def update_all_feature_status(*, ph_data_root: Path, env: dict[str, str]) -> int:
    tasks_by_feature = collect_all_sprint_tasks(sprints_dir=ph_data_root / "sprints")
    if not tasks_by_feature:
        print("📋 No sprint tasks found")
        return 0

    updated_count = 0
    for feature, tasks in tasks_by_feature.items():
        if feature == "unknown":
            continue
        if update_feature_status_file(ph_data_root=ph_data_root, feature=feature, tasks=tasks, env=env):
            updated_count += 1

    print(f"\n🎯 Updated {updated_count} feature status files")
    print(f"📊 Features with active work: {len([f for f, t in tasks_by_feature.items() if f != 'unknown' and t])}")
    return 0


def show_feature_summary(*, ph_data_root: Path, env: dict[str, str]) -> int:
    tasks_by_feature = collect_all_sprint_tasks(sprints_dir=ph_data_root / "sprints")

    print("🎯 FEATURE SUMMARY WITH SPRINT DATA")
    print("=" * 60)

    for feature, tasks in sorted(tasks_by_feature.items()):
        if feature == "unknown":
            continue

        metrics = calculate_feature_metrics(tasks=tasks, env=env)

        current_sprint = get_current_sprint(ph_data_root=ph_data_root, env=env)
        current_tasks = len([t for t in tasks if t.get("sprint") == current_sprint])

        if metrics["completion_percentage"] >= 90:
            status_emoji = "🎉"
        elif metrics["completion_percentage"] >= 50:
            status_emoji = "🔄"
        elif current_tasks > 0:
            status_emoji = "⚡"
        else:
            status_emoji = "💤"

        print(
            f"{status_emoji} {feature:<25} "
            f"{metrics['completed_points']:3d}/{metrics['total_points']:3d} pts "
            f"({metrics['completion_percentage']:3d}%) "
            f"Current: {current_tasks} tasks"
        )

    return 0


def run_feature_update_status(*, ctx: Context, env: dict[str, str]) -> int:
    return update_all_feature_status(ph_data_root=ctx.ph_data_root, env=env)


def run_feature_summary(*, ctx: Context, env: dict[str, str]) -> int:
    return show_feature_summary(ph_data_root=ctx.ph_data_root, env=env)
