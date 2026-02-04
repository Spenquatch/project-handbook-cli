from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .clock import now as clock_now
from .clock import today as clock_today


@dataclass(frozen=True)
class DailyPaths:
    status_file: Path
    daily_dir: Path


def relative_markdown_link(*, from_dir: Path, target: Path) -> str:
    rel = os.path.relpath(str(target), str(from_dir))
    return rel.replace(os.sep, "/")


def _load_rules_or_default(*, ph_root: Path) -> dict[str, Any]:
    rules_path = ph_root / "process" / "checks" / "validation_rules.json"
    default_config: dict[str, Any] = {
        "daily_status": {
            "skip_weekends": True,
            "weekend_days": [5, 6],
            "max_hours_without_update": 24,
            "monday_weekend_summary": True,
            "friday_week_wrapup": True,
        }
    }

    try:
        if rules_path.exists():
            return json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        return default_config

    return default_config


def _fallback_iso_sprint_id(*, env: dict[str, str]) -> str:
    day = clock_today(env=env)
    week_num = day.isocalendar()[1]
    year = day.year
    return f"SPRINT-{year}-W{week_num:02d}"


def _resolve_current_sprint_path(*, ph_data_root: Path) -> Path | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return resolved if resolved.exists() else None


def get_current_sprint(*, ph_data_root: Path, env: dict[str, str]) -> str:
    path = _resolve_current_sprint_path(ph_data_root=ph_data_root)
    if path:
        return path.name
    return _fallback_iso_sprint_id(env=env)


def _guess_current_sprint_dir(*, ph_data_root: Path, env: dict[str, str]) -> Path | None:
    path = _resolve_current_sprint_path(ph_data_root=ph_data_root)
    if path:
        return path

    sprint_id = _fallback_iso_sprint_id(env=env)
    parts = sprint_id.split("-")
    if len(parts) < 2:
        return None
    year = parts[1]
    candidate = ph_data_root / "sprints" / year / sprint_id
    return candidate if candidate.exists() else None


def should_generate_daily(*, ph_root: Path, env: dict[str, str]) -> bool:
    config = _load_rules_or_default(ph_root=ph_root)
    daily_config = config.get("daily_status", {}) if isinstance(config, dict) else {}

    if not daily_config.get("skip_weekends", True):
        return True

    day = clock_today(env=env)
    weekend_days = daily_config.get("weekend_days", [5, 6])
    return day.weekday() not in weekend_days


def daily_paths_for_date(*, ph_data_root: Path, date: dt.date) -> DailyPaths:
    daily_dir = ph_data_root / "status" / "daily" / date.strftime("%Y") / date.strftime("%m")
    status_file = daily_dir / f"{date.strftime('%d')}.md"
    return DailyPaths(status_file=status_file, daily_dir=daily_dir)


