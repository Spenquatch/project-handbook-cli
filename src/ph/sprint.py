from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from .clock import now as clock_now
from .clock import today as clock_today
from .release import get_current_release, load_release_features, parse_plan_front_matter


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

def sprint_id_scheme(config: dict[str, Any]) -> str:
    """
    Return sprint id scheme:
    - "date" (default): SPRINT-YYYY-MM-DD[-HH]
    - "iso-week": SPRINT-YYYY-W##
    - "sequence": SPRINT-SEQ-0001
    """
    sprint_management = config.get("sprint_management", {}) or {}
    raw = str(sprint_management.get("id_scheme") or "").strip().lower()
    if raw in {"seq", "sequence", "counter"}:
        return "sequence"
    if raw in {"iso-week", "iso_week", "week"}:
        return "iso-week"
    if use_iso_week_ids(config):
        return "iso-week"
    return "date"


def sprint_dir_from_id(*, ph_data_root: Path, sprint_id: str) -> Path:
    parts = sprint_id.split("-")
    year = parts[1] if len(parts) > 1 else dt.date.today().strftime("%Y")
    return ph_data_root / "sprints" / year / sprint_id


def get_sprint_id(*, ph_root: Path, ph_data_root: Path, env: dict[str, str]) -> str:
    config = load_sprint_config(ph_root=ph_root)
    now = clock_now(env=env)
    scheme = sprint_id_scheme(config)
    if scheme == "sequence":
        seq_root = ph_data_root / "sprints" / "SEQ"
        seq_root.mkdir(parents=True, exist_ok=True)
        archive_root = ph_data_root / "sprints" / "archive" / "SEQ"
        archive_root.mkdir(parents=True, exist_ok=True)

        pattern = re.compile(r"^SPRINT-SEQ-(\d{4,})$")
        max_seen = 0
        for base in (seq_root, archive_root):
            for entry in base.iterdir():
                if not entry.is_dir():
                    continue
                match = pattern.match(entry.name)
                if not match:
                    continue
                try:
                    max_seen = max(max_seen, int(match.group(1)))
                except Exception:
                    continue

        next_value = max_seen + 1 if max_seen else 1
        candidate = f"SPRINT-SEQ-{next_value:04d}"
        while (seq_root / candidate).exists() or (archive_root / candidate).exists():
            next_value += 1
            candidate = f"SPRINT-SEQ-{next_value:04d}"
        return candidate

    if scheme == "iso-week":
        iso_date = now.date()
        week_num = iso_date.isocalendar()[1]
        year = iso_date.year
        return f"SPRINT-{year}-W{week_num:02d}"

    base = f"SPRINT-{now:%Y-%m-%d}"
    year_dir = ph_data_root / "sprints" / f"{now.year:04d}"
    archive_year_dir = ph_data_root / "sprints" / "archive" / f"{now.year:04d}"
    year_dir.mkdir(parents=True, exist_ok=True)

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

def _get_release_timeline_info(*, ph_root: Path, version: str) -> dict[str, object]:
    plan_path = ph_root / "releases" / version / "plan.md"
    return parse_plan_front_matter(plan_path=plan_path)

def _get_current_release_context(*, ph_root: Path) -> dict[str, object]:
    version = get_current_release(ph_root=ph_root)
    if not version:
        return {}
    features = load_release_features(ph_root=ph_root, version=version)
    timeline = _get_release_timeline_info(ph_root=ph_root, version=version)
    return {"version": version, "features": features, "timeline": timeline}


