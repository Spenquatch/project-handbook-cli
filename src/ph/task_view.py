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


def _get_current_sprint_path(*, ph_data_root: Path) -> Path | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return resolved if resolved.exists() else None


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


def _resolve_task_dir(*, ctx: Context, task_id: str, sprint_dir: Path | None = None) -> tuple[Path, Path] | None:
    if sprint_dir is None:
        sprint_dir = _get_current_sprint_path(ph_data_root=ctx.ph_data_root)

    if sprint_dir is not None:
        tasks_dir = sprint_dir / "tasks"
        if tasks_dir.exists():
            for task_dir in tasks_dir.iterdir():
                if task_dir.is_dir() and task_dir.name.startswith(f"{task_id}-"):
                    return sprint_dir, task_dir

    archive_root = ctx.ph_data_root / "sprints" / "archive"
    matches: list[tuple[Path, Path]] = []
    if archive_root.exists():
        for task_yaml in archive_root.glob(f"**/tasks/{task_id}-*/task.yaml"):
            task_dir = task_yaml.parent
            sprint_dir = task_dir.parent.parent
            if task_dir.is_dir() and sprint_dir.is_dir():
                matches.append((sprint_dir, task_dir))

    if not matches:
        return None

    if len(matches) > 1:
        enriched: list[tuple[str, Path, Path]] = []
        for sprint_dir, task_dir in matches:
            task_yaml = task_dir / "task.yaml"
            try:
                status = str(_parse_task_yaml(task_yaml.read_text(encoding="utf-8")).get("status", "")).strip().lower()
            except OSError:
                status = ""
            enriched.append((status, sprint_dir, task_dir))

        in_progress = [
            (sprint_dir, task_dir)
            for status, sprint_dir, task_dir in enriched
            if status in {"doing", "review", "blocked"}
        ]
        if len(in_progress) == 1:
            return in_progress[0]

        not_done = [(sprint_dir, task_dir) for status, sprint_dir, task_dir in enriched if status and status != "done"]
        if len(not_done) == 1:
            return not_done[0]

        print(f"❌ Task {task_id} is ambiguous (found in multiple archived sprints).")
        for status, sprint_dir, task_dir in enriched[:12]:
            status_info = status or "unknown"
            print(f"  - {sprint_dir.name} [{status_info}]: {task_dir}")
        if len(enriched) > 12:
            print(f"  - (+{len(enriched) - 12} more)")
        print("Set an active sprint via `make sprint-open --sprint SPRINT-...`, then retry.")
        return None

    return matches[0]


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
    resolved = _resolve_task_dir(ctx=ctx, task_id=task_id)
    if not resolved:
        print(f"❌ Task {task_id} not found")
        return 1

    sprint_dir, task_dir = resolved
    task_yaml = task_dir / "task.yaml"
    if not task_yaml.exists():
        print(f"❌ Task metadata not found: {task_yaml}")
        return 1
    task = _parse_task_yaml(task_yaml.read_text(encoding="utf-8"))
    task["directory"] = task_dir.name

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

    release = task.get("release")
    release_value = str(release).strip() if release is not None else ""
    if release_value and release_value.lower() not in {"null", "none"}:
        print(f"Release: {release_value}")
    if str(task.get("release_gate", "")).strip().lower() in {"true", "yes", "1"}:
        print("Release Gate: true")

    deps = _normalize_list(task.get("depends_on", []))
    if deps:
        depends_raw = task.get("depends_on")
        if isinstance(depends_raw, str):
            print(f"Dependencies: {depends_raw}")
        else:
            print(f"Dependencies: {', '.join(deps)}")
    else:
        print("Dependencies: None")

    print()
    if ctx.scope == "project":
        location = f"{sprint_dir}/tasks/{task.get('directory')}"
    else:
        location = _task_location_for_scope(ctx=ctx, directory=str(task.get("directory", "")))
    print(f"Location: {location}")
    print("Files: README.md, steps.md, commands.md, checklist.md, validation.md")
    return 0
