from __future__ import annotations

from pathlib import Path
from typing import Any

from .context import Context
from .sprint import sprint_dir_from_id
from .task_taxonomy import effective_task_type_and_session


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
        inferred_type, derived_session, _issues = effective_task_type_and_session(task)
        task_type = inferred_type or str(task.get("task_type", "") or "").strip() or "unknown"
        task_type_info = f" [type:{task_type}]" if task_type else ""
        session_info = f" ({derived_session})" if derived_session else ""

        release = task.get("release")
        release_value = str(release).strip() if release is not None else ""
        release_info = ""
        if release_value and release_value.lower() not in {"null", "none"}:
            release_info = f" [rel:{release_value}]"

        gate_raw = task.get("release_gate")
        gate_value = False
        if isinstance(gate_raw, bool):
            gate_value = gate_raw
        elif gate_raw is not None:
            gate_str = str(gate_raw).strip().lower()
            gate_value = gate_str in {"true", "1", "yes"}
        gate_info = " [gate]" if gate_value else ""

        points = task.get("story_points")
        points_value = str(points).strip() if points is not None else "?"

        print(
            f"{status_emoji} {task.get('id')}: {task.get('title')} "
            f"{lane_info}{task_type_info}{session_info}{release_info}{gate_info} [{points_value}pts]{dep_info}"
        )

    return 0
