from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .context import Context
from .task_view import list_sprint_tasks
from .work_item_archiver import archive_work_items_for_task, refresh_indexes


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


def _load_allowed_statuses(*, ph_data_root: Path) -> list[str]:
    rules_path = ph_data_root / "process" / "checks" / "validation_rules.json"
    try:
        if rules_path.exists():
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
            raw = rules.get("task_status", {}).get("allowed_statuses")
            if isinstance(raw, list):
                out = [str(v).strip() for v in raw if str(v).strip()]
                if out:
                    return out
    except Exception:
        pass
    return ["todo", "doing", "review", "done", "blocked"]


def _update_task_yaml_status(*, task_yaml: Path, new_status: str) -> None:
    content = task_yaml.read_text(encoding="utf-8")
    lines = content.splitlines()
    replaced = False
    for idx, line in enumerate(lines):
        if line.startswith("status:"):
            lines[idx] = f"status: {new_status}"
            replaced = True
            break
    if not replaced:
        lines.append(f"status: {new_status}")
    task_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_task_status(*, ctx: Context, task_id: str, new_status: str, force: bool) -> int:
    task_id = (task_id or "").strip()
    new_status = (new_status or "").strip()

    valid_statuses = _load_allowed_statuses(ph_data_root=ctx.ph_data_root)
    if new_status not in valid_statuses:
        print(f"❌ Invalid status '{new_status}'. Must be one of: {valid_statuses}")
        return 1

    sprint_dir = _get_current_sprint_path(ph_data_root=ctx.ph_data_root)
    if sprint_dir is None:
        print("❌ No current sprint found. Run 'ph sprint plan' first.")
        return 1

    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        print(f"❌ No tasks directory found in {sprint_dir}")
        return 1

    task_dir: Path | None = None
    for candidate in tasks_dir.iterdir():
        if candidate.is_dir() and candidate.name.startswith(f"{task_id}-"):
            task_dir = candidate
            break

    if task_dir is None:
        print(f"❌ Task {task_id} not found in current sprint")
        return 1

    task_yaml = task_dir / "task.yaml"
    if not task_yaml.exists():
        print(f"❌ Task metadata not found: {task_yaml}")
        return 1

    meta = _parse_task_yaml(task_yaml.read_text(encoding="utf-8"))
    dependencies = _normalize_list(meta.get("depends_on", []))

    if new_status in {"doing", "review", "done"} and dependencies:
        tasks = list_sprint_tasks(sprint_dir=sprint_dir)
        task_map = {str(t.get("id", "")).strip(): t for t in tasks}
        unresolved = [
            dep
            for dep in dependencies
            if dep != "FIRST_TASK"
            if dep in task_map
            if str(task_map.get(dep, {}).get("status", "")).strip().lower() != "done"
        ]
        if unresolved and not force:
            csv = ", ".join(unresolved)
            print(f"❌ Cannot move {task_id} to '{new_status}' because dependencies are still open: {csv}")
            print("   Finish the prerequisite tasks or rerun with --force after explicit user approval.")
            return 1
        if unresolved and force:
            print(f"⚠️  Forcing status update despite unresolved dependencies: {', '.join(unresolved)}")

    _update_task_yaml_status(task_yaml=task_yaml, new_status=new_status)

    print(f"✅ Updated {task_id} status: {new_status}")

    if new_status == "doing":
        print(f"📋 Next: Read {task_dir}/steps.md for implementation details")
    elif new_status == "review":
        print(f"📋 Next: Ensure {task_dir}/checklist.md is complete")
    elif new_status == "done":
        print("🎉 Task complete! Run 'ph sprint status' to see updated progress")
        try:
            archived, errors = archive_work_items_for_task(
                task_id=task_id,
                sprint_id=sprint_dir.name,
                task_dir=task_dir,
                ph_data_root=ctx.ph_data_root,
                strict=False,
                dry_run=False,
            )
            if errors:
                for err in errors:
                    print(f"⚠️  {err}")
            if archived:
                refresh_indexes(ph_data_root=ctx.ph_data_root)
                print(f"📦 Archived {len(archived)} linked backlog/parking-lot item(s)")
        except Exception as exc:
            print(f"⚠️  Work-item archiving skipped: {exc}")

    return 0