def collect_sprint_tasks(*, ph_data_root: Path, env: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    tasks_by_status: dict[str, list[dict[str, Any]]] = {
        "todo": [],
        "doing": [],
        "review": [],
        "done": [],
        "blocked": [],
    }

    sprint_dir = _guess_current_sprint_dir(ph_data_root=ph_data_root, env=env)
    if sprint_dir is None:
        return tasks_by_status

    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        return tasks_by_status

    for task_dir in tasks_dir.iterdir():
        if not task_dir.is_dir():
            continue

        task_yaml = task_dir / "task.yaml"
        if not task_yaml.exists():
            continue

        try:
            content = task_yaml.read_text(encoding="utf-8")
        except Exception:
            continue

        task_data: dict[str, Any] = {}
        for line in content.splitlines():
            if ":" in line and not line.strip().startswith("-"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value.isdigit():
                    task_data[key] = int(value)
                else:
                    task_data[key] = value

        status = str(task_data.get("status", "todo") or "todo")
        if status in tasks_by_status:
            tasks_by_status[status].append(
                {
                    "id": task_data.get("id"),
                    "title": task_data.get("title"),
                    "story_points": task_data.get("story_points", 0),
                    "owner": task_data.get("owner"),
                    "blocked_reason": task_data.get("blocked_reason", ""),
                }
            )

    return tasks_by_status


def generate_daily_template(*, ph_root: Path, ph_data_root: Path, date: dt.date, env: dict[str, str]) -> str:
    sprint_id = get_current_sprint(ph_data_root=ph_data_root, env=env)
    tasks = collect_sprint_tasks(ph_data_root=ph_data_root, env=env)

    paths = daily_paths_for_date(ph_data_root=ph_data_root, date=date)
    sprint_plan = ph_data_root / "sprints" / "current" / "plan.md"
    sprint_plan_rel = relative_markdown_link(from_dir=paths.status_file.parent, target=sprint_plan)

    weekday = date.weekday()
    is_monday = weekday == 0
    is_friday = weekday == 4

    template = f"""---
title: Daily Status - {date.strftime("%Y-%m-%d")}
type: status-daily
date: {date.strftime("%Y-%m-%d")}
sprint: {sprint_id}
tags: [status, daily]
links: [{sprint_plan_rel}]
---

# Daily Status - {date.strftime("%A, %B %d, %Y")}

## Sprint: {sprint_id}
**Weekday**: {date.strftime("%A")} (daily status is date-based; sprint planning may be bounded)
"""

    if is_monday:
        template += "\n## Weekend Summary\n"
        template += "- [ ] Review any weekend commits/PRs\n"
        template += "- [ ] Check monitoring/alerts from weekend\n\n"

    template += "\n## Progress\n"
    if tasks["doing"]:
        for task in tasks["doing"]:
            template += f"- [ ] {task['id']}: {task['title']} - UPDATE PROGRESS\n"
    if tasks["review"]:
        for task in tasks["review"]:
            template += f"- [ ] {task['id']}: {task['title']} - IN REVIEW\n"
    if not tasks["doing"] and not tasks["review"]:
        template += "- [ ] No tasks currently in progress\n"

    template += "\n## Completed Today\n"
    template += "- [ ] (Update with completed tasks)\n"

    template += "\n## Blockers\n"
    if tasks["blocked"]:
        for task in tasks["blocked"]:
            reason = task.get("blocked_reason", "Reason not specified")
            template += f"- {task['id']}: {reason}\n"
    else:
        template += "- None\n"

    template += "\n## Backlog Impact\n"

    backlog_index = ph_data_root / "backlog" / "index.json"
    if backlog_index.exists():
        try:
            backlog_data = json.loads(backlog_index.read_text(encoding="utf-8"))
        except Exception:
            backlog_data = {}
        p0_count = len([i for i in backlog_data.get("items", []) if i.get("severity") == "P0"])
        p1_count = len([i for i in backlog_data.get("items", []) if i.get("severity") == "P1"])

        if p0_count > 0:
            template += f"- ⚠️  **P0 Issues**: {p0_count} critical issues require immediate attention\n"
        if p1_count > 0:
            template += f"- P1 Issues: {p1_count} high priority for next sprint\n"
        if p0_count == 0 and p1_count == 0:
            template += "- No P0/P1 issues\n"
    else:
        template += "- No backlog items tracked\n"

    template += "- New issues discovered: (Update if any)\n"

    template += "\n## Decisions\n"
    template += "- (Document any technical decisions made today)\n"

    template += "\n## Next Focus\n"
    if tasks["todo"]:
        for task in tasks["todo"][:3]:
            template += f"- {task['id']}: {task['title']}\n"
    else:
        template += "- Continue current work\n"

    total_points = sum(int(t.get("story_points", 0) or 0) for tasks_list in tasks.values() for t in tasks_list)
    done_points = sum(int(t.get("story_points", 0) or 0) for t in tasks["done"])
    in_progress_points = sum(int(t.get("story_points", 0) or 0) for t in tasks["doing"])

    velocity_pct = int(done_points * 100 / total_points) if total_points else 0
    template += f"""
## Sprint Telemetry
- Total Points: {total_points}
- Completed: {done_points}
- In Progress: {in_progress_points}
- Velocity: {done_points}/{total_points} ({velocity_pct}%)
"""

    if is_friday:
        template += "\n## Week Summary\n"
        template += "- Sprint progress: ON TRACK / AT RISK / BEHIND\n"
        template += "- Key achievements: \n"
        template += "- Carry-over items: \n"

    return template


def create_daily_status(*, ph_root: Path, ph_data_root: Path, force: bool, env: dict[str, str]) -> Path | None:
    day = clock_today(env=env)

    if not force and not should_generate_daily(ph_root=ph_root, env=env):
        print(f"Skipping daily status for {day.strftime('%A')} (weekend)")
        return None

    paths = daily_paths_for_date(ph_data_root=ph_data_root, date=day)
    paths.daily_dir.mkdir(parents=True, exist_ok=True)

    if paths.status_file.exists() and not force:
        print(f"Daily status already exists: {paths.status_file}")
        return None

    template = generate_daily_template(ph_root=ph_root, ph_data_root=ph_data_root, date=day, env=env)
    paths.status_file.write_text(template, encoding="utf-8")
    print(f"Created daily status: {paths.status_file}")
    return paths.status_file


def _iter_daily_files(*, ph_data_root: Path) -> list[Path]:
    daily_dir = ph_data_root / "status" / "daily"
    if not daily_dir.exists():
        return []

    out: list[Path] = []
    for year_dir in daily_dir.iterdir():
        if not (year_dir.is_dir() and year_dir.name.isdigit()):
            continue
        for month_dir in year_dir.iterdir():
            if not (month_dir.is_dir() and month_dir.name.isdigit()):
                continue
            out.extend(sorted(month_dir.glob("*.md")))
    return out


def _date_from_daily_path(path: Path) -> dt.date | None:
    try:
        day = int(path.stem)
        month = int(path.parent.name)
        year = int(path.parent.parent.name)
        return dt.date(year, month, day)
    except Exception:
        return None


def get_last_daily_status(*, ph_data_root: Path) -> tuple[Path | None, dt.date | None]:
    files = _iter_daily_files(ph_data_root=ph_data_root)
    best: tuple[dt.date, Path] | None = None
    for f in files:
        d = _date_from_daily_path(f)
        if d is None:
            continue
        if best is None or d > best[0]:
            best = (d, f)
    if best is None:
        return None, None
    return best[1], best[0]


def hours_since_last_daily(*, ph_data_root: Path, env: dict[str, str]) -> float:
    _path, last_date = get_last_daily_status(ph_data_root=ph_data_root)
    if not last_date:
        return float("inf")
    last_dt = dt.datetime.combine(last_date, dt.time.min)
    delta = clock_now(env=env) - last_dt
    return delta.total_seconds() / 3600


def check_status(*, ph_root: Path, ph_data_root: Path, verbose: bool, env: dict[str, str]) -> int:
    if not should_generate_daily(ph_root=ph_root, env=env):
        if verbose:
            print("Weekend - no daily status required")
        return 0

    hours = hours_since_last_daily(ph_data_root=ph_data_root, env=env)
    if hours > 24:
        if hours == float("inf"):
            print("⚠️  No daily status found!")
        else:
            print(f"⚠️  Daily status is {int(hours)} hours old!")
        print("Run: ph daily generate")
        return 1

    if verbose:
        print(f"✅ Daily status is current ({int(hours)} hours old)")
    return 0
