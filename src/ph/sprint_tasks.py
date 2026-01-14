from __future__ import annotations

from pathlib import Path
from typing import Any

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


def list_sprint_tasks(*, sprint_dir: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        return tasks

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
        task_data["directory"] = task_dir.name
        tasks.append(task_data)

    return tasks


def run_sprint_tasks(*, ctx: Context, sprint: str | None) -> int:
    sprint_dir = _resolve_sprint_dir(ctx=ctx, sprint=sprint)
    if sprint_dir is None or not sprint_dir.exists():
        print("📋 No tasks in current sprint")
        print("💡 Create one with: ph task create")
        return 0

    tasks = list_sprint_tasks(sprint_dir=sprint_dir)
    if not tasks:
        print("📋 No tasks in current sprint")
        print("💡 Create one with: ph task create")
        return 0

    print(f"📋 SPRINT TASKS: {sprint_dir.name}")
    print("=" * 60)

    for task in tasks:
        status_emoji = {
            "todo": "⭕",
            "doing": "🔄",
            "review": "👀",
            "done": "✅",
            "blocked": "🚫",
        }.get(str(task.get("status", "")).lower(), "❓")

        deps = task.get("depends_on", [])
        dep_info = f" (depends: {', '.join(deps)})" if deps else ""
        lane = task.get("lane")
        lane_info = f" [{lane}]" if lane else ""
        session = task.get("session")
        session_info = f" ({session})" if session else ""

        print(
            f"{status_emoji} {task.get('id')}: {task.get('title')} "
            f"{lane_info}{session_info} [{task.get('story_points')}pts]{dep_info}"
        )

    return 0
