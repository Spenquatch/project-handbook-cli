from __future__ import annotations

import datetime as dt
import heapq
import json
import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

from .clock import local_today_from_now as clock_local_today_from_now
from .feature_status_updater import update_all_feature_status
from .question_manager import QuestionManager
from .sprint import get_sprint_dates

STAGE_PRIORITY: dict[str, int] = {
    "in-progress": 0,
    "in progress": 0,
    "active": 0,
    "doing": 0,
    "blocked": 1,
    "review": 2,
    "planning": 3,
    "planned": 3,
    "proposed": 4,
    "concept": 4,
    "backlog": 5,
    "todo": 5,
    "hold": 6,
    "on-hold": 6,
    "done": 7,
    "completed": 7,
    "complete": 7,
    "live": 8,
    "released": 8,
    "deprecated": 9,
    "unknown": 10,
}

CYCLE_PRIORITY: dict[str, int] = {"now": 0, "next": 1, "later": 2}


def _utc_now_iso_z(*, env: dict[str, str]) -> str:
    raw = (env.get("PH_FAKE_NOW") or "").strip()
    if raw:
        text = raw.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_config(*, ph_project_root: Path) -> dict[str, Any]:
    rules_path = ph_project_root / "process" / "checks" / "validation_rules.json"
    try:
        if rules_path.exists():
            return json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "sprint_management": {
            "mode": "bounded",
            "id_scheme": "date",
            "health_check_thresholds": {
                "blocked_percentage_red": 30,
                "progress_percentage_red": 50,
                "progress_check_day": 3,
            },
            "sprint_duration_days": 5,
        }
    }


def _calculate_velocity(tasks: list[dict[str, Any]]) -> dict[str, int]:
    metrics = {
        "total_points": 0,
        "completed_points": 0,
        "in_progress_points": 0,
        "blocked_points": 0,
        "todo_points": 0,
        "velocity_percentage": 0,
    }

    for task in tasks:
        try:
            points = int(task.get("story_points", 0) or 0)
        except Exception:
            points = 0

        status = str(task.get("status", "todo")).lower()

        metrics["total_points"] += points

        if status in {"done", "completed"}:
            metrics["completed_points"] += points
        elif status in {"doing", "in_progress", "in-progress", "review"}:
            metrics["in_progress_points"] += points
        elif status == "blocked":
            metrics["blocked_points"] += points
        else:
            metrics["todo_points"] += points

    if metrics["total_points"] > 0:
        metrics["velocity_percentage"] = int(metrics["completed_points"] * 100 / metrics["total_points"])

    return metrics


def _get_sprint_health(
    *, tasks: list[dict[str, Any]], day_of_sprint: int, config: dict[str, Any], mode: str = "timeboxed"
) -> str:
    thresholds = config.get("sprint_management", {}).get("health_check_thresholds", {})
    red_blocked = thresholds.get("blocked_percentage_red", 30)
    red_progress = thresholds.get("progress_percentage_red", 50)
    check_day = thresholds.get("progress_check_day", 3)

    metrics = _calculate_velocity(tasks)

    blocked_percentage = metrics["blocked_points"] * 100 / metrics["total_points"] if metrics["total_points"] > 0 else 0
    progress_percentage = (
        (metrics["completed_points"] + metrics["in_progress_points"]) * 100 / metrics["total_points"]
        if metrics["total_points"] > 0
        else 0
    )

    if mode == "bounded":
        if blocked_percentage > red_blocked:
            return f"🔴 RED - Too many blockers ({blocked_percentage:.0f}% > {red_blocked}%)"
        if blocked_percentage > red_blocked / 2:
            return f"🟡 YELLOW - Some blockers need attention ({blocked_percentage:.0f}%)"
        return "🟢 GREEN - Flowing"

    if blocked_percentage > red_blocked:
        return f"🔴 RED - Too many blockers ({blocked_percentage:.0f}% > {red_blocked}%)"
    if day_of_sprint >= check_day and progress_percentage < red_progress:
        return f"🔴 RED - Behind schedule ({progress_percentage:.0f}% < {red_progress}% by day {check_day})"

    if blocked_percentage > red_blocked / 2:
        return f"🟡 YELLOW - Some blockers need attention ({blocked_percentage:.0f}%)"
    if day_of_sprint >= check_day - 1 and progress_percentage < red_progress * 0.8:
        return f"🟡 YELLOW - Slightly behind schedule ({progress_percentage:.0f}%)"

    return "🟢 GREEN - On track"


