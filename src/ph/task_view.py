from __future__ import annotations

from pathlib import Path
from typing import Any

from .context import Context


def _get_current_sprint_link(*, ph_data_root: Path) -> Path | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return link if resolved.exists() else None


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


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1]
            return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
        if raw:
            return [raw]
    return []


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


def _task_location_for_scope(*, ctx: Context, directory: str) -> str:
    if ctx.scope == "system":
        return f".project-handbook/system/sprints/current/tasks/{directory}"
    return f"sprints/current/tasks/{directory}"


def run_task_list(*, ctx: Context) -> int:
    current_link = _get_current_sprint_link(ph_data_root=ctx.ph_data_root)
    if current_link is None:
        print("📋 No tasks in current sprint")
        print("💡 Create one with: ph task create")
        return 0

    sprint_id = current_link.resolve().name
    tasks = list_sprint_tasks(sprint_dir=current_link)
    if not tasks:
        print("📋 No tasks in current sprint")
        print("💡 Create one with: ph task create")
        return 0

    print(f"📋 SPRINT TASKS: {sprint_id}")
    print("=" * 60)

    for task in tasks:
        status_emoji = {
            "todo": "⭕",
            "doing": "🔄",
            "review": "👀",
            "done": "✅",
            "blocked": "🚫",
        }.get(str(task.get("status", "")).lower(), "❓")

        deps = _normalize_list(task.get("depends_on", []))
        dep_info = f" (depends: {', '.join(deps)})" if deps else ""
        lane = str(task.get("lane", "") or "").strip()
        lane_info = f" [{lane}]" if lane else ""
        session = str(task.get("session", "") or "").strip()
        session_info = f" ({session})" if session else ""

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
        if not points_value or points_value.lower() in {"null", "none"}:
            points_value = "?"

        print(
            f"{status_emoji} {task.get('id')}: {task.get('title')} "
            f"{lane_info}{session_info}{release_info}{gate_info} [{points_value}pts]{dep_info}"
        )

    return 0


def run_task_show(*, ctx: Context, task_id: str) -> int:
    current_link = _get_current_sprint_link(ph_data_root=ctx.ph_data_root)
    tasks: list[dict[str, Any]] = []
    if current_link is not None:
        tasks = list_sprint_tasks(sprint_dir=current_link)

    task = next((t for t in tasks if str(t.get("id", "")).strip() == task_id), None)
    if not task:
        print(f"❌ Task {task_id} not found")
        return 1

    print(f"📋 TASK DETAILS: {task_id}")
    print("=" * 50)
    print(f"Title: {task.get('title')}")
    print(f"Feature: {task.get('feature')}")
    lane = str(task.get("lane", "") or "").strip()
    if lane:
        print(f"Lane: {lane}")
    session = str(task.get("session", "") or "").strip()
    if session:
        print(f"Session: {session}")
    print(f"Owner: {task.get('owner')}")
    print(f"Status: {task.get('status')}")
    print(f"Story Points: {task.get('story_points')}")
    print(f"Priority: {task.get('prio')}")
    print(f"Due: {task.get('due')}")

    deps = _normalize_list(task.get("depends_on", []))
    if deps:
        print(f"Dependencies: {', '.join(deps)}")
    else:
        print("Dependencies: None")

    print()
    location = _task_location_for_scope(ctx=ctx, directory=str(task.get("directory", "")))
    print(f"Location: {location}")
    print("Files: README.md, steps.md, commands.md, checklist.md, validation.md")
    return 0
