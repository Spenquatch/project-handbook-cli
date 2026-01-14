from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .clock import now as clock_now
from .clock import today as clock_today


def load_sprint_config(*, ph_root: Path) -> dict[str, Any]:
    rules_path = ph_root / "process" / "checks" / "validation_rules.json"
    try:
        if rules_path.exists():
            return json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    return {
        "sprint_management": {
            "mode": "bounded",
            "health_check_thresholds": {
                "blocked_percentage_red": 30,
                "progress_percentage_red": 50,
                "progress_check_day": 3,
            },
            "sprint_duration_days": 5,
        }
    }


def use_iso_week_ids(config: dict[str, Any]) -> bool:
    return bool(config.get("sprint_management", {}).get("enforce_iso_week_ids", False))


def sprint_dir_from_id(*, ph_data_root: Path, sprint_id: str) -> Path:
    parts = sprint_id.split("-")
    year = parts[1] if len(parts) > 1 else dt.date.today().strftime("%Y")
    return ph_data_root / "sprints" / year / sprint_id


def get_sprint_id(*, ph_root: Path, ph_data_root: Path, env: dict[str, str]) -> str:
    config = load_sprint_config(ph_root=ph_root)
    now = clock_now(env=env)
    if use_iso_week_ids(config):
        iso_date = now.date()
        week_num = iso_date.isocalendar()[1]
        year = iso_date.year
        return f"SPRINT-{year}-W{week_num:02d}"

    base = f"SPRINT-{now:%Y-%m-%d}"
    year_dir = ph_data_root / "sprints" / f"{now.year:04d}"
    archive_year_dir = ph_data_root / "sprints" / "archive" / f"{now.year:04d}"
    year_dir.mkdir(parents=True, exist_ok=True)
    archive_year_dir.mkdir(parents=True, exist_ok=True)

    candidate = base
    if (year_dir / candidate).exists() or (archive_year_dir / candidate).exists():
        candidate = f"{base}-{now:%H}"
        suffix = 0
        while (year_dir / candidate).exists() or (archive_year_dir / candidate).exists():
            suffix += 1
            candidate = f"{base}-{now:%H}{suffix:02d}"
    return candidate


def get_sprint_dates(sprint_id: str) -> tuple[dt.date, dt.date]:
    parts = sprint_id.split("-")
    if len(parts) >= 3 and parts[2].startswith("W"):
        year = int(parts[1])
        week = int(parts[2][1:])
        jan1 = dt.date(year, 1, 1)
        week1_monday = jan1 - dt.timedelta(days=jan1.weekday())
        sprint_start = week1_monday + dt.timedelta(weeks=week - 1)
        sprint_end = sprint_start + dt.timedelta(days=4)
        return sprint_start, sprint_end

    if len(parts) < 4:
        raise ValueError(f"Unrecognized sprint id: {sprint_id}")
    date_str = "-".join(parts[1:4])
    sprint_start = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    sprint_end = sprint_start + dt.timedelta(days=4)
    return sprint_start, sprint_end


def update_current_symlink(*, ph_data_root: Path, sprint_id: str) -> None:
    sprints_dir = ph_data_root / "sprints"
    current_link = sprints_dir / "current"
    sprint_path = sprint_dir_from_id(ph_data_root=ph_data_root, sprint_id=sprint_id)

    if current_link.exists() or current_link.is_symlink():
        try:
            current_link.unlink()
        except FileNotFoundError:
            pass

    if sprint_path.exists():
        current_link.symlink_to(sprint_path.relative_to(sprints_dir))


def create_sprint_plan_template(
    *, ph_root: Path, ph_data_root: Path, scope: str, sprint_id: str, env: dict[str, str]
) -> str:
    config = load_sprint_config(ph_root=ph_root)
    mode = (config.get("sprint_management", {}).get("mode") or "timeboxed").strip().lower()
    if mode not in {"bounded", "timeboxed"}:
        mode = "timeboxed"

    task_create_cmd = "ph --scope system task create" if scope == "system" else "ph task create"

    template = f"""---
title: Sprint Plan - {sprint_id}
type: sprint-plan
date: {clock_today(env=env).strftime("%Y-%m-%d")}
sprint: {sprint_id}
mode: {mode}
tags: [sprint, planning]
"""

    # System scope MUST NOT include release context.
    template += "release: null\n"
    if mode == "timeboxed":
        start_date, end_date = get_sprint_dates(sprint_id)
        template += f"start: {start_date.strftime('%Y-%m-%d')}\n"
        template += f"end: {end_date.strftime('%Y-%m-%d')}\n"
    template += "---\n\n"
    template += f"# Sprint Plan: {sprint_id}\n\n"

    if mode == "bounded":
        bounded_lines = [
            "## Sprint Model",
            (
                "This sprint uses **bounded planning** (ADR-0013): sprint scope is defined by "
                "*work boundaries* and *parallel lanes*, not a fixed calendar window or points cap."
            ),
            "",
            "## Sprint Goal",
            "1. [ ] Primary outcome (clear deliverable + validation gate)",
            "2. [ ] Secondary outcome",
            "3. [ ] Integration outcome (if multiple lanes)",
            "",
            "## Boundaries (Lanes)",
            "Define lanes to maximize parallel execution and minimize cross-lane coupling.",
            "",
            "| Lane | Scope | Success Output |",
            "|------|-------|----------------|",
            "| `service/<name>` | | |",
            "| `infra/<name>` | | |",
            "| `handbook/<area>` | | |",
            "| `integration/<scope>` | | |",
            "",
            "## Integration Tasks",
            "- List explicit cross-lane integration tasks and their dependencies.",
            "",
            "## Task Creation Guide",
            "```bash",
            (
                f'{task_create_cmd} --title "Task Name" --feature feature-name --decision ADR-XXX '
                '--points 3 --lane "handbook/automation"'
            ),
            "```",
            "",
            "## Telemetry (Points)",
            "- Story points are tracked for throughput/velocity trends, not for limiting sprint scope.",
            "",
            "## Dependencies & Risks",
            "- External dependencies",
            "- Cross-lane dependencies (integration risk)",
            "- Unknowns / validation gaps",
            "",
            "## Success Criteria",
            "- [ ] Lanes are explicit and independently executable",
            "- [ ] Integration tasks are explicit and dependency-linked",
            "- [ ] All committed tasks completed (points recorded for telemetry)",
        ]
        template += "\n".join(bounded_lines) + "\n"
        return template

    start_date, end_date = get_sprint_dates(sprint_id)
    start_label = start_date.strftime("%A, %B %d, %Y")
    end_label = end_date.strftime("%A, %B %d, %Y")
    template += f"""## Sprint Duration
- Start: {start_label}
- End: {end_label}

## Sprint Goals
1. [ ] Primary goal
2. [ ] Secondary goal
3. [ ] Stretch goal

## Task Creation Guide
```bash
{task_create_cmd} --title \"Task Name\" --feature feature-name --decision ADR-XXX --points 5
```

## Capacity Planning (Optional)
- Use capacity planning only if it adds signal for your team.

## Dependencies & Risks
- External dependencies
"""
    return template