def _strip(val: str) -> str:
    return val.strip().strip('"').strip("'")


def _parse_front_matter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}
    fm: dict[str, Any] = {}
    for line in lines[1:end]:
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    fm[k] = json.loads(v)
                except json.JSONDecodeError:
                    parts = [p.strip().strip("\"'") for p in v[1:-1].split(",")]
                    fm[k] = [p for p in parts if p]
            else:
                fm[k] = v
    return fm


def _parse_ymd_date(raw: Any) -> dt.date | None:
    if raw is None:
        return None
    text = str(raw).strip().strip('"').strip("'")
    if not text:
        return None
    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except Exception:
        return None


def _load_current_sprint_dir(*, sprints_dir: Path) -> Path | None:
    link = sprints_dir / "current"
    if not link.exists():
        return None
    try:
        sprint_dir = link.resolve()
    except FileNotFoundError:
        return None
    return sprint_dir if sprint_dir.exists() else None


def _get_sprint_dates_from_plan(*, sprint_dir: Path, mode: str, duration_days: int) -> tuple[dt.date, dt.date] | None:
    plan_path = sprint_dir / "plan.md"
    if not plan_path.exists():
        return None
    try:
        text = plan_path.read_text(encoding="utf-8")
    except Exception:
        return None
    fm = _parse_front_matter(text)

    if mode == "bounded":
        start = (
            _parse_ymd_date(fm.get("date")) or _parse_ymd_date(fm.get("created")) or _parse_ymd_date(fm.get("start"))
        )
        if start is None:
            return None
        end = start + dt.timedelta(days=max(1, duration_days) - 1)
        return start, end

    start = _parse_ymd_date(fm.get("start")) or _parse_ymd_date(fm.get("date"))
    end = _parse_ymd_date(fm.get("end"))
    if start is None or end is None:
        return None
    return start, end


