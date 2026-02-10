from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from .clock import today as clock_today
from .context import Context
from .feature_status_updater import calculate_feature_metrics, collect_all_sprint_tasks

_SYSTEM_SCOPE_REMEDIATION = "Releases are project-scope only. Use: ph --scope project release ..."

def _plan_hint_lines() -> tuple[str, ...]:
    return (
        "Release plan scaffold created under .project-handbook/releases/<version>/plan.md",
        "  - Assign features via 'ph release add-feature --release <version> --feature <name>'",
        "  - Activate when ready via 'ph release activate --release <version>'",
        "  - Confirm sprint alignment via 'ph release status' (requires an active release)",
        "  - Run 'ph validate --quick' before sharing externally",
    )

_ADD_FEATURE_SUCCESS_PREFIX = "✅ Added"


def parse_version(version: str) -> tuple[int, int, int]:
    if not version.startswith("v"):
        version = f"v{version}"

    parts = version[1:].split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major, minor, patch
    except Exception:
        return 0, 0, 0


def format_version(major: int, minor: int, patch: int) -> str:
    return f"v{major}.{minor}.{patch}"


def bump_version(version: str, *, bump: str = "patch") -> str:
    major, minor, patch = parse_version(version)
    if bump == "major":
        return format_version(major + 1, 0, 0)
    if bump == "minor":
        return format_version(major, minor + 1, 0)
    return format_version(major, minor, patch + 1)


def list_release_versions(*, ph_root: Path) -> list[str]:
    releases_dir = ph_root / "releases"
    if not releases_dir.exists():
        return []
    released: list[str] = []
    for path in releases_dir.iterdir():
        if path.is_dir() and path.name.startswith("v"):
            released.append(path.name)
    released.sort(key=parse_version)
    return released


def get_current_release(*, ph_root: Path) -> str | None:
    releases_dir = ph_root / "releases"
    current_link = releases_dir / "current"

    if current_link.is_symlink():
        target = current_link.readlink()
        target_path = releases_dir / target
        if target_path.exists():
            return target.name
        current_link.unlink(missing_ok=True)
    return None


def set_current_release(*, ph_root: Path, version: str) -> bool:
    if not version.startswith("v"):
        version = f"v{version}"
    release_dir = ph_root / "releases" / version
    if not release_dir.exists():
        return False

    releases_dir = ph_root / "releases"
    current_link = releases_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink(missing_ok=True)
    try:
        current_link.symlink_to(version)
    except OSError:
        return False
    return True


def clear_current_release(*, ph_root: Path) -> None:
    current_link = ph_root / "releases" / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink(missing_ok=True)


def calculate_sprint_range(*, start_sprint: str, sprint_count: int, explicit: list[str] | None = None) -> list[str]:
    if explicit:
        return list(explicit)

    parts = start_sprint.split("-")
    sprint_ids: list[str] = []

    if len(parts) == 3 and parts[1] == "SEQ" and parts[2].isdigit():
        base = int(parts[2])
        width = len(parts[2])
        for i in range(sprint_count):
            if i == 0:
                sprint_ids.append(start_sprint)
            else:
                sprint_ids.append(f"SPRINT-SEQ-{base + i:0{width}d}")
        return sprint_ids

    if len(parts) >= 3 and parts[2].startswith("W"):
        year = int(parts[1])
        week = int(parts[2][1:])
        for i in range(sprint_count):
            current_week = week + i
            if i == 0:
                sprint_ids.append(start_sprint)
            else:
                sprint_ids.append(f"SPRINT-{year}-W{current_week:02d}")
        return sprint_ids

    if len(parts) < 4:
        raise ValueError(f"Unrecognized sprint id format: {start_sprint}")

    date_str = "-".join(parts[1:4])
    start_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    sprint_ids.append(start_sprint)
    for i in range(1, sprint_count):
        scheduled = start_date + dt.timedelta(weeks=i)
        sprint_ids.append(f"SPRINT-{scheduled:%Y-%m-%d}")
    return sprint_ids