def create_sprint_plan_template(
    *, ph_root: Path, ph_data_root: Path, scope: str, sprint_id: str, env: dict[str, str]
) -> str:
    config = load_sprint_config(ph_root=ph_root)
    mode = (config.get("sprint_management", {}).get("mode") or "timeboxed").strip().lower()
    if mode not in {"bounded", "timeboxed"}:
        mode = "timeboxed"

    release_context: dict[str, object] = {}
    if scope != "system":
        release_context = _get_current_release_context(ph_root=ph_root)

    template = f"""---
title: Sprint Plan - {sprint_id}
type: sprint-plan
date: {clock_today(env=env).strftime("%Y-%m-%d")}
sprint: {sprint_id}
mode: {mode}
tags: [sprint, planning]
"""

    # System scope MUST NOT include release context.
    if scope == "system":
        template += "release: null\n"
    else:
        release_version = str(release_context.get("version") or "").strip()
        template += f"release: {release_version}\n" if release_version else "release: null\n"
        if release_version:
            timeline = release_context.get("timeline") if isinstance(release_context.get("timeline"), dict) else {}
            timeline_mode = str((timeline or {}).get("timeline_mode") or "").strip().lower()
            if timeline_mode == "sprint_slots":
                slots = (timeline or {}).get("sprint_slots") or []
                assignments = (timeline or {}).get("slot_assignments") or {}
                next_slot: int | None = None
                for slot in slots:
                    try:
                        slot_int = int(slot)
                    except Exception:
                        continue
                    if slot_int not in assignments:
                        next_slot = slot_int
                        break
                if next_slot is not None:
                    template += f"release_sprint_slot: {next_slot}\n"

    if mode == "timeboxed":
        start_date, end_date = get_sprint_dates(sprint_id)
        template += f"start: {start_date.strftime('%Y-%m-%d')}\n"
        template += f"end: {end_date.strftime('%Y-%m-%d')}\n"

    template += "---\n\n"
    template += f"# Sprint Plan: {sprint_id}\n\n"

    if scope != "system" and str(release_context.get("version") or "").strip():
        version = str(release_context.get("version") or "").strip()
        template += "## Release Context\n"
        timeline = release_context.get("timeline") if isinstance(release_context.get("timeline"), dict) else {}
        sprint_index = (timeline or {}).get("current_sprint_index")
        planned_sprints = (timeline or {}).get("planned_sprints")
        end_sprint = (timeline or {}).get("end_sprint")

        template += f"**Release**: {version}\n"
        if sprint_index and planned_sprints:
            template += f"**Release sprint position**: Sprint {sprint_index} of {planned_sprints}\n"
        if end_sprint:
            template += f"**Release target**: {end_sprint}\n"
        template += "**Features in this release**:\n"
        features = release_context.get("features") if isinstance(release_context.get("features"), dict) else {}
        for feature_name, feature_data in (features or {}).items():
            feature_dict = feature_data if isinstance(feature_data, dict) else {}
            critical_note = " (Critical Path)" if feature_dict.get("critical_path") else ""
            template += f"- {feature_name}: {feature_dict.get('type', 'regular')}{critical_note}\n"
        template += "\n"

    if mode == "bounded":
        if scope == "system":
            task_create_cmd = "ph --scope system task create"
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

        project_bounded_lines = [
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
            "## Release Alignment (Explicit)",
            "If you have an active release, it is a *measurement context* — not an automatic scope cap.",
            "",
            "| Bucket | Intention | Notes |",
            "|--------|-----------|-------|",
            "| Release-critical | Work that must move critical-path features | |",
            "| Release-support | Work that enables the release but lives outside assigned features | |",
            "| Non-release | Necessary work that does not serve the active release | |",
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
                "make task-create title=\"Task Name\" feature=feature-name decision=ADR-XXX points=3 "
                "lane=\"handbook/automation\" release=current"
            ),
            (
                "make task-create title=\"Gate: <name>\" feature=feature-name decision=ADR-XXX points=3 "
                "lane=\"integration/<scope>\" release=current gate=true"
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
        template += "\n".join(project_bounded_lines) + "\n"
        return template

    start_date, end_date = get_sprint_dates(sprint_id)
    start_label = start_date.strftime("%A, %B %d, %Y")
    end_label = end_date.strftime("%A, %B %d, %Y")
    timeboxed_lines: list[str] = [
        "## Sprint Duration",
        f"- Start: {start_label}",
        f"- End: {end_label}",
        "",
        "## Sprint Goals",
    ]
    if scope != "system" and str(release_context.get("version") or "").strip():
        timeboxed_lines.append("*(Align with release features above)*")
    timeboxed_lines.extend(
        [
            "1. [ ] Primary goal",
            "2. [ ] Secondary goal",
            "3. [ ] Stretch goal",
            "",
            "## Release Alignment (Optional)",
            "| Bucket | Intention | Notes |",
            "|--------|-----------|-------|",
            "| Release-critical | | |",
            "| Release-support | | |",
            "| Non-release | | |",
            "",
            "## Task Creation Guide",
            "```bash",
            (
                "make task-create title=\"Task Name\" feature=feature-name decision=ADR-XXX points=5 "
                "release=current"
            ),
            (
                "make task-create title=\"Gate: <name>\" feature=feature-name decision=ADR-XXX points=3 "
                "release=current gate=true"
            ),
            "```",
            "",
            "## Capacity Planning (Optional)",
            "- Use capacity planning only if it adds signal for your team.",
            "",
            "## Dependencies & Risks",
            "- External dependencies",
            "- Cross-team dependencies",
            "- Technical risks",
            "",
            "## Success Criteria",
            "- [ ] All committed tasks completed (story points delivered)",
            "- [ ] Sprint health maintained",
        ]
    )
    template += "\n".join(timeboxed_lines) + "\n"

    if scope == "system":
        template = template.replace("make task-create", "ph --scope system task create")
    return template