def _parse_dependency_features(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        candidates = raw
    else:
        text = str(raw).strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                candidates = json.loads(text)
            except json.JSONDecodeError:
                parts = [seg.strip() for seg in text[1:-1].split(",")]
                candidates = [p.strip("\"'") for p in parts if p]
        else:
            candidates = [text]

    features: list[str] = []
    for entry in candidates:
        if isinstance(entry, str):
            cleaned = entry.strip()
            if cleaned.lower().startswith("feature:"):
                features.append(cleaned.split(":", 1)[1].strip())
    return features


def _load_roadmap_priorities(*, roadmap_dir: Path) -> dict[str, tuple[int, int]]:
    path = roadmap_dir / "now-next-later.md"
    priorities: dict[str, tuple[int, int]] = {}
    if not path.exists():
        return priorities
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return priorities

    section: str | None = None
    order_in_section = 0
    for line in text.splitlines():
        line = line.strip()
        lowered = line.lower()

        if lowered in CYCLE_PRIORITY:
            section = lowered
            order_in_section = 0
            continue

        if section and line.startswith("-"):
            content = line[1:].strip()
            feature_text, _, _ = content.partition(":")
            feature_key = feature_text.strip()
            if feature_key:
                priorities[feature_key] = (CYCLE_PRIORITY[section], order_in_section)
                order_in_section += 1
    return priorities


def _compute_feature_priority(
    *,
    feature: str,
    status_info: dict[str, Any],
    index: int,
    roadmap_priorities: dict[str, tuple[int, int]],
    dependent_count: int,
) -> tuple[int, int, int, int, int, str]:
    now_items = status_info.get("now", []) if isinstance(status_info, dict) else []
    next_items = status_info.get("next", []) if isinstance(status_info, dict) else []

    stage = (status_info.get("stage") or "unknown") if isinstance(status_info, dict) else "unknown"
    stage_key = stage.lower().strip().replace("-", " ")

    if feature in roadmap_priorities:
        cycle_rank, cycle_position = roadmap_priorities[feature]
    else:
        if now_items:
            cycle_rank = CYCLE_PRIORITY["now"]
        elif next_items:
            cycle_rank = CYCLE_PRIORITY["next"]
        else:
            cycle_rank = CYCLE_PRIORITY["later"]
        cycle_position = index

    dependent_rank = -dependent_count
    stage_rank = STAGE_PRIORITY.get(stage_key, 10)
    return (cycle_rank, cycle_position, dependent_rank, stage_rank, index, feature)


def _topologically_sort_features(
    *,
    features: list[str],
    dependencies: dict[str, list[str]],
    priority_hints: dict[str, tuple[int, int, int, int, int, str]],
) -> list[str]:
    adjacency: dict[str, set[str]] = {feature: set() for feature in features}
    indegree: dict[str, int] = {feature: 0 for feature in features}
    feature_set = set(features)

    for feature in features:
        for dep in dependencies.get(feature, []):
            if dep in feature_set:
                if feature not in adjacency[dep]:
                    adjacency[dep].add(feature)
                    indegree[feature] += 1

    heap: list[tuple[tuple[int, int, int, int, int, str], str]] = []

    def default_priority(f: str) -> tuple[int, int, int, int, int, str]:
        return (99, 99, 0, 99, 99, f)

    for feature in features:
        if indegree[feature] == 0:
            heapq.heappush(heap, (priority_hints.get(feature, default_priority(feature)), feature))

    ordered: list[str] = []
    while heap:
        _, current = heapq.heappop(heap)
        ordered.append(current)
        for neighbor in sorted(adjacency.get(current, [])):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                heapq.heappush(heap, (priority_hints.get(neighbor, default_priority(neighbor)), neighbor))

    if len(ordered) != len(features):
        remaining = [f for f in features if f not in ordered]
        remaining.sort(key=lambda f: priority_hints.get(f, default_priority(f)))
        ordered.extend(remaining)

    return ordered


def _parse_status_content(text: str) -> dict[str, Any]:
    info: dict[str, Any] = {"stage": None, "now": [], "next": [], "risks": []}
    if not text:
        return info

    lines = text.splitlines()
    section: str | None = None
    in_auto_generated = False

    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower()

        if "## Active Work (auto-generated)" in line or "Active Work (generated)" in line:
            in_auto_generated = True
            continue

        if in_auto_generated and line.startswith("## ") and "auto-generated" not in line:
            in_auto_generated = False

        if in_auto_generated:
            continue

        if lowered.startswith("stage:"):
            info["stage"] = stripped.split(":", 1)[1].strip()
            continue

        if lowered in ["now:", "next:", "risks:"]:
            section = lowered[:-1]
            continue

        if line.startswith("##"):
            section = None
            continue

        if section and stripped.startswith("-") and not in_auto_generated:
            content = stripped[1:].strip()
            if content:
                info[section].append(content)

    return info


def _bucket(status: str) -> str:
    s = (status or "").lower()
    if s in {"done", "completed"}:
        return "done"
    if s in {"review"}:
        return "review"
    if s in {"doing", "in_progress", "in-progress", "wip"}:
        return "in_progress"
    if s in {"blocked"}:
        return "blocked"
    if s in {"todo", "planned"}:
        return "planned"
    return "backlog"


def _load_current_sprint_context(*, sprints_dir: Path) -> dict[str, Any] | None:
    link = sprints_dir / "current"
    if not link.exists():
        return None
    try:
        sprint_dir = link.resolve()
    except FileNotFoundError:
        return None

    tasks: list[dict[str, Any]] = []
    tasks_dir = sprint_dir / "tasks"
    if tasks_dir.exists():
        for task_dir in sorted(tasks_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_yaml = task_dir / "task.yaml"
            if not task_yaml.exists():
                continue
            data: dict[str, Any] = {}
            try:
                content = task_yaml.read_text(encoding="utf-8")
            except Exception:
                continue
            for line in content.splitlines():
                if ":" not in line or line.strip().startswith("-"):
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    items = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
                    data[key] = items
                else:
                    data[key] = value
            data.setdefault("id", task_dir.name.split("-")[0])
            try:
                data["story_points"] = int(data.get("story_points", 0))
            except Exception:
                data["story_points"] = 0
            tasks.append(data)

    return {"sprint_id": sprint_dir.name, "tasks": tasks}


def _priority_rank(priority: str) -> int:
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
    return order.get(priority.upper(), 5) if priority else 5


def _write_status_summary(
    *,
    ph_project_root: Path,
    ph_data_root: Path,
    sprints_dir: Path,
    summary_path: Path,
    status_payload: dict[str, Any],
    env: dict[str, str],
) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    context = _load_current_sprint_context(sprints_dir=sprints_dir)
    if not context:
        summary_path.write_text("# Current Sprint\n\n_No active sprint_\n", encoding="utf-8")
        return

    sprint_id = str(context["sprint_id"])
    tasks = list(context["tasks"])
    config = _load_config(ph_project_root=ph_project_root)
    mode = str(config.get("sprint_management", {}).get("mode") or "bounded").strip().lower() or "bounded"
    duration_days = int(config.get("sprint_management", {}).get("sprint_duration_days") or 5)

    sprint_dir = _load_current_sprint_dir(sprints_dir=sprints_dir)
    plan_dates = (
        _get_sprint_dates_from_plan(sprint_dir=sprint_dir, mode=mode, duration_days=duration_days)
        if sprint_dir
        else None
    )

    if plan_dates is not None:
        start_date, end_date = plan_dates
    else:
        start_date, end_date = get_sprint_dates(sprint_id)

    today = clock_local_today_from_now(env=env)
    day_of_sprint = max(1, (today - start_date).days + 1)
    max_days = max(1, (end_date - start_date).days + 1)
    day_of_sprint = min(day_of_sprint, max_days)
    health = _get_sprint_health(tasks=tasks, day_of_sprint=day_of_sprint, config=config, mode=mode)
    velocity = _calculate_velocity(tasks)

    todo_tasks = [t for t in tasks if str(t.get("status", "")).lower() in {"todo", "planned"}]
    doing_tasks = [t for t in tasks if str(t.get("status", "")).lower() in {"doing", "in_progress", "in-progress"}]
    blocked_tasks = [t for t in tasks if str(t.get("status", "")).lower() == "blocked"]

    todo_tasks.sort(key=lambda t: (_priority_rank(str(t.get("prio", ""))), str(t.get("id", ""))))
    doing_tasks.sort(key=lambda t: str(t.get("id", "")))
    blocked_tasks.sort(key=lambda t: str(t.get("id", "")))

    lines: list[str] = []
    lines.append("# Status Snapshot")
    lines.append("")
    lines.append("## Current Sprint")
    lines.append(f"- ID: `{sprint_id}`")
    if mode == "bounded":
        created = start_date
        if today < created:
            days_until = (created - today).days
            lines.append(f"- Mode: bounded | Starts in {days_until} days (planned: {created.strftime('%Y-%m-%d')})")
        else:
            age_days = (today - created).days
            lines.append(f"- Mode: bounded | Age: {age_days} days (since {created.strftime('%Y-%m-%d')})")
    else:
        lines.append(
            f"- Day: {day_of_sprint} / {max_days} ({start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')})"
        )
    lines.append(f"- Health: {health}")
    lines.append("")

    def format_task(task: dict[str, Any]) -> str:
        owner = task.get("owner", "@owner")
        title = task.get("title", "Untitled")
        session = task.get("session")
        session_info = f" [{session}]" if session else ""
        release = task.get("release")
        release_info = ""
        if release and str(release).strip().lower() not in {"null", "none", ""}:
            release_info = f" [rel:{release}]"
        gate_info = ""
        if str(task.get("release_gate", "")).strip().lower() in {"true", "yes", "1"}:
            gate_info = " [gate]"
        return f"- `{task.get('id', '')}` ({owner}){session_info}{release_info}{gate_info} — {title}"

    total_points = velocity.get("total_points", 0)
    completed_points = velocity.get("completed_points", 0)
    in_progress_points = velocity.get("in_progress_points", 0)
    blocked_points = velocity.get("blocked_points", 0)

    lines.append("## Sprint Metrics")
    if total_points:
        lines.append(f"- Planned Points: {total_points}")
        lines.append(f"- Completed: {completed_points} ({(completed_points / total_points * 100):.0f}% )")
        lines.append(f"- In Progress: {in_progress_points} ({(in_progress_points / total_points * 100):.0f}% )")
        lines.append(f"- Blocked: {blocked_points} ({(blocked_points / total_points * 100):.0f}% )")
    else:
        lines.append("- No pointed work scheduled")
    lines.append("")

    owner_map: dict[str, list[dict[str, Any]]] = {}
    for task in doing_tasks:
        owner = task.get("owner", "@owner")
        owner_map.setdefault(str(owner), []).append(task)
    for tasks_list in owner_map.values():
        tasks_list.sort(key=lambda t: str(t.get("id", "")))

    lines.append("## Active Work by Owner")
    if owner_map:
        for owner in sorted(owner_map.keys()):
            lines.append(f"- **{owner}**")
            for task in owner_map[owner][:2]:
                lines.append(f"  - `{task.get('id', '')}` — {task.get('title', 'Untitled')}")
    else:
        lines.append("- No tasks currently in progress")
    lines.append("")

    lines.append("## Open Questions")
    try:
        qm = QuestionManager(ph_data_root=ph_data_root, env=env)
        questions = [q for q in qm.get_questions() if q.status.strip().lower() == "open"]
    except Exception:
        questions = []

    def q_sort_key(q) -> tuple[int, str]:
        sev = (getattr(q, "severity", "") or "").strip().lower()
        sev_rank = 0 if sev == "blocking" else 1
        return (sev_rank, str(getattr(q, "id", "")))

    questions = sorted(questions, key=q_sort_key)
    if questions:
        for q in questions[:10]:
            sev = (q.severity or "non-blocking").strip().lower()
            scope = (q.scope or "project").strip().lower()
            sprint = f" sprint={q.sprint}" if q.sprint else ""
            lines.append(f"- `{q.id}` [{sev}] [{scope}]{sprint} — {q.title}")
        if len(questions) > 10:
            lines.append(f"- …and {len(questions) - 10} more (run `ph question list`)")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Blockers")
    if blocked_tasks:
        for task in blocked_tasks[:5]:
            lines.append(f"{format_task(task)} ")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Next Up")
    if todo_tasks:
        for task in todo_tasks[:5]:
            lines.append(f"{format_task(task)} [prio {task.get('prio', 'P2')}]")
    else:
        lines.append("- Backlog is clear")
    lines.append("")

    project_section = status_payload.get("project", {})
    upcoming = project_section.get("next", [])
    lines.append("## Upcoming Milestones")
    if upcoming:
        for item in upcoming[:5]:
            lines.append(f"- {item}")
    else:
        lines.append("- Align with release plan for next milestones")
    lines.append("")

    lines.append("## Quick Links")
    lines.append("- `ph onboarding` (default guide)")
    lines.append("- `ph onboarding session sprint-planning` to facilitate planning")
    lines.append("- `ph onboarding session sprint-closing` to close a sprint cleanly")
    lines.append("- `ph onboarding session research-discovery` for research-discovery decisions")
    lines.append("- `ph onboarding session continue-session` for continuity")
    lines.append("")
    lines.append("> Generated with `ph status`.")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _generate_status_payload(*, ph_data_root: Path, env: dict[str, str]) -> dict[str, Any]:
    sprints = ph_data_root / "sprints"
    features = ph_data_root / "features"
    roadmap = ph_data_root / "roadmap"

    phases: list[dict[str, Any]] = []
    totals: dict[str, int] = {k: 0 for k in ["backlog", "planned", "in_progress", "review", "blocked", "done"]}
    features_data: dict[str, dict[str, list[dict[str, Any]]]] = {}
    features_summary: list[dict[str, Any]] = []

    roadmap_priorities = _load_roadmap_priorities(roadmap_dir=roadmap)

    feature_dependencies: dict[str, list[str]] = {}
    feature_status_map: dict[str, dict[str, Any]] = {}
    feature_index_map: dict[str, int] = {}

    if features.exists():
        feature_dirs = sorted([p for p in features.iterdir() if p.is_dir()])
        for idx, feat_dir in enumerate(feature_dirs):
            feature_key = feat_dir.name

            overview_path = feat_dir / "overview.md"
            if overview_path.exists():
                try:
                    text = overview_path.read_text(encoding="utf-8")
                    fm = _parse_front_matter(text)
                    dependencies = _parse_dependency_features(fm.get("dependencies"))
                    feature_dependencies[feature_key] = dependencies
                except Exception:
                    feature_dependencies[feature_key] = []

            status_path = feat_dir / "status.md"
            if status_path.exists():
                try:
                    text = status_path.read_text(encoding="utf-8")
                    status_info = _parse_status_content(text)
                    feature_status_map[feature_key] = status_info
                    feature_index_map[feature_key] = idx

                    features_summary.append(
                        {
                            "key": feature_key,
                            "stage": status_info.get("stage"),
                            "now": status_info.get("now", []),
                            "next": status_info.get("next", []),
                            "risks": status_info.get("risks", []),
                        }
                    )
                except Exception:
                    pass

    if sprints.exists():
        for year_dir in sprints.iterdir():
            if not year_dir.is_dir() or year_dir.name == "current":
                continue

            for sprint_dir in year_dir.iterdir():
                if not sprint_dir.is_dir() or not sprint_dir.name.startswith("SPRINT-"):
                    continue

                tasks_dir = sprint_dir / "tasks"
                if not tasks_dir.exists():
                    continue

                sprint_tasks: list[dict[str, Any]] = []
                for task_dir in tasks_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    task_yaml = task_dir / "task.yaml"
                    if not task_yaml.exists():
                        continue
                    try:
                        content = task_yaml.read_text(encoding="utf-8")
                        task_data: dict[str, Any] = {}
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
                        sprint_tasks.append(task_data)
                    except Exception as exc:
                        print(f"Error parsing {task_yaml}: {exc}")

                if sprint_tasks:
                    phases.append(
                        {
                            "name": sprint_dir.name,
                            "phase": sprint_dir.name,
                            "title": f"Sprint {sprint_dir.name}",
                            "features": list({t.get("feature", "unknown") for t in sprint_tasks}),
                            "decisions": list({t.get("decision", "") for t in sprint_tasks if t.get("decision")}),
                            "tasks": [t.get("id") for t in sprint_tasks],
                        }
                    )

                    for t in sprint_tasks:
                        b = _bucket(str(t.get("status", "")))
                        totals[b] = totals.get(b, 0) + 1
                        feat = str(t.get("feature", "unknown"))
                        features_data.setdefault(feat, {"open": [], "done": []})
                        entry = {
                            "id": t.get("id"),
                            "title": t.get("title"),
                            "sprint": sprint_dir.name,
                            "status": t.get("status"),
                            "story_points": t.get("story_points"),
                            "prio": t.get("prio"),
                            "decision": t.get("decision"),
                        }
                        if b == "done":
                            features_data[feat]["done"].append(entry)
                        else:
                            features_data[feat]["open"].append(entry)

    feature_keys = [s["key"] for s in features_summary]
    dependent_counts = {feature: 0 for feature in feature_keys}
    for feature, deps in feature_dependencies.items():
        for dep in deps:
            if dep in dependent_counts:
                dependent_counts[dep] += 1

    feature_priority_hints: dict[str, tuple[int, int, int, int, int, str]] = {}
    for feature in feature_keys:
        feature_priority_hints[feature] = _compute_feature_priority(
            feature=feature,
            status_info=feature_status_map.get(feature, {}),
            index=feature_index_map.get(feature, 0),
            roadmap_priorities=roadmap_priorities,
            dependent_count=dependent_counts.get(feature, 0),
        )

    feature_order = _topologically_sort_features(
        features=feature_keys, dependencies=feature_dependencies, priority_hints=feature_priority_hints
    )

    summary_by_key = {s["key"]: s for s in features_summary}
    features_summary = [summary_by_key[key] for key in feature_order if key in summary_by_key]

    project_now: list[str] = []
    project_next: list[str] = []
    project_risks: list[dict[str, Any]] = []

    for feature in features_summary:
        for item in feature.get("now", []):
            project_now.append(f"{feature['key']}: {item}")
        for item in feature.get("next", []):
            project_next.append(f"{feature['key']}: {item}")
        for item in feature.get("risks", []):
            project_risks.append({"feature": feature["key"], "risk": item})

    return {
        "generated_at": _utc_now_iso_z(env=env),
        "phases": phases,
        "totals": totals,
        "features": features_data,
        "features_summary": features_summary,
        "project": {"now": project_now, "next": project_next, "risks": project_risks},
    }


class StatusResult(tuple[Path, Path, str | None]):
    __slots__ = ()

    @property
    def json_path(self) -> Path:
        return self[0]

    @property
    def summary_path(self) -> Path:
        return self[1]

    @property
    def feature_update_message(self) -> str | None:
        return self[2]


def run_status(
    *, ph_root: Path, ph_project_root: Path, ph_data_root: Path, env: dict[str, str] | None = None
) -> StatusResult:
    env = env or os.environ
    status_dir = ph_data_root / "status"
    status_dir.mkdir(parents=True, exist_ok=True)

    current_json = status_dir / "current.json"
    summary_md = status_dir / "current_summary.md"

    payload = _generate_status_payload(ph_data_root=ph_data_root, env=env)
    current_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_status_summary(
        ph_project_root=ph_project_root,
        ph_data_root=ph_data_root,
        sprints_dir=ph_data_root / "sprints",
        summary_path=summary_md,
        status_payload=payload,
        env=env,
    )

    feature_update_message: str | None = None
    try:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = update_all_feature_status(ph_data_root=ph_data_root, env=env)
        if exit_code == 0:
            feature_update_message = "Updated feature status files"
        else:
            feature_update_message = "Warning: Feature status update failed"
    except Exception as exc:
        feature_update_message = f"Warning: Could not update feature status: {exc}"

    return StatusResult((current_json, summary_md, feature_update_message))
