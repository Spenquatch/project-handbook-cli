from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .context import Context
from .release import (
    collect_release_tagged_tasks,
    get_current_release,
    get_release_timeline_info,
    is_sprint_archived,
    list_release_versions,
    normalize_version,
    parse_task_yaml,
    summarize_tagged_tasks,
)
from .sprint import sprint_dir_from_id
from .sprint_status import dependency_ready, is_sprint_gate_task, sort_tasks


def _repo_rel(*, ctx: Context, path: Path) -> str:
    try:
        return path.relative_to(ctx.ph_root).as_posix()
    except Exception:
        return path.as_posix()


def _scope_prefix(ctx: Context) -> str:
    return ".project-handbook" if ctx.scope == "project" else ".project-handbook/system"


def _resolve_current_sprint_dir(*, ctx: Context) -> Path | None:
    link = ctx.ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return resolved if resolved.exists() else None


def _sprint_paths(*, ctx: Context, sprint_id: str, state: str, is_current: bool) -> dict[str, str]:
    prefix = _scope_prefix(ctx)
    if is_current:
        return {"plan": f"{prefix}/sprints/current/plan.md"}

    sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
    if state == "closed":
        year = sprint_id.split("-")[1] if "-" in sprint_id else sprint_id
        sprint_dir = ctx.ph_data_root / "sprints" / "archive" / year / sprint_id

    return {"plan": _repo_rel(ctx=ctx, path=sprint_dir / "plan.md")}


def _release_paths(*, ctx: Context, release_version: str, used_current_pointer: bool) -> dict[str, str]:
    prefix = ".project-handbook"
    if used_current_pointer:
        plan = f"{prefix}/releases/current/plan.md"
    else:
        plan = f"{prefix}/releases/{release_version}/plan.md"
    pointer = f"{prefix}/releases/current.txt"
    return {"plan": plan, "pointer": pointer}


def _task_id_sort_key(task_id: str) -> tuple[int, str]:
    raw = (task_id or "").strip()
    if raw.startswith("TASK-"):
        suffix = raw.split("-", 1)[1]
        try:
            return (int(suffix), raw)
        except Exception:
            return (999999, raw)
    return (999999, raw)


def _normalize_status(raw: Any) -> str:
    s = str(raw or "todo").strip().lower()
    if s == "completed":
        return "done"
    return s


def _collect_sprint_tasks(*, sprint_dir: Path) -> list[dict[str, Any]]:
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
        task = parse_task_yaml(task_yaml=task_yaml)
        task.setdefault("id", task_dir.name.split("-", 1)[0])
        task.setdefault("title", task_dir.name)
        task["directory"] = task_dir.name
        tasks.append(task)
    return sort_tasks(tasks)


def _task_path(
    *,
    ctx: Context,
    sprint_id: str,
    sprint_state: str,
    is_current_sprint: bool,
    task_dir_name: str,
    filename: str,
) -> str:
    prefix = _scope_prefix(ctx)
    if is_current_sprint:
        return f"{prefix}/sprints/current/tasks/{task_dir_name}/{filename}"

    sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
    if sprint_state == "closed":
        year = sprint_id.split("-")[1] if "-" in sprint_id else sprint_id
        sprint_dir = ctx.ph_data_root / "sprints" / "archive" / year / sprint_id
    return _repo_rel(ctx=ctx, path=sprint_dir / "tasks" / task_dir_name / filename)


def _resolve_sprint_state(*, ctx: Context, sprint_id: str, current_sprint_id: str | None) -> tuple[str, bool]:
    if is_sprint_archived(ph_root=ctx.ph_data_root, sprint_id=sprint_id):
        return ("closed", False)
    if current_sprint_id and sprint_id == current_sprint_id:
        return ("open", True)
    sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
    if sprint_dir.exists():
        return ("locked", False)
    return ("locked", False)