def _parse_sprint_ids_csv(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    return parts or None


def _resolve_current_sprint_id(*, ph_root: Path, fallback: str) -> str:
    link = ph_root / "sprints" / "current"
    if not link.exists():
        return fallback
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return fallback
    return resolved.name if resolved.exists() else fallback


def _ensure_release_files_exist(
    *,
    ph_root: Path,
    version: str,
    timeline_mode: str,
    sprint_count: int,
    start_sprint: str | None,
    sprint_ids: list[str] | None,
    env: dict[str, str],
) -> Path:
    if not version.startswith("v"):
        version = f"v{version}"

    releases_dir = ph_root / "releases"
    release_dir = releases_dir / version
    release_dir.mkdir(parents=True, exist_ok=True)

    today = clock_today(env=env).strftime("%Y-%m-%d")

    plan_path = release_dir / "plan.md"
    if not plan_path.exists():
        normalized_mode = (timeline_mode or "").strip().lower()
        if normalized_mode == "sprint_slots":
            slots = list(range(1, sprint_count + 1))
            slots_csv = ", ".join(str(slot) for slot in slots)
            plan_content = f"""---
title: Release {version} Plan
type: release-plan
version: {version}
timeline_mode: sprint_slots
planned_sprints: {sprint_count}
sprint_slots: [{slots_csv}]
status: planned
date: {today}
tags: [release, planning]
links: []
---


# Release {version}

## Release Summary
Brief description of what this release delivers.

## Release Goals
1. **Primary Goal**: Main feature or capability
2. **Secondary Goal**: Supporting features
3. **Stretch Goal**: Nice-to-have if time permits

## Release Type & Scope
- **Type**: minor (2 sprints) / standard (3 sprints) / major (4 sprints)
- **In scope (must-have)**:
  - TBD
- **Out of scope (explicitly not in this release)**:
  - TBD
- **Scope flexibility**:
  - Locked: TBD
  - Flexible: TBD

## Sprint Timeline
This release uses **sprint slots** (not calendar dates). Assign a concrete sprint to a slot by setting
`release: {version}` and `release_sprint_slot: <n>` in the sprint plan front matter.

- **Slot 1** (Sprint 1 of {sprint_count}): Sprint theme/focus
"""
            for slot in range(2, sprint_count + 1):
                plan_content += f"- **Slot {slot}** (Sprint {slot} of {sprint_count}): Sprint theme/focus\n"

            plan_content += "\n\n## Slot Plans\n"
            for slot in range(1, sprint_count + 1):
                plan_content += f"""
### Slot {slot}

#### Goal / Purpose
- TBD

#### Scope boundaries (in/out)
- In: TBD
- Out: TBD

#### Intended gate(s)
- TBD

#### Enablement
- How this slot advances the release: TBD
"""

            plan_content += f"""

## Release Gates (Burn-up)
Define a small set of explicit gates (smoke/demo/contract-lock) as **sprint tasks** and tag them to this release:
```bash
ph task create --title "Gate: <name>" --feature <feature> --decision ADR-XXX --points 3 --release {version} --gate
```

## Feature Assignments
*Use `ph release add-feature` to assign features to this release*

## Scope Control
- **Scope lock**: TBD (slot or criteria)
- **Change control**:
  - Default: new requests go to the next release
  - Exceptions: TBD (who decides, criteria, and how to document)

## Communication Plan
### Internal
- Announcement: TBD
- Progress cadence: weekly release health check
- Escalation path: TBD

### Stakeholders
- Update cadence: TBD
- Demo date(s): TBD
- Release notes owner: TBD

## Success Criteria
- [ ] All assigned features complete
- [ ] Performance benchmarks met
- [ ] Quality gates passed
- [ ] Documentation updated

## Risk Management
- Critical path: (Identify critical features)
- Dependencies: (External dependencies)
- Capacity: (Team availability considerations)

## Release Notes Draft
*Auto-generated from completed tasks and features*
"""
        else:
            if not start_sprint:
                raise ValueError("start_sprint is required when timeline_mode != sprint_slots")
            timeline = calculate_sprint_range(start_sprint=start_sprint, sprint_count=sprint_count, explicit=sprint_ids)
            end_sprint = timeline[-1]
            plan_content = f"""---
title: Release {version} Plan
type: release-plan
version: {version}
start_sprint: {start_sprint}
end_sprint: {end_sprint}
planned_sprints: {sprint_count}
sprint_ids: [{", ".join(timeline)}]
status: planned
date: {today}
tags: [release, planning]
links: []
---

# Release {version}

## Release Summary
Brief description of what this release delivers.

## Release Goals
1. **Primary Goal**: Main feature or capability
2. **Secondary Goal**: Supporting features
3. **Stretch Goal**: Nice-to-have if time permits

## Release Type & Scope
- **Type**: minor (2 sprints) / standard (3 sprints) / major (4 sprints)
- **In scope (must-have)**:
  - TBD
- **Out of scope (explicitly not in this release)**:
  - TBD
- **Scope flexibility**:
  - Locked: TBD
  - Flexible: TBD

## Sprint Timeline
"""
            for i, sprint_id in enumerate(timeline, 1):
                plan_content += f"- **{sprint_id}** (Sprint {i} of {sprint_count}): Sprint theme/focus\n"

            plan_content += """

## Feature Assignments
*Use `ph release add-feature` to assign features to this release*

## Scope Control
- **Scope lock date**: TBD
- **Change control**:
  - Default: new requests go to the next release
  - Exceptions: TBD (who decides, criteria, and how to document)

## Communication Plan
### Internal
- Announcement: TBD
- Progress cadence: weekly release health check
- Escalation path: TBD

### Stakeholders
- Update cadence: TBD
- Demo date(s): TBD
- Release notes owner: TBD

## Success Criteria
- [ ] All assigned features complete
- [ ] Performance benchmarks met
- [ ] Quality gates passed
- [ ] Documentation updated

## Risk Management
- Critical path: (Identify critical features)
- Dependencies: (External dependencies)
- Capacity: (Team availability considerations)

## Release Notes Draft
*Auto-generated from completed tasks and features*
"""

        plan_path.write_text(plan_content, encoding="utf-8")

    features_path = release_dir / "features.yaml"
    if not features_path.exists():
        normalized_mode = (timeline_mode or "").strip().lower()
        if normalized_mode == "sprint_slots":
            features_content = f"""# Feature assignments for {version}
# Auto-managed by release commands

version: {version}
timeline_mode: sprint_slots
start_sprint_slot: 1
end_sprint_slot: {sprint_count}
planned_sprints: {sprint_count}


features:
  # Features will be added with: ph release add-feature
  # Example:
  # auth-system:
  #   type: epic
  #   priority: P0
  #   status: planned
  #   completion: 0
  #   critical_path: true
"""
        else:
            if not start_sprint:
                raise ValueError("start_sprint is required when timeline_mode != sprint_slots")
            timeline = calculate_sprint_range(start_sprint=start_sprint, sprint_count=sprint_count, explicit=sprint_ids)
            end_sprint = timeline[-1]
            features_content = f"""# Feature assignments for {version}
# Auto-managed by release commands

version: {version}
start_sprint: {start_sprint}
end_sprint: {end_sprint}
planned_sprints: {sprint_count}

features:
  # Features will be added with: ph release add-feature
  # Example:
  # auth-system:
  #   type: epic
  #   priority: P0
  #   sprints: [SPRINT-2025-11-03, SPRINT-2025-11-10, SPRINT-2025-11-17]
  #   status: in_progress
  #   critical_path: true
"""
        features_path.write_text(features_content, encoding="utf-8")

    progress_path = release_dir / "progress.md"
    if not progress_path.exists():
        normalized_mode = (timeline_mode or "").strip().lower()
        progress_content = f"""---
title: Release {version} Progress
type: release-progress
version: {version}
date: {today}
tags: [release, progress]
links: []
---

# Release {version} Progress

*This file is auto-generated. Do not edit manually.*

## Sprint Progress
"""

        if normalized_mode == "sprint_slots":
            for slot in range(1, sprint_count + 1):
                progress_content += f"- **Slot {slot}**: ⭕ Planned\n"
        else:
            if not start_sprint:
                raise ValueError("start_sprint is required when timeline_mode != sprint_slots")
            timeline = calculate_sprint_range(start_sprint=start_sprint, sprint_count=sprint_count, explicit=sprint_ids)
            current_active = _resolve_current_sprint_id(ph_root=ph_root, fallback=start_sprint)
            for i, sprint_id in enumerate(timeline, 1):
                if i == 1:
                    status = "✅ Complete"
                elif sprint_id == current_active:
                    status = "🔄 In Progress"
                else:
                    status = "⭕ Planned"
                progress_content += f"- **{sprint_id}**: {status}\n"

        progress_content += """

## Feature Progress
*Updated automatically from feature status files*

## Task Completion
*Updated automatically from sprint tasks*

## Release Health
*Calculated from sprint velocity and feature completion*
"""
        progress_path.write_text(progress_content, encoding="utf-8")

    return release_dir


def run_release_plan(
    *,
    ctx: Context,
    version: str | None,
    bump: str,
    sprints: int,
    start_sprint: str | None,
    sprint_ids: str | None,
    activate: bool,
    env: dict[str, str],
) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    raw_version = (version or "next").strip()
    raw_bump = (bump or "patch").strip()

    user_provided_start_sprint = start_sprint is not None
    explicit_sprint_ids = _parse_sprint_ids_csv(sprint_ids)

    sprint_count = int(sprints) if sprints else 3
    if explicit_sprint_ids:
        sprint_count = len(explicit_sprint_ids)

    timeline_mode = "sprint_slots"
    if user_provided_start_sprint or explicit_sprint_ids:
        timeline_mode = "sprint_ids"
        if not start_sprint and explicit_sprint_ids:
            start_sprint = explicit_sprint_ids[0]
        if start_sprint is None:
            start_sprint = f"SPRINT-{clock_today(env=env):%Y-%m-%d}"

    if raw_version in {"next", "auto"}:
        current = get_current_release(ph_root=ctx.ph_data_root)
        available = list_release_versions(ph_root=ctx.ph_data_root)
        base = current or (available[-1] if available else "v0.1.0")
        raw_version = bump_version(base, bump=raw_bump)

    if not raw_version.startswith("v"):
        raw_version = f"v{raw_version}"

    release_dir = _ensure_release_files_exist(
        ph_root=ctx.ph_data_root,
        version=raw_version,
        timeline_mode=timeline_mode,
        sprint_count=sprint_count,
        start_sprint=start_sprint,
        sprint_ids=explicit_sprint_ids,
        env=env,
    )

    if activate:
        ok = set_current_release(ph_root=ctx.ph_data_root, version=raw_version)
        if not ok:
            print(f"⚠️  Failed to activate current release (symlink): releases/current → {raw_version}")

    resolved_release_dir = release_dir.resolve()
    resolved_plan_path = (resolved_release_dir / "plan.md").resolve()
    print(f"✅ Created release plan: {raw_version}")
    print(f"📁 Location: {resolved_release_dir}")
    print(f"📅 Timeline: {sprint_count} sprint slot(s) (decoupled from calendar dates)")
    print("📝 Next steps:")
    print(f"   1. Edit {resolved_plan_path} to define release goals")
    print(f"   2. Add features: ph release add-feature --release {raw_version} --feature feature-name")
    print(f"   3. Activate when ready: ph release activate --release {raw_version}")
    print("   4. Review timeline and adjust if needed")
    for line in _plan_hint_lines():
        print(line)
    return 0


def run_release_activate(*, ctx: Context, release: str, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = (release or "").strip()
    if not version:
        print("❌ Usage: ph release activate --release vX.Y.Z")
        return 2
    if not version.startswith("v"):
        version = f"v{version}"

    if not set_current_release(ph_root=ctx.ph_data_root, version=version):
        print(f"❌ Release {version} not found (expected: releases/{version}/)")
        return 1

    print(f"⭐ Current release set to: {version}")
    return run_release_status(ctx=ctx, env=env)


def run_release_clear(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    clear_current_release(ph_root=ctx.ph_data_root)
    print("⭐ Cleared current release")
    return 0


def run_release_progress(*, ctx: Context, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = _read_current_release_target(ph_root=ctx.ph_data_root)
    if not version:
        print("❌ No current release found")
        print("💡 Activate one with: ph release activate --release vX.Y.Z")
        return 1

    try:
        path = write_release_progress(ph_root=ctx.ph_data_root, version=version, env=env)
    except FileNotFoundError:
        print(f"❌ Release {version} not found")
        return 1
    print(f"📝 Updated: {path}")
    return 0


def write_release_progress(*, ph_root: Path, version: str, env: dict[str, str]) -> Path:
    """
    Write `releases/<version>/progress.md` and return the path.

    This is used by both `ph release progress` (current release) and sprint-close parity,
    where legacy runs `process/automation/release_manager.py --progress <version>`.
    """
    resolved = normalize_version(version)
    if not resolved:
        raise ValueError("missing version")

    release_dir = ph_root / "releases" / resolved
    if not release_dir.exists():
        raise FileNotFoundError(resolved)

    plan_file = release_dir / "plan.md"
    features_file = release_dir / "features.yaml"
    progress_file = release_dir / "progress.md"

    timeline = get_release_timeline_info(ph_root=ph_root, version=resolved)
    features = load_release_features(ph_root=ph_root, version=resolved)
    progress = calculate_release_progress(ph_root=ph_root, version=resolved, features=features, env=env)
    current_sprint = _resolve_current_sprint_id(ph_root=ph_root, fallback="SPRINT-SEQ-0001")
    timeline_mode = str(timeline.get("timeline_mode") or "sprint_slots").strip().lower()

    def status_for_sprint_id(sprint_id: str | None) -> str:
        if not sprint_id:
            return "⭕ Planned"
        if sprint_id == current_sprint:
            return "🔄 In Progress"
        if is_sprint_archived(ph_root=ph_root, sprint_id=sprint_id):
            return "✅ Complete"
        return "⭕ Planned"

    today = clock_today(env=env).strftime("%Y-%m-%d")
    links: list[str] = []
    try:
        if plan_file.exists():
            links.append(str(plan_file.relative_to(ph_root)))
        if features_file.exists():
            links.append(str(features_file.relative_to(ph_root)))
    except Exception:
        links = []

    content = f"""---
title: Release {resolved} Progress
type: release-progress
version: {resolved}
date: {today}
tags: [release, progress]
links: [{", ".join(links)}]
---

# Release {resolved} Progress

*This file is auto-generated. Do not edit manually.*
"""

    planned_sprints = int(timeline.get("planned_sprints") or 0)
    if timeline_mode == "sprint_slots":
        slot_list_raw = timeline.get("sprint_slots") or list(range(1, planned_sprints + 1))
        if not isinstance(slot_list_raw, list):
            slot_list_raw = list(range(1, planned_sprints + 1))
        slots = [
            int(slot)
            for slot in slot_list_raw
            if isinstance(slot, int) or (isinstance(slot, str) and str(slot).isdigit())
        ]
        assignments = timeline.get("slot_assignments") or {}
        if not isinstance(assignments, dict):
            assignments = {}

        slot_alignments = _collect_release_slot_alignments(plan_path=plan_file, slots=slots)
        warnings = _release_alignment_warnings_for_active_sprint(
            ph_root=ph_root,
            version=resolved,
            timeline=timeline,
            slots=slots,
            slot_alignments=slot_alignments,
        )
        if warnings:
            content += "\n## Alignment Warnings\n"
            for w in warnings:
                content += f"- ⚠️ {w}\n"

        content += "\n## Sprint Progress\n"
        current_slot = timeline.get("current_sprint_slot") if isinstance(timeline.get("current_sprint_slot"), int) else None
        for i, slot in enumerate(slots, 1):
            sprint_id = assignments.get(slot)
            status = status_for_sprint_id(sprint_id)
            label = sprint_id or "(unassigned)"
            marker = "▶ " if current_slot == slot else ""
            goal = _slot_alignment_goal(slot_alignments.get(slot))
            content += f"- {marker}**Slot {slot}**: {status} — {label} (Sprint {i} of {len(slots)}) — Goal: {goal}\n"
    else:
        content += "\n## Sprint Progress\n"
        sprint_ids = timeline.get("sprint_ids") or []
        for i, sprint_id in enumerate(sprint_ids, 1):
            status = status_for_sprint_id(sprint_id)
            content += f"- **{sprint_id}**: {status} (Sprint {i} of {len(sprint_ids)})\n"

    content += "\n## Feature Progress\n"
    if features and progress.get("feature_completions"):
        for feature_name, feature_data in features.items():
            completion = int(progress.get("feature_completions", {}).get(feature_name, 0) or 0)
            status_emoji = "✅" if completion >= 90 else ("🔄" if completion > 0 else "⭕")
            critical = " (Critical Path)" if bool(feature_data.get("critical_path")) else ""
            content += f"- {status_emoji} {feature_name}: {completion}%{critical}\n"
    else:
        content += "*No release features tracked yet.*\n"

    tagged_tasks = collect_release_tagged_tasks(ph_root=ph_root, version=resolved)
    gates = [
        task
        for task in tagged_tasks
        if bool(task.get("release_gate") is True)
        or str(task.get("release_gate", "")).strip().lower() in {"true", "yes", "1"}
    ]
    gates_done = len([task for task in gates if str(task.get("status", "")).strip().lower() == "done"])

    content += "\n## Gate Burn-up\n"
    if gates:
        content += f"- Gates: {gates_done}/{len(gates)} complete\n"
        for gate in sorted(gates, key=lambda task: (str(task.get("status", "")), str(task.get("id", ""))))[:8]:
            status = str(gate.get("status", "todo")).strip().lower()
            status_emoji = {"todo": "⭕", "doing": "🔄", "review": "👀", "done": "✅", "blocked": "🚫"}.get(
                status, "❓"
            )
            content += f"- {status_emoji} {gate.get('id')}: {gate.get('title')} ({gate.get('sprint')})\n"
        remaining = len(gates) - 8
        if remaining > 0:
            content += f"- …and {remaining} more\n"
    else:
        content += "*No release gates tracked yet.*\n"

    content += "\n## Release Health\n"
    readiness = calculate_release_readiness(progress=progress) if progress else "n/a"
    content += f"- Readiness: {readiness}\n"

    progress_file.write_text(content.rstrip() + "\n", encoding="utf-8")
    return progress_file


def run_release_show(*, ctx: Context, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = _read_current_release_target(ph_root=ctx.ph_data_root)
    if not version:
        print("❌ No current release found")
        print("💡 Activate one with: ph release activate --release vX.Y.Z")
        return 1

    plan_path = ctx.ph_data_root / "releases" / version / "plan.md"
    if plan_path.exists():
        print(f"📘 RELEASE PLAN: {version}")
        print("=" * 60)
        print(plan_path.read_text(encoding="utf-8").rstrip())
        print()
    else:
        print(f"⚠️  Missing release plan: {plan_path}")

    print("---")
    print()

    exit_code = run_release_status(ctx=ctx, env=env)

    progress_path = write_release_progress(ph_root=ctx.ph_data_root, version=version, env=env)
    print()
    print(f"📝 Updated: {progress_path.resolve()}")
    return exit_code


def _read_current_release_target(*, ph_root: Path) -> str | None:
    releases_dir = ph_root / "releases"
    current_link = releases_dir / "current"
    if not current_link.is_symlink():
        return None
    try:
        target = current_link.readlink()
    except OSError:
        return None
    target_name = target.name
    if not target_name.startswith("v"):
        return None
    if not (releases_dir / target).exists():
        return None
    return target_name


def parse_plan_front_matter(*, plan_path: Path) -> dict[str, object]:
    if not plan_path.exists():
        return {}
    try:
        text = plan_path.read_text(encoding="utf-8")
    except Exception:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    meta: dict[str, object] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if inner:
                meta[key] = [item.strip() for item in inner.split(",") if item.strip()]
            else:
                meta[key] = []
        else:
            meta[key] = value
    return meta


def parse_release_plan_slot_alignment(*, plan_path: Path, slot: int) -> dict[str, object]:
    """
    Extract slot-derived alignment fields from a sprint-slots release plan.

    Expected markers (I06-RLSLOT-0001):
    - Slot header: "### Slot <n>"
    - Subsections: "#### Goal / Purpose", "#### Intended gate(s)", "#### Enablement"

    Returns:
      {
        "slot_goal": str,
        "enablement": str,
        "intended_gates": list[str],  # markdown list items (e.g. "- Gate: ...")
      }
    """
    if slot <= 0:
        return {}
    if not plan_path.exists():
        return {}
    try:
        text = plan_path.read_text(encoding="utf-8")
    except Exception:
        return {}

    lines = text.splitlines()
    slot_header_re = re.compile(rf"^###\s+Slot\s+{slot}\b", re.IGNORECASE)
    next_slot_header_re = re.compile(r"^###\s+Slot\s+\d+\b", re.IGNORECASE)

    start_idx: int | None = None
    for i, raw in enumerate(lines):
        if slot_header_re.match(raw.strip()):
            start_idx = i + 1
            break
    if start_idx is None:
        return {}

    end_idx = len(lines)
    for j in range(start_idx, len(lines)):
        if next_slot_header_re.match(lines[j].strip()):
            end_idx = j
            break

    slot_lines = lines[start_idx:end_idx]
    heading_re = re.compile(r"^####\s+", re.IGNORECASE)

    def section_lines(*, section_header: re.Pattern[str]) -> list[str]:
        header_idx: int | None = None
        for i2, raw in enumerate(slot_lines):
            if section_header.match(raw.strip()):
                header_idx = i2
                break
        if header_idx is None:
            return []
        content_start = header_idx + 1
        content_end = len(slot_lines)
        for k in range(content_start, len(slot_lines)):
            if heading_re.match(slot_lines[k].strip()):
                content_end = k
                break
        return slot_lines[content_start:content_end]

    goal_lines = section_lines(section_header=re.compile(r"^####\s+Goal\s*/\s*Purpose\s*$", re.IGNORECASE))
    enablement_lines = section_lines(section_header=re.compile(r"^####\s+Enablement\s*$", re.IGNORECASE))
    intended_gate_lines = section_lines(
        section_header=re.compile(r"^####\s+Intended\s+gate\(s\)\s*$", re.IGNORECASE)
    )

    def first_meaningful_line(raw_lines: list[str]) -> str:
        for raw in raw_lines:
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith(("- ", "* ")):
                return stripped[2:].strip()
            if stripped.startswith("-") and len(stripped) > 1 and stripped[1].isspace():
                return stripped[1:].strip()
            return stripped
        return ""

    intended_gates: list[str] = []
    for raw in intended_gate_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            intended_gates.append(stripped)
            continue
        if stripped.startswith("* "):
            intended_gates.append("- " + stripped[2:].strip())
            continue
        intended_gates.append("- " + stripped)

    if not intended_gates:
        intended_gates = ["- TBD"]

    return {
        "slot_goal": first_meaningful_line(goal_lines),
        "enablement": first_meaningful_line(enablement_lines),
        "intended_gates": intended_gates,
    }


def _slot_alignment_goal(alignment: dict[str, object] | None) -> str:
    if not alignment:
        return "TBD"
    raw = alignment.get("slot_goal")
    if not isinstance(raw, str):
        return "TBD"
    value = raw.strip()
    return value or "TBD"


def _slot_alignment_enablement(alignment: dict[str, object] | None) -> str:
    if not alignment:
        return "TBD"
    raw = alignment.get("enablement")
    if not isinstance(raw, str):
        return "TBD"
    value = raw.strip()
    return value or "TBD"


def _collect_release_slot_alignments(*, plan_path: Path, slots: list[int]) -> dict[int, dict[str, object]]:
    alignments: dict[int, dict[str, object]] = {}
    for slot in slots:
        if slot <= 0:
            continue
        alignment = parse_release_plan_slot_alignment(plan_path=plan_path, slot=slot)
        alignments[slot] = alignment if alignment else {}
    return alignments


def _resolve_current_sprint_dir(*, ph_root: Path, current_sprint_id: str) -> Path | None:
    link = ph_root / "sprints" / "current"
    if link.exists():
        try:
            resolved = link.resolve()
        except Exception:
            resolved = None
        if resolved and resolved.exists() and resolved.is_dir() and resolved.name == current_sprint_id:
            return resolved

    for sprint_dir in iter_sprint_dirs(sprints_dir=ph_root / "sprints"):
        if sprint_dir.name == current_sprint_id:
            return sprint_dir
    return None


def _sprint_plan_has_release_alignment_heading(*, sprint_plan_path: Path, slot: int) -> bool:
    if slot <= 0:
        return False
    if not sprint_plan_path.exists():
        return False
    try:
        text = sprint_plan_path.read_text(encoding="utf-8")
    except Exception:
        return False
    heading_re = re.compile(rf"^##\s+Release\s+Alignment\s+\(Slot\s+{slot}\)\s*$", flags=re.MULTILINE)
    return bool(heading_re.search(text))


def _release_alignment_warnings_for_active_sprint(
    *,
    ph_root: Path,
    version: str,
    timeline: dict[str, object],
    slots: list[int],
    slot_alignments: dict[int, dict[str, object]],
) -> list[str]:
    warnings: list[str] = []

    current_sprint_id = str(timeline.get("current_sprint") or "").strip()
    if not current_sprint_id:
        return warnings

    current_sprint_dir = _resolve_current_sprint_dir(ph_root=ph_root, current_sprint_id=current_sprint_id)
    current_plan_path = (current_sprint_dir / "plan.md") if current_sprint_dir else None
    meta = parse_sprint_plan_front_matter(plan_path=current_plan_path) if current_plan_path else {}

    raw_release = meta.get("release")
    release = raw_release.strip() if isinstance(raw_release, str) else ""
    slot_meta = parse_int(meta.get("release_sprint_slot"))

    assignments = timeline.get("slot_assignments") if isinstance(timeline.get("slot_assignments"), dict) else {}
    current_slot = timeline.get("current_sprint_slot") if isinstance(timeline.get("current_sprint_slot"), int) else None
    slot_to_check = current_slot or slot_meta

    if not release or release.lower() in {"null", "none"}:
        warnings.append(
            f"Current sprint `{current_sprint_id}` is missing `release: {version}` in its front matter."
        )
    else:
        normalized_release = normalize_version(release)
        if release.strip().lower() == "current":
            warnings.append(
                f"Current sprint `{current_sprint_id}` uses `release: current`; use `release: {version}` for slot matching."
            )
        elif normalized_release != normalize_version(version):
            warnings.append(
                f"Current sprint `{current_sprint_id}` is aligned to `{normalized_release}`, not `{version}`."
            )

    if slot_meta is None:
        warnings.append(f"Current sprint `{current_sprint_id}` is missing `release_sprint_slot: <n>` in its front matter.")
    else:
        if slot_meta not in slots:
            warnings.append(
                f"Current sprint `{current_sprint_id}` has `release_sprint_slot: {slot_meta}`, but release plan slots are {slots}."
            )
        assigned = assignments.get(slot_meta) if isinstance(assignments, dict) else None
        if assigned and str(assigned) != current_sprint_id:
            warnings.append(
                f"Slot {slot_meta} is assigned to `{assigned}`, but current sprint is `{current_sprint_id}`."
            )
        if current_slot is not None and current_slot != slot_meta:
            warnings.append(
                f"Current sprint `{current_sprint_id}` front matter says slot {slot_meta}, but computed current slot is {current_slot}."
            )
        if current_plan_path and not _sprint_plan_has_release_alignment_heading(sprint_plan_path=current_plan_path, slot=slot_meta):
            warnings.append(
                f"Current sprint plan is missing required heading: `## Release Alignment (Slot {slot_meta})`."
            )

    if slot_to_check is not None:
        alignment = slot_alignments.get(int(slot_to_check), {})
        if not alignment:
            warnings.append(
                f"Release plan is missing required slot markers for Slot {slot_to_check} (expected `### Slot {slot_to_check}` + subsections)."
            )
        else:
            if _slot_alignment_goal(alignment) == "TBD":
                warnings.append(f"Release plan Slot {slot_to_check} is missing a `#### Goal / Purpose` value.")
            if _slot_alignment_enablement(alignment) == "TBD":
                warnings.append(f"Release plan Slot {slot_to_check} is missing a `#### Enablement` value.")

    duplicates = timeline.get("slot_duplicates") if isinstance(timeline.get("slot_duplicates"), dict) else {}
    if duplicates:
        for dup_slot, sprint_ids in sorted(duplicates.items(), key=lambda t: t[0]):
            if not isinstance(dup_slot, int):
                continue
            if not isinstance(sprint_ids, list):
                continue
            warnings.append(f"Slot {dup_slot} has multiple sprint assignments: {', '.join(str(s) for s in sprint_ids)}.")

    return warnings


def parse_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.isdigit():
            try:
                return int(raw)
            except Exception:
                return None
    return None


def parse_slot_list(value: object, fallback_count: int) -> list[int]:
    """Return a stable 1-based list of sprint slots for a release timeline."""
    if isinstance(value, list) and value:
        slots: list[int] = []
        for item in value:
            parsed = parse_int(item)
            if parsed is not None:
                slots.append(parsed)
        if slots:
            return slots
    count = max(0, int(fallback_count or 0))
    return list(range(1, count + 1))


def parse_sprint_plan_front_matter(*, plan_path: Path) -> dict[str, object]:
    return parse_plan_front_matter(plan_path=plan_path)


def sprint_plan_release_slot(*, sprint_dir: Path) -> int | None:
    meta = parse_sprint_plan_front_matter(plan_path=sprint_dir / "plan.md")
    return parse_int(meta.get("release_sprint_slot"))


def normalize_version(version: str) -> str:
    if not version:
        return version
    return version if version.startswith("v") else f"v{version}"


def sprint_plan_release_version(*, sprint_dir: Path) -> str | None:
    meta = parse_sprint_plan_front_matter(plan_path=sprint_dir / "plan.md")
    raw = meta.get("release")
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value or value.lower() in {"null", "none"}:
        return None
    return normalize_version(value)


def iter_sprint_dirs(*, sprints_dir: Path) -> list[Path]:
    dirs: list[Path] = []
    if not sprints_dir.exists():
        return dirs

    for year_dir in sprints_dir.iterdir():
        if not year_dir.is_dir() or year_dir.name == "current":
            continue

        if year_dir.name == "archive":
            for archived_year_dir in year_dir.iterdir():
                if not archived_year_dir.is_dir():
                    continue
                for sprint_dir in archived_year_dir.iterdir():
                    if sprint_dir.is_dir() and sprint_dir.name.startswith("SPRINT-"):
                        dirs.append(sprint_dir)
            continue

        for sprint_dir in year_dir.iterdir():
            if sprint_dir.is_dir() and sprint_dir.name.startswith("SPRINT-"):
                dirs.append(sprint_dir)

    dirs.sort(key=lambda p: p.name)
    return dirs


def is_sprint_archived(*, ph_root: Path, sprint_id: str) -> bool:
    archive_dir = ph_root / "sprints" / "archive"
    if not archive_dir.exists():
        return False
    for path in archive_dir.rglob(sprint_id):
        if path.is_dir() and path.name == sprint_id:
            return True
    return False


def parse_task_yaml(*, task_yaml: Path) -> dict[str, Any]:
    try:
        content = task_yaml.read_text(encoding="utf-8")
    except Exception:
        return {}

    data: dict[str, Any] = {}
    current_key: str | None = None
    collecting_list = False
    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if collecting_list and current_key and line.strip().startswith("-"):
            data.setdefault(current_key, []).append(line.strip()[1:].strip())
            continue
        collecting_list = False
        if ":" not in line or line.strip().startswith("-"):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
            collecting_list = True
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                data[key] = []
            else:
                items = [item.strip().strip("\"'") for item in inner.split(",")]
                data[key] = [item for item in items if item]
            continue
        if value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
            continue
        if value.isdigit():
            data[key] = int(value)
            continue
        data[key] = value
    return data


def task_matches_release(*, task: dict[str, Any], version: str) -> bool:
    version = normalize_version(version)

    val = task.get("release")
    if isinstance(val, str):
        raw = val.strip()
        if raw.lower() in {"", "null", "none"}:
            return False
        if raw.lower() == "current":
            return True
        return normalize_version(raw) == version
    if isinstance(val, list):
        for item in val:
            if not isinstance(item, str):
                continue
            raw = item.strip()
            if not raw or raw.lower() in {"null", "none"}:
                continue
            if raw.lower() == "current":
                return True
            if normalize_version(raw) == version:
                return True
    return False


def collect_release_tagged_tasks(*, ph_root: Path, version: str) -> list[dict[str, Any]]:
    version = normalize_version(version)
    tagged: list[dict[str, Any]] = []

    for sprint_dir in iter_sprint_dirs(sprints_dir=ph_root / "sprints"):
        tasks_dir = sprint_dir / "tasks"
        if not tasks_dir.exists():
            continue

        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue
            task_yaml = task_dir / "task.yaml"
            if not task_yaml.exists():
                continue

            task = parse_task_yaml(task_yaml=task_yaml)
            task.setdefault("id", task_dir.name.split("-", 1)[0])
            task.setdefault("title", task_dir.name)
            task.setdefault("feature", "unknown")
            task["sprint"] = sprint_dir.name
            task["directory"] = task_dir.name

            if task_matches_release(task=task, version=version):
                tagged.append(task)

    def sort_key(t: dict[str, Any]) -> tuple[str, str]:
        return (str(t.get("sprint", "")), str(t.get("id", "")))

    tagged.sort(key=sort_key)
    return tagged


def summarize_tagged_tasks(*, tasks: list[dict[str, Any]], sprint_timeline: list[str] | None = None) -> dict[str, Any]:
    sprint_set = set(sprint_timeline or [])
    points_total = 0
    points_done = 0
    by_status: dict[str, int] = {"todo": 0, "doing": 0, "review": 0, "done": 0, "blocked": 0, "other": 0}
    features: set[str] = set()
    in_timeline = 0
    out_of_timeline = 0

    gates_total = 0
    gates_done = 0
    gates_in_timeline = 0
    gates_done_in_timeline = 0

    for task in tasks:
        status = str(task.get("status", "todo")).strip().lower()
        if status not in by_status:
            by_status["other"] += 1
        else:
            by_status[status] += 1

        try:
            points = int(task.get("story_points", 0) or 0)
        except Exception:
            points = 0
        points_total += points
        if status in {"done", "completed"}:
            points_done += points

        feature = str(task.get("feature", "unknown")).strip()
        if feature:
            features.add(feature)

        sprint = str(task.get("sprint", "")).strip()
        is_in_timeline = bool(sprint and sprint_set and sprint in sprint_set)
        if sprint_set:
            if is_in_timeline:
                in_timeline += 1
            else:
                out_of_timeline += 1

        is_gate = bool(task.get("release_gate") is True) or str(task.get("release_gate", "")).strip().lower() in {
            "true",
            "yes",
            "1",
        }
        if is_gate:
            gates_total += 1
            if status in {"done", "completed"}:
                gates_done += 1
            if is_in_timeline:
                gates_in_timeline += 1
                if status in {"done", "completed"}:
                    gates_done_in_timeline += 1

    completion = int(points_done * 100 / points_total) if points_total > 0 else 0
    return {
        "tasks_total": len(tasks),
        "points_total": points_total,
        "points_done": points_done,
        "completion": completion,
        "by_status": by_status,
        "features_touched": sorted(features),
        "in_timeline": in_timeline,
        "out_of_timeline": out_of_timeline,
        "gates_total": gates_total,
        "gates_done": gates_done,
        "gates_in_timeline": gates_in_timeline,
        "gates_done_in_timeline": gates_done_in_timeline,
    }


def calculate_release_readiness(*, progress: dict[str, object]) -> str:
    avg = progress.get("avg_completion", 0) or 0
    critical_path_complete = bool(progress.get("critical_path_complete", False))

    try:
        avg_int = int(avg)  # type: ignore[arg-type]
    except Exception:
        avg_int = 0

    if avg_int >= 90 and critical_path_complete:
        return "🟢 GREEN - Ready to ship"
    if critical_path_complete:
        return "🟡 YELLOW - Not ready yet (scope remaining)"
    return "🔴 RED - Critical path incomplete"


def calculate_release_trajectory(
    *, progress: dict[str, object], current_sprint_index: int | None, sprint_count: int
) -> tuple[str, tuple[int, int] | None]:
    """
    Trajectory is timeline-aware (sprint index), not "are we already done?".
    Returns (label, expected_range).
    """
    avg = progress.get("avg_completion", 0) or 0
    critical_path_started = bool(progress.get("critical_path_started", True))

    try:
        avg_int = int(avg)  # type: ignore[arg-type]
    except Exception:
        avg_int = 0

    if not current_sprint_index or sprint_count <= 0:
        return ("🟡 YELLOW - No timeline position (current sprint not in release timeline)", None)

    expected_min = int(100 * (current_sprint_index - 1) / sprint_count)
    expected_max = int(100 * current_sprint_index / sprint_count)

    if current_sprint_index >= 2 and not critical_path_started:
        return (f"🔴 RED - Critical path not started by Sprint {current_sprint_index}", (expected_min, expected_max))

    if avg_int < expected_min - 10:
        return (f"🔴 RED - Behind expected completion for Sprint {current_sprint_index}", (expected_min, expected_max))
    if avg_int < expected_min:
        return (
            f"🟡 YELLOW - Slightly behind expected completion for Sprint {current_sprint_index}",
            (expected_min, expected_max),
        )
    if avg_int > expected_max + 10:
        return (
            f"🟢 GREEN - Ahead of expected completion for Sprint {current_sprint_index}",
            (expected_min, expected_max),
        )
    return (f"🟢 GREEN - On track for Sprint {current_sprint_index}", (expected_min, expected_max))


def get_release_timeline_info(*, ph_root: Path, version: str) -> dict[str, object]:
    """Return release timeline + current sprint position (if available)."""
    version = normalize_version(version)
    release_dir = ph_root / "releases" / version
    plan_file = release_dir / "plan.md"

    sprint_count_default = 3
    current_sprint = _resolve_current_sprint_id(ph_root=ph_root, fallback="SPRINT-SEQ-0001")
    start_sprint_default = current_sprint

    plan_meta = parse_plan_front_matter(plan_path=plan_file)
    planned_sprints = sprint_count_default
    if plan_meta:
        maybe = parse_int(plan_meta.get("planned_sprints"))
        if maybe is not None and maybe > 0:
            planned_sprints = maybe

    timeline_mode: str | None = None
    if plan_meta:
        raw_mode = plan_meta.get("timeline_mode")
        if isinstance(raw_mode, str):
            timeline_mode = raw_mode.strip().lower()

    has_slot_config = bool(
        plan_meta and ("sprint_slots" in plan_meta or timeline_mode in {"slots", "sprint-slots", "sprint_slots"})
    )
    if has_slot_config:
        slots = parse_slot_list(plan_meta.get("sprint_slots") if plan_meta else None, planned_sprints)

        assignments: dict[int, str] = {}
        duplicates: dict[int, list[str]] = {}

        for sprint_dir in iter_sprint_dirs(sprints_dir=ph_root / "sprints"):
            sprint_release = sprint_plan_release_version(sprint_dir=sprint_dir)
            if sprint_release != version:
                continue
            slot = sprint_plan_release_slot(sprint_dir=sprint_dir)
            if slot is None:
                continue
            sprint_id = sprint_dir.name
            if slot in assignments and assignments[slot] != sprint_id:
                duplicates.setdefault(slot, [assignments[slot]]).append(sprint_id)
                continue
            assignments[slot] = sprint_id

        sprint_ids: list[str] = [assignments[slot] for slot in slots if slot in assignments]

        current_slot: int | None = None
        for slot, sprint_id in assignments.items():
            if sprint_id == current_sprint:
                current_slot = slot
                break

        current_index: int | None = None
        if current_slot is not None and current_slot in slots:
            current_index = slots.index(current_slot) + 1

        return {
            "timeline_mode": "sprint_slots",
            "planned_sprints": len(slots),
            "sprint_slots": slots,
            "slot_assignments": assignments,
            "slot_duplicates": duplicates,
            "sprint_ids": sprint_ids,
            "current_sprint": current_sprint,
            "current_sprint_slot": current_slot,
            "current_sprint_index": current_index,
        }

    start_sprint = start_sprint_default
    sprint_timeline: list[str] = []
    if plan_meta:
        raw = plan_meta.get("start_sprint")
        if isinstance(raw, str) and raw.strip():
            start_sprint = raw.strip()
        explicit_timeline = plan_meta.get("sprint_ids")
        if isinstance(explicit_timeline, list) and explicit_timeline:
            sprint_timeline = calculate_sprint_range(
                start_sprint=start_sprint,
                sprint_count=len(explicit_timeline),
                explicit=[str(item) for item in explicit_timeline if str(item)],
            )
            planned_sprints = len(sprint_timeline)
        else:
            sprint_timeline = calculate_sprint_range(
                start_sprint=start_sprint,
                sprint_count=planned_sprints,
                explicit=None,
            )
    else:
        sprint_timeline = calculate_sprint_range(start_sprint=start_sprint, sprint_count=planned_sprints, explicit=None)

    current_index = None
    if current_sprint in sprint_timeline:
        current_index = sprint_timeline.index(current_sprint) + 1

    return {
        "timeline_mode": "sprint_ids",
        "planned_sprints": planned_sprints,
        "sprint_ids": sprint_timeline,
        "current_sprint": current_sprint,
        "current_sprint_index": current_index,
    }


def load_release_features(*, ph_root: Path, version: str) -> dict[str, dict[str, object]]:
    if not version.startswith("v"):
        version = f"v{version}"

    features_file = ph_root / "releases" / version / "features.yaml"
    if not features_file.exists():
        return {}

    try:
        content = features_file.read_text(encoding="utf-8")
    except Exception:
        return {}

    features: dict[str, dict[str, object]] = {}
    in_features = False
    current_feature: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip()

        if line.startswith("features:"):
            in_features = True
            continue

        if not line.strip() or line.strip().startswith("#"):
            continue

        if in_features:
            if line.startswith("  ") and ":" in line and not line.startswith("    "):
                current_feature = line.strip().split(":", 1)[0]
                if current_feature:
                    features[current_feature] = {}
            elif current_feature and line.startswith("    ") and ":" in line:
                key, value = line.strip().split(":", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                if value.startswith("[") and value.endswith("]"):
                    items = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
                    features[current_feature][key] = [item for item in items if item]
                elif value.lower() in {"true", "false"}:
                    features[current_feature][key] = value.lower() == "true"
                elif value.isdigit():
                    features[current_feature][key] = int(value)
                else:
                    features[current_feature][key] = value

    return features


def calculate_release_progress(
    *, ph_root: Path, version: str, features: dict[str, dict[str, object]], env: dict[str, str]
) -> dict[str, object]:
    if not features:
        return {}

    tasks_by_feature = collect_all_sprint_tasks(sprints_dir=ph_root / "sprints")

    feature_completions: dict[str, int] = {}
    feature_started: dict[str, bool] = {}
    for feature_name in features.keys():
        tasks = tasks_by_feature.get(feature_name)
        if tasks:
            metrics = calculate_feature_metrics(tasks=tasks)
            raw = metrics.get("completion_percentage", 0)
            try:
                feature_completions[feature_name] = int(raw)  # type: ignore[arg-type]
            except Exception:
                feature_completions[feature_name] = 0
            by_status = metrics.get("by_status") or {}
            started = bool(by_status.get("done") or by_status.get("doing") or by_status.get("review"))  # type: ignore[truthy-bool]
            feature_started[feature_name] = started
        else:
            feature_completions[feature_name] = 0
            feature_started[feature_name] = False

    total_features = len(features)
    completed_features = 0
    total_completion = 0
    critical_path_complete = True
    critical_path_started = True
    started_features = 0

    for feature_name, feature_data in features.items():
        completion = feature_completions.get(feature_name, 0)
        total_completion += completion

        if completion >= 90:
            completed_features += 1

        if bool(feature_data.get("critical_path")) and completion < 90:
            critical_path_complete = False

        if feature_started.get(feature_name, False):
            started_features += 1
        if bool(feature_data.get("critical_path")) and not feature_started.get(feature_name, False):
            critical_path_started = False

    avg_completion = total_completion // total_features if total_features > 0 else 0

    return {
        "total_features": total_features,
        "completed_features": completed_features,
        "avg_completion": avg_completion,
        "critical_path_complete": critical_path_complete,
        "critical_path_started": critical_path_started,
        "started_features": started_features,
        "feature_completions": feature_completions,
    }


def run_release_list(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    releases_dir = ctx.ph_data_root / "releases"
    if not releases_dir.exists():
        print("📦 No releases directory")
        return 0

    releases = list_release_versions(ph_root=ctx.ph_data_root)
    if not releases:
        print("📦 No releases found")
        return 0

    current = _read_current_release_target(ph_root=ctx.ph_data_root)

    print("📦 RELEASES")
    for release in releases:
        indicator = " (current)" if current and release == current else ""
        print(f"  {release}{indicator}")
    return 0


def run_release_status(*, ctx: Context, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = _read_current_release_target(ph_root=ctx.ph_data_root)
    if not version:
        print("❌ No current release found")
        available = list_release_versions(ph_root=ctx.ph_data_root)
        if available:
            print("📦 Available releases:")
            for name in available:
                print(f"  • {name}")
            print("💡 Activate one with: ph release activate --release vX.Y.Z")
        else:
            print("💡 Create one with: ph release plan --version v1.2.0 --sprints 3 --activate")
        return 1

    release_dir = ctx.ph_data_root / "releases" / version
    if not release_dir.exists():
        print(f"❌ Release {version} not found")
        return 1

    features = load_release_features(ph_root=ctx.ph_data_root, version=version)
    progress = calculate_release_progress(ph_root=ctx.ph_data_root, version=version, features=features, env=env)
    readiness = calculate_release_readiness(progress=progress)

    timeline = get_release_timeline_info(ph_root=ctx.ph_data_root, version=version)
    sprint_count = int(timeline.get("planned_sprints") or 3)
    sprint_timeline = timeline.get("sprint_ids") or []
    if not isinstance(sprint_timeline, list):
        sprint_timeline = []
    sprint_timeline = [str(item) for item in sprint_timeline if str(item)]
    current_sprint = str(
        timeline.get("current_sprint")
        or _resolve_current_sprint_id(ph_root=ctx.ph_data_root, fallback="SPRINT-SEQ-0001")
    )
    current_sprint_index = timeline.get("current_sprint_index")
    if not isinstance(current_sprint_index, int):
        current_sprint_index = None
    timeline_mode = str(timeline.get("timeline_mode") or "sprint_ids").strip().lower()
    slot_alignments: dict[int, dict[str, object]] = {}
    slot_list: list[int] = []

    if timeline_mode == "sprint_slots":
        slot_list_raw = timeline.get("sprint_slots") or list(range(1, sprint_count + 1))
        if not isinstance(slot_list_raw, list):
            slot_list_raw = list(range(1, sprint_count + 1))
        slot_list = [
            int(slot)
            for slot in slot_list_raw
            if isinstance(slot, int) or (isinstance(slot, str) and str(slot).isdigit())
        ]
        slot_alignments = _collect_release_slot_alignments(plan_path=release_dir / "plan.md", slots=slot_list)

        current_slot = timeline.get("current_sprint_slot")
        slot_suffix = f" (slot {current_slot})" if current_slot else ""
        current_sprint_label = (
            f"{current_sprint_index} of {sprint_count}{slot_suffix}"
            if current_sprint_index
            else f"n/a of {sprint_count}"
        )
        target_slot = slot_list[-1] if slot_list else sprint_count
        target = f"Slot {target_slot}"
    else:
        current_sprint_label = (
            f"{current_sprint_index} of {sprint_count}" if current_sprint_index else f"n/a of {sprint_count}"
        )
        target = sprint_timeline[-1] if sprint_timeline else "TBD"

    trajectory, expected_range = calculate_release_trajectory(
        progress=progress, current_sprint_index=current_sprint_index, sprint_count=sprint_count
    )

    tagged_tasks = collect_release_tagged_tasks(ph_root=ctx.ph_data_root, version=version)
    tagged_summary = summarize_tagged_tasks(tasks=tagged_tasks, sprint_timeline=sprint_timeline)
    tagged_progress: dict[str, object] = {
        "avg_completion": tagged_summary.get("completion", 0),
        "critical_path_started": True,
    }
    tagged_trajectory, tagged_expected_range = calculate_release_trajectory(
        progress=tagged_progress, current_sprint_index=current_sprint_index, sprint_count=sprint_count
    )

    print(f"📦 RELEASE STATUS: {version}")
    print("=" * 60)
    print(f"Sprint: {current_sprint_label} ({current_sprint})")
    if timeline_mode == "sprint_slots":
        current_slot = timeline.get("current_sprint_slot")
        if isinstance(current_slot, int) and current_slot in slot_list:
            goal = _slot_alignment_goal(slot_alignments.get(current_slot))
            print(f"Slot Goal: {goal}")
        warnings = _release_alignment_warnings_for_active_sprint(
            ph_root=ctx.ph_data_root,
            version=version,
            timeline=timeline,
            slots=slot_list,
            slot_alignments=slot_alignments,
        )
        if warnings:
            print("⚠️ Alignment warnings:")
            for w in warnings:
                print(f"  - {w}")
    print(
        f"Overall Progress: {progress.get('avg_completion', 0)}% complete "
        f"({progress.get('started_features', 0)}/{progress.get('total_features', 0)} features started)"
    )
    print(f"Target: {target}")
    print(f"Release Trajectory: {trajectory}")
    if expected_range and current_sprint_index:
        print(
            f"  Expected completion band: {expected_range[0]}–{expected_range[1]}% "
            f"by end of Sprint {current_sprint_index}/{sprint_count}"
        )
    if tagged_summary.get("tasks_total"):
        features_touched = tagged_summary.get("features_touched") or []
        features_count = len(features_touched)
        print(
            "Tagged Workstream: "
            f"{tagged_summary.get('completion', 0)}% "
            f"({tagged_summary.get('points_done', 0)}/{tagged_summary.get('points_total', 0)} pts) "
            f"across {tagged_summary.get('tasks_total', 0)} tasks ({features_count} features)"
        )
        print(f"Tagged Trajectory: {tagged_trajectory}")
        if tagged_expected_range and current_sprint_index:
            print(
                f"  Expected completion band: {tagged_expected_range[0]}–{tagged_expected_range[1]}% "
                f"by end of Sprint {current_sprint_index}/{sprint_count}"
            )
        if sprint_timeline:
            out_of_timeline = int(tagged_summary.get("out_of_timeline") or 0)
            if out_of_timeline:
                print(f"  ⚠️  {out_of_timeline} tagged task(s) are outside the release sprint timeline")
        gates_total = int(tagged_summary.get("gates_total") or 0)
        if gates_total:
            gates_done = int(tagged_summary.get("gates_done") or 0)
            if sprint_timeline:
                gates_done_in = int(tagged_summary.get("gates_done_in_timeline") or 0)
                gates_in = int(tagged_summary.get("gates_in_timeline") or 0)
                print(f"Gate Burn-up: {gates_done}/{gates_total} complete (in timeline: {gates_done_in}/{gates_in})")
            else:
                print(f"Gate Burn-up: {gates_done}/{gates_total} complete")
    print(f"Release Readiness: {readiness}")
    print()

    if features:
        print("🎯 Feature Progress:")
        for feature_name, feature_data in features.items():
            completion = int(progress.get("feature_completions", {}).get(feature_name, 0))
            status_emoji = "✅" if completion >= 90 else ("🔄" if completion > 0 else "⭕")
            critical_indicator = " (Critical Path)" if bool(feature_data.get("critical_path")) else ""
            print(f"{status_emoji} {feature_name:<20} {completion:3d}% complete{critical_indicator}")
        print()

    if tagged_tasks:
        print("🏷️ Release-Tagged Tasks:")

        def _is_gate(task: dict[str, Any]) -> bool:
            return bool(task.get("release_gate") is True) or str(task.get("release_gate", "")).strip().lower() in {
                "true",
                "yes",
                "1",
            }

        tagged_tasks = sorted(
            tagged_tasks,
            key=lambda task: (
                0 if _is_gate(task) else 1,
                str(task.get("id") or ""),
            ),
        )
        show_n = 12
        for task in tagged_tasks[:show_n]:
            status = str(task.get("status", "todo")).strip().lower()
            if status == "completed":
                status = "done"
            status_emoji = {
                "todo": "⭕",
                "doing": "🔄",
                "review": "👀",
                "done": "✅",
                "blocked": "🚫",
            }.get(status, "❓")
            gate = _is_gate(task)
            gate_suffix = " [gate]" if gate else ""
            try:
                points = int(task.get("story_points", 0) or 0)
            except Exception:
                points = 0
            print(
                f"{status_emoji} {task.get('id')}: {task.get('title')} ({points}pts) "
                f"[{task.get('feature')}] {task.get('sprint')}{gate_suffix}"
            )
        remaining = len(tagged_tasks) - show_n
        if remaining > 0:
            print(f"...and {remaining} more")
    print()

    print("📅 Sprint Breakdown:")
    if timeline_mode == "sprint_slots":
        slots = slot_list or list(range(1, sprint_count + 1))
        assignments = timeline.get("slot_assignments") or {}
        if not isinstance(assignments, dict):
            assignments = {}
        current_slot = timeline.get("current_sprint_slot") if isinstance(timeline.get("current_sprint_slot"), int) else None
        for i, slot in enumerate(slots, 1):
            sprint_id = assignments.get(slot)
            label = sprint_id if sprint_id else "(unassigned)"
            if sprint_id == current_sprint:
                status = "🔄 In progress"
            elif sprint_id and is_sprint_archived(ph_root=ctx.ph_data_root, sprint_id=str(sprint_id)):
                status = "✅ Complete"
            elif current_sprint_index and sprint_id and i < int(current_sprint_index):
                status = "✅ Complete"
            else:
                status = "⭕ Planned"
            marker = "▶ " if current_slot == slot else ""
            goal = _slot_alignment_goal(slot_alignments.get(slot))
            print(f"{status} {marker}Slot {slot}: {label} — Goal: {goal} (Sprint {i} of {sprint_count})")
    else:
        for i, sprint_id in enumerate(sprint_timeline, 1):
            if sprint_id == current_sprint:
                status = "🔄 In progress"
            elif current_sprint_index and i < int(current_sprint_index):
                status = "✅ Complete"
            else:
                status = "⭕ Planned"
            print(f"{status} {sprint_id} (Sprint {i} of {sprint_count})")
    return 0


def _release_features_yaml_path(*, ph_root: Path, version: str) -> Path:
    if not version.startswith("v"):
        version = f"v{version}"
    return ph_root / "releases" / version / "features.yaml"


def run_release_add_feature(
    *,
    ctx: Context,
    release: str,
    feature: str,
    epic: bool,
    critical: bool,
) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = release.strip()
    if not version.startswith("v"):
        version = f"v{version}"

    features_file = _release_features_yaml_path(ph_root=ctx.ph_data_root, version=version)
    if not features_file.exists():
        print(f"❌ Release {version} not found. Create with: ph release plan")
        return 1

    features = load_release_features(ph_root=ctx.ph_data_root, version=version)

    feature_type = "epic" if epic else "regular"
    features[feature] = {
        "type": feature_type,
        "priority": "P1",
        "status": "planned",
        "completion": 0,
        "critical_path": critical,
    }

    # Match legacy release add-feature behavior byte-for-byte.
    content = features_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    new_lines: list[str] = []
    in_features = False
    for line in lines:
        if line.strip().startswith("features:"):
            new_lines.append(line)
            in_features = True

            for feat_name, feat_data in features.items():
                new_lines.append(f"  {feat_name}:")
                for key, value in feat_data.items():
                    if isinstance(value, list):
                        value_str = "[" + ", ".join(str(item) for item in value) + "]"
                    else:
                        value_str = str(value)
                    new_lines.append(f"    {key}: {value_str}")
                new_lines.append("")
            continue

        if in_features and (line.startswith("features:") or not line.startswith(" ")):
            in_features = False
            if line.strip():
                new_lines.append(line)
            continue

        if not in_features:
            new_lines.append(line)

    features_file.write_text("\n".join(new_lines), encoding="utf-8")

    print(f"{_ADD_FEATURE_SUCCESS_PREFIX} {feature} to release {version}")
    return 0


def run_release_suggest(*, ctx: Context, version: str) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    print(f"💡 SUGGESTED FEATURES FOR {version}")
    print("=" * 50)

    features_dir = ctx.ph_data_root / "features"
    if not features_dir.exists():
        return 0

    for feature_dir in features_dir.iterdir():
        if not feature_dir.is_dir():
            continue

        status_file = feature_dir / "status.md"
        if not status_file.exists():
            continue

        try:
            content = status_file.read_text(encoding="utf-8")
        except Exception:
            continue

        stage = "unknown"
        for line in content.splitlines():
            if line.startswith("Stage:"):
                stage = line.split(":", 1)[1].strip()
                break

        if stage in ["approved", "developing", "in_progress"]:
            print(f"📦 {feature_dir.name:<20} Stage: {stage} - Good candidate")
        elif stage in ["proposed", "planned"]:
            print(f"🤔 {feature_dir.name:<20} Stage: {stage} - Needs approval")
    return 0


def _resolve_required_current_sprint_id(*, ph_root: Path) -> str | None:
    link = ph_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    if not resolved.is_dir() or not resolved.name.startswith("SPRINT-"):
        return None
    return resolved.name


def run_release_close(*, ctx: Context, version: str, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = version.strip()
    if not version.startswith("v"):
        version = f"v{version}"

    release_dir = ctx.ph_data_root / "releases" / version
    if not release_dir.exists():
        print(f"❌ Release {version} not found")
        return 1

    delivered_sprint = _resolve_required_current_sprint_id(ph_root=ctx.ph_data_root)
    if not delivered_sprint:
        print("❌ No current sprint found (missing or invalid sprints/current)")
        return 1

    delivered_date_obj = clock_today(env=env)
    delivered_date = delivered_date_obj.strftime("%Y-%m-%d")

    changelog_content = f"""---
title: Release {version} Changelog
type: changelog
version: {version}
date: {delivered_date}
tags: [changelog, release]
links: []
---

# Changelog: {version}

## Release Summary
Released on {delivered_date_obj.strftime("%B %d, %Y")}

## Features Delivered
"""

    features = load_release_features(ph_root=ctx.ph_data_root, version=version)
    for feature_name in features.keys():
        changelog_content += f"- **{feature_name}**: Feature description\n"

    changelog_content += """

## Tasks Completed
*Auto-generated from sprint tasks*

## Breaking Changes
- None

## Migration Guide
- No migration required

## Known Issues
- None

## Contributors
- Team members who contributed
"""

    (release_dir / "changelog.md").write_text(changelog_content, encoding="utf-8")

    plan_file = release_dir / "plan.md"
    if plan_file.exists():
        try:
            lines = plan_file.read_text(encoding="utf-8").splitlines()
            if lines and lines[0].strip() == "---":
                front_matter_end: int | None = None
                for idx in range(1, len(lines)):
                    if lines[idx].strip() == "---":
                        front_matter_end = idx
                        break

                if front_matter_end is not None:
                    front_matter = lines[1:front_matter_end]
                    index_by_key: dict[str, int] = {}
                    for idx, line in enumerate(front_matter):
                        if ":" not in line:
                            continue
                        key = line.split(":", 1)[0].strip()
                        if key:
                            index_by_key[key] = idx

                    def upsert(key: str, value: str) -> None:
                        rendered = f"{key}: {value}"
                        if key in index_by_key:
                            front_matter[index_by_key[key]] = rendered
                            return

                        insert_at = index_by_key.get("status")
                        if insert_at is None:
                            insert_at = len(front_matter) - 1 if front_matter else 0
                        else:
                            insert_at += 1
                        front_matter.insert(insert_at, rendered)

                        index_by_key.clear()
                        for i, line in enumerate(front_matter):
                            if ":" not in line:
                                continue
                            k = line.split(":", 1)[0].strip()
                            if k:
                                index_by_key[k] = i

                    upsert("status", "delivered")
                    upsert("delivered_sprint", delivered_sprint)
                    upsert("delivered_date", delivered_date)

                    lines = [lines[0], *front_matter, lines[front_matter_end], *lines[front_matter_end + 1 :]]

            header = f"# Release {version}"
            for idx, line in enumerate(lines):
                if line.strip() != header:
                    continue
                note = (
                    f"> Release status: **delivered** (marked delivered in `{delivered_sprint}`, on {delivered_date})."
                )
                search_end = min(idx + 8, len(lines))
                replaced = False
                for j in range(idx + 1, search_end):
                    if lines[j].startswith("> Release status:"):
                        lines[j] = note
                        replaced = True
                        break
                    if lines[j].startswith("## "):
                        break
                if not replaced:
                    lines.insert(idx + 1, "")
                    lines.insert(idx + 2, note)
                break

            plan_file.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        except Exception as exc:
            print(f"⚠️ Could not update {plan_file}: {exc}")

    delivered_dir = ctx.ph_data_root / "releases" / "delivered"
    delivered_dir.mkdir(parents=True, exist_ok=True)

    print(f"✅ Release {version} closed")
    print(f"📋 Generated changelog: {release_dir}/changelog.md")
    if plan_file.exists():
        print(f"📝 Updated plan status: {plan_file}")
    print("📈 Ready for deployment")

    return 0