def _first_incomplete_sprint_gate(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    gates = [t for t in tasks if is_sprint_gate_task(t)]
    gates.sort(key=lambda t: _task_id_sort_key(str(t.get("id", ""))))
    for gate in gates:
        if _normalize_status(gate.get("status")) != "done":
            return gate
    return None


def _summarize_sprint_gates(tasks: list[dict[str, Any]]) -> tuple[int, int, dict[str, Any] | None]:
    gates = [t for t in tasks if is_sprint_gate_task(t)]
    total = len(gates)
    done = sum(1 for t in gates if _normalize_status(t.get("status")) == "done")
    first_incomplete = _first_incomplete_sprint_gate(tasks)
    return total, done, first_incomplete


def _compute_next_actions(
    *,
    ctx: Context,
    sprint_id: str | None,
    sprint_state: str | None,
    is_current_sprint: bool,
    sprint_tasks: list[dict[str, Any]] | None,
    release_version: str | None,
    release_timeline: dict[str, object] | None,
    env: dict[str, str],
) -> list[dict[str, str | None]]:
    _ = env
    actions: list[dict[str, str | None]] = []

    def add(
        priority: str,
        code: str,
        title: str,
        why: str,
        do: str,
        path: str | None = None,
    ) -> None:
        if len(actions) >= 5:
            return
        actions.append(
            {
                "priority": priority,
                "code": code,
                "title": title,
                "why": why,
                "do": do,
                "path": path,
            }
        )

    if sprint_id is None:
        add(
            "P0",
            "no_active_sprint",
            "Create/open a sprint",
            "No active sprint (sprints/current not set).",
            "ph sprint plan",
        )
        return actions

    current_sprint_dir = _resolve_current_sprint_dir(ctx=ctx)
    current_sprint_id = current_sprint_dir.name if current_sprint_dir else None

    tasks = sprint_tasks or []
    gate_total, gate_done, first_incomplete_gate = _summarize_sprint_gates(tasks)
    if gate_total == 0:
        add(
            "P0",
            "sprint_gate_missing",
            "Create sprint gate task",
            "Sprint gate task required per sprint.",
            (
                "ph task create --title 'Sprint Gate: <goal>' --feature sprint --decision N/A "
                "--type sprint-gate --points 3"
            ),
            (
                f"{_scope_prefix(ctx)}/sprints/current/plan.md"
                if is_current_sprint
                else _sprint_paths(ctx=ctx, sprint_id=sprint_id, state=str(sprint_state or "locked"), is_current=False)[
                    "plan"
                ]
            ),
        )
    elif gate_done < gate_total and first_incomplete_gate is not None:
        task_id = str(first_incomplete_gate.get("id", "TASK-???"))
        title = f"Complete sprint gate {task_id}"
        why = f"Sprint gate must close last; currently status={_normalize_status(first_incomplete_gate.get('status'))}."
        task_dir = str(first_incomplete_gate.get("directory", ""))
        validation_path = (
            _task_path(
                ctx=ctx,
                sprint_id=sprint_id,
                sprint_state=str(sprint_state or "locked"),
                is_current_sprint=is_current_sprint,
                task_dir_name=task_dir,
                filename="validation.md",
            )
            if task_dir
            else None
        )
        add(
            "P0",
            "sprint_gate_incomplete",
            title,
            why,
            f"ph task status --id {task_id} --status done",
            validation_path,
        )

    if ctx.scope == "project" and release_version is None:
        available = list_release_versions(ph_root=ctx.ph_project_root)
        if available:
            latest = available[-1]
            add(
                "P1",
                "release_missing",
                "Activate a release",
                "No active release pointer (releases exist).",
                f"ph release activate --release {latest}",
                ".project-handbook/releases/current.txt",
            )

    if ctx.scope == "project" and release_version:
        tagged_tasks = collect_release_tagged_tasks(ph_root=ctx.ph_data_root, version=release_version)
        sprint_timeline = None
        if release_timeline and isinstance(release_timeline.get("sprint_ids"), list):
            sprint_timeline = [str(x) for x in release_timeline.get("sprint_ids") or [] if str(x)]
        summary = summarize_tagged_tasks(tasks=tagged_tasks, sprint_timeline=sprint_timeline)
        gates_total = int(summary.get("gates_total", 0) or 0)
        gates_done = int(summary.get("gates_done", 0) or 0)
        if gates_total > 0 and gates_done < gates_total:

            def _is_gate(t: dict[str, Any]) -> bool:
                return bool(t.get("release_gate") is True) or str(t.get("release_gate", "")).strip().lower() in {
                    "true",
                    "yes",
                    "1",
                }

            gates = [t for t in tagged_tasks if _is_gate(t) and _normalize_status(t.get("status")) != "done"]
            gates.sort(key=lambda t: (str(t.get("sprint", "")), _task_id_sort_key(str(t.get("id", "")))))
            gate = None
            if sprint_id:
                for cand in gates:
                    if str(cand.get("sprint", "")) == sprint_id:
                        gate = cand
                        break
            gate = gate or (gates[0] if gates else None)
            if gate:
                gate_id = str(gate.get("id", "TASK-???"))
                gate_sprint = str(gate.get("sprint", "")).strip()
                gate_dir = str(gate.get("directory", "")).strip()
                gate_sprint_state, gate_is_current = _resolve_sprint_state(
                    ctx=ctx,
                    sprint_id=gate_sprint,
                    current_sprint_id=current_sprint_id,
                )
                gate_path = (
                    _task_path(
                        ctx=ctx,
                        sprint_id=gate_sprint,
                        sprint_state=gate_sprint_state,
                        is_current_sprint=gate_is_current,
                        task_dir_name=gate_dir,
                        filename="validation.md",
                    )
                    if gate_sprint and gate_dir
                    else None
                )
                add(
                    "P1",
                    "release_gate_incomplete",
                    f"Complete release gate {gate_id}",
                    "Release readiness is gate-first; at least one release gate task is incomplete.",
                    f"ph task status --id {gate_id} --status done",
                    gate_path,
                )

    active_task = None
    for task in tasks:
        if _normalize_status(task.get("status")) in {"doing", "review"}:
            active_task = task
            break
    if active_task is None:
        task_map = {str(t.get("id")): t for t in tasks if t.get("id")}
        for task in tasks:
            if _normalize_status(task.get("status")) not in {"todo", "planned"}:
                continue
            if dependency_ready(task, task_map):  # type: ignore[arg-type]
                task_id = str(task.get("id", "TASK-???"))
                task_dir = str(task.get("directory", "")).strip()
                steps_path = (
                    _task_path(
                        ctx=ctx,
                        sprint_id=sprint_id,
                        sprint_state=str(sprint_state or "locked"),
                        is_current_sprint=is_current_sprint,
                        task_dir_name=task_dir,
                        filename="steps.md",
                    )
                    if task_dir
                    else None
                )
                add(
                    "P2",
                    "pull_next_task",
                    f"Start next task {task_id}",
                    "No task in doing/review; next planned task is dependency-ready.",
                    f"ph task status --id {task_id} --status doing",
                    steps_path,
                )
                break

    return actions


def run_next(
    *,
    ph_root: Path,
    ctx: Context,
    release: str | None,
    sprint: str | None,
    format: str,
    env: dict[str, str],
) -> int:
    _ = ph_root
    fmt = (format or "text").strip().lower()
    if fmt not in {"text", "json"}:
        fmt = "text"

    current_sprint_dir = _resolve_current_sprint_dir(ctx=ctx)
    current_sprint_id = current_sprint_dir.name if current_sprint_dir else None

    sprint_id: str | None = None
    sprint_dir: Path | None = None
    if sprint is None or sprint.strip() in {"", "current"}:
        sprint_dir = current_sprint_dir
        sprint_id = current_sprint_id
    else:
        sprint_id = sprint.strip()
        candidate = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)
        if candidate.exists():
            sprint_dir = candidate
        else:
            year = sprint_id.split("-")[1] if "-" in sprint_id else sprint_id
            archived = ctx.ph_data_root / "sprints" / "archive" / year / sprint_id
            if archived.exists():
                sprint_dir = archived

    sprint_state: str | None = None
    is_current_sprint = False
    if sprint_id is not None:
        sprint_state, is_current_sprint = _resolve_sprint_state(
            ctx=ctx,
            sprint_id=sprint_id,
            current_sprint_id=current_sprint_id,
        )

    sprint_paths = (
        _sprint_paths(
            ctx=ctx,
            sprint_id=sprint_id or "",
            state=str(sprint_state or "locked"),
            is_current=is_current_sprint,
        )
        if sprint_id
        else {"plan": f"{_scope_prefix(ctx)}/sprints/current/plan.md"}
    )

    sprint_tasks = _collect_sprint_tasks(sprint_dir=sprint_dir) if sprint_dir else []
    if sprint_dir:
        gate_total, gate_done, first_incomplete_gate = _summarize_sprint_gates(sprint_tasks)
    else:
        gate_total, gate_done, first_incomplete_gate = (0, 0, None)

    release_version: str | None = None
    used_current_pointer = False
    release_timeline: dict[str, object] | None = None
    release_paths: dict[str, str] | None = None
    release_slots: list[dict[str, object]] | None = None
    release_slot_count: int | None = None
    release_current_slot: int | None = None
    release_archived_slots: list[int] = []

    if ctx.scope == "project":
        if release is None or release.strip() in {"", "current"}:
            found = get_current_release(ph_root=ctx.ph_project_root)
            if found:
                release_version = found
                used_current_pointer = True
        else:
            release_version = normalize_version(release)

        if release_version:
            release_timeline = get_release_timeline_info(ph_root=ctx.ph_data_root, version=release_version)
            release_paths = _release_paths(
                ctx=ctx,
                release_version=release_version,
                used_current_pointer=used_current_pointer,
            )
            timeline_mode = str(release_timeline.get("timeline_mode") or "").strip().lower()
            release_slot_count = int(release_timeline.get("planned_sprints") or 0) or None

            if timeline_mode == "sprint_slots":
                raw_slots = release_timeline.get("sprint_slots")
                if not isinstance(raw_slots, list):
                    raw_slots = []
                slots = [int(s) for s in raw_slots if isinstance(s, int) or (isinstance(s, str) and str(s).isdigit())]
                assignments = (
                    release_timeline.get("slot_assignments")
                    if isinstance(release_timeline.get("slot_assignments"), dict)
                    else {}
                )
                release_slots = []
                for slot in slots:
                    sprint_assigned = assignments.get(slot)
                    sprint_assigned = str(sprint_assigned) if sprint_assigned is not None else None
                    state = "unassigned"
                    if sprint_assigned:
                        if is_sprint_archived(ph_root=ctx.ph_data_root, sprint_id=sprint_assigned):
                            state = "closed"
                            release_archived_slots.append(int(slot))
                        elif sprint_id and sprint_assigned == sprint_id:
                            state = "open"
                        else:
                            state = "locked"
                    release_slots.append({"slot": int(slot), "sprint": sprint_assigned, "state": state})

                if sprint_id:
                    release_current_slot = None
                    for entry in release_slots:
                        if str(entry.get("sprint") or "") == sprint_id:
                            release_current_slot = int(entry.get("slot") or 0) or None
                            break
                else:
                    raw_current = release_timeline.get("current_sprint_slot")
                    release_current_slot = int(raw_current) if isinstance(raw_current, int) else None
            else:
                sprint_ids = (
                    [str(x) for x in (release_timeline.get("sprint_ids") or [])]
                    if isinstance(release_timeline.get("sprint_ids"), list)
                    else []
                )
                release_slots = []
                for idx, sid in enumerate(sprint_ids, 1):
                    if not sid:
                        continue
                    state = "closed" if is_sprint_archived(ph_root=ctx.ph_data_root, sprint_id=sid) else "locked"
                    if sprint_id and sid == sprint_id and state != "closed":
                        state = "open"
                    if state == "closed":
                        release_archived_slots.append(idx)
                    release_slots.append({"slot": idx, "sprint": sid, "state": state})

                if sprint_id and sprint_id in sprint_ids:
                    release_current_slot = sprint_ids.index(sprint_id) + 1
                else:
                    raw_current = release_timeline.get("current_sprint_index")
                    release_current_slot = int(raw_current) if isinstance(raw_current, int) else None

    actions = _compute_next_actions(
        ctx=ctx,
        sprint_id=sprint_id,
        sprint_state=sprint_state,
        is_current_sprint=is_current_sprint,
        sprint_tasks=sprint_tasks,
        release_version=release_version,
        release_timeline=release_timeline,
        env=env,
    )

    if fmt == "json":
        payload: dict[str, Any] = {
            "type": "ph-next",
            "schema_version": 1,
            "scope": ctx.scope,
            "release": None,
            "sprint": None,
            "next_actions": actions,
        }

        if ctx.scope == "project":
            payload["release"] = (
                {
                    "active": release_version,
                    "planned_sprints": release_slot_count,
                    "timeline_mode": str(release_timeline.get("timeline_mode")) if release_timeline else None,
                    "current_slot": release_current_slot,
                    "archived_slots": release_archived_slots,
                    "slots": release_slots,
                    "paths": release_paths,
                }
                if release_version
                else {
                    "active": None,
                    "planned_sprints": None,
                    "timeline_mode": None,
                    "current_slot": None,
                    "archived_slots": [],
                    "slots": [],
                    "paths": {
                        "pointer": ".project-handbook/releases/current.txt",
                        "plan": ".project-handbook/releases/current/plan.md",
                    },
                }
            )

        payload["sprint"] = (
            {
                "active": sprint_id,
                "state": sprint_state,
                "slot": release_current_slot if ctx.scope == "project" else None,
                "paths": sprint_paths,
                "sprint_gates": {
                    "total": gate_total,
                    "done": gate_done,
                    "first_incomplete": str(first_incomplete_gate.get("id")) if first_incomplete_gate else None,
                },
            }
            if sprint_id
            else {
                "active": None,
                "state": None,
                "slot": None,
                "paths": {"plan": f"{_scope_prefix(ctx)}/sprints/current/plan.md"},
                "sprint_gates": {"total": 0, "done": 0, "first_incomplete": None},
            }
        )

        print(json.dumps(payload, indent=2))
        return 0

    print("🧭 NEXT")
    print("=" * 80)
    print(f"Scope: {ctx.scope}")
    print()

    print("Release:")
    if ctx.scope == "system":
        print("  Active: n/a (system scope)")
    else:
        print(f"  Active: {release_version or 'none'}")
        if release_version:
            print(f"  Slots: {release_slot_count or '?'}")
            print(f"  Current slot: {release_current_slot if release_current_slot is not None else 'unknown'}")
            if release_archived_slots:
                closed_csv = ", ".join(str(x) for x in release_archived_slots)
            else:
                closed_csv = "none"
            print(f"  Archived/closed slots: {closed_csv}")
            if release_paths:
                print(f"  Plan: {release_paths.get('plan')}")
                pointer_path = release_paths.get("pointer") or ".project-handbook/releases/current.txt"
                pointer_file = ctx.ph_project_root / "releases" / "current.txt"
                pointer_note = "" if pointer_file.exists() else " (missing)"
                print(f"  Pointer: {pointer_path}{pointer_note}")
        else:
            print("  Slots: ?")
            print("  Current slot: n/a")
            print("  Archived/closed slots: n/a")
            print("  Plan: .project-handbook/releases/current/plan.md")
            pointer_file = ctx.ph_project_root / "releases" / "current.txt"
            pointer_note = "" if pointer_file.exists() else " (missing)"
            print(f"  Pointer: .project-handbook/releases/current.txt{pointer_note}")

    print()
    print("Sprint:")
    print(f"  Active: {sprint_id or 'none'}")
    print(f"  State: {sprint_state or 'unknown'}")
    if ctx.scope == "project":
        print(f"  Slot (active release): {release_current_slot if release_current_slot is not None else 'n/a'}")
    else:
        print("  Slot (active release): n/a")
    print(f"  Plan: {sprint_paths.get('plan')}")
    if sprint_id:
        if gate_total == 0:
            print("  Sprint gate: missing")
        else:
            gate_line = f"{gate_done}/{gate_total} done"
            if first_incomplete_gate is not None:
                gid = str(first_incomplete_gate.get("id", "TASK-???"))
                gtitle = str(first_incomplete_gate.get("title", "") or "")
                suffix = f" (first incomplete: {gid}{' — ' + gtitle if gtitle else ''})"
            else:
                suffix = ""
            print(f"  Sprint gate: {gate_line}{suffix}")
    else:
        print("  Sprint gate: n/a")

    print()
    print("Next actions:")
    if not actions:
        print("  (none)")
        return 0

    for idx, action in enumerate(actions, 1):
        prio = str(action.get("priority") or "P?")
        title = str(action.get("title") or "").strip() or "(missing title)"
        why = str(action.get("why") or "").strip()
        do = str(action.get("do") or "").strip()
        path = action.get("path")
        print(f"  {idx}) [{prio}] {title}")
        if why:
            print(f"     - Why: {why}")
        if do:
            print(f"     - Do: {do}")
        if path:
            print(f"     - Path: {path}")

    return 0
