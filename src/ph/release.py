from __future__ import annotations

import datetime as dt
import difflib
import re
import sys
from pathlib import Path
from typing import Any, TextIO

from .clock import today as clock_today
from .context import Context
from .feature_status_updater import calculate_feature_metrics, collect_all_sprint_tasks
from .remediation_hints import ph_prefix, print_next_commands
from .shell_quote import shell_quote
from .validate_docs import run_validate

_SYSTEM_SCOPE_REMEDIATION = "Releases are project-scope only. Use: ph --scope project release ..."
_DONE_STATUSES = {"done", "completed"}


def _plan_hint_lines() -> tuple[str, ...]:
    return (
        "Release plan scaffold created under .project-handbook/releases/<version>/plan.md",
        "  - Assign features via 'ph release add-feature --release <version> --feature <name> --slot <n> "
        "--commitment committed|stretch --intent deliver|decide|enable'",
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


def _current_release_pointer_path(*, ph_root: Path) -> Path:
    return ph_root / "releases" / "current.txt"


def _write_current_release_pointer(*, ph_root: Path, version: str) -> None:
    version = normalize_version((version or "").strip())
    if not version:
        return
    path = _current_release_pointer_path(ph_root=ph_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{version}\n", encoding="utf-8")


def _read_current_release_pointer(*, ph_root: Path) -> str | None:
    path = _current_release_pointer_path(ph_root=ph_root)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    version = normalize_version(raw)
    if not version:
        return None
    if not (ph_root / "releases" / version).exists():
        return None
    return version


def get_current_release(*, ph_root: Path) -> str | None:
    return _read_current_release_target(ph_root=ph_root)


def set_current_release(*, ph_root: Path, version: str) -> bool:
    version = normalize_version((version or "").strip())
    if not version:
        return False
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

    _write_current_release_pointer(ph_root=ph_root, version=version)
    return True


def clear_current_release(*, ph_root: Path) -> None:
    current_link = ph_root / "releases" / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink(missing_ok=True)
    _current_release_pointer_path(ph_root=ph_root).unlink(missing_ok=True)


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

            for slot in range(1, sprint_count + 1):
                plan_content += f"""

## Slot {slot}: Slot {slot}
### Slot Goal
- TBD
### Enablement
- TBD
### Scope Boundaries
In scope:
- TBD
Out of scope:
- TBD
### Intended Gates
- Gate: TBD
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
  #   slot: 1
  #   commitment: committed   # committed|stretch
  #   intent: deliver         # deliver|decide|enable
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
  #   slot: 1
  #   commitment: committed   # committed|stretch
  #   intent: deliver         # deliver|decide|enable
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
    print(f"cd -- {shell_quote(resolved_release_dir)}")
    print(f"📅 Timeline: {sprint_count} sprint slot(s) (decoupled from calendar dates)")
    print("📝 Next steps:")
    print(f"   1. Edit {resolved_plan_path} to define release goals")
    print(
        f"   2. Add features: ph release add-feature --release {raw_version} --feature feature-name "
        "--slot 1 --commitment committed --intent deliver"
    )
    print(f"   3. Activate when ready: ph release activate --release {raw_version}")
    print("   4. Review timeline and adjust if needed")
    for line in _plan_hint_lines():
        print(line)
    return 0


def _feature_stage(*, feature_dir: Path) -> str:
    status_path = feature_dir / "status.md"
    if not status_path.exists():
        return "unknown"
    try:
        content = status_path.read_text(encoding="utf-8")
    except Exception:
        return "unknown"
    for raw in content.splitlines():
        if raw.startswith("Stage:"):
            return raw.split(":", 1)[1].strip() or "unknown"
    return "unknown"


def _resolve_base_release_for_draft(*, ctx: Context, base: str) -> str | None:
    base_norm = (base or "").strip()
    if not base_norm:
        return None
    if base_norm.lower() == "current":
        return get_current_release(ph_root=ctx.ph_data_root)
    if base_norm.lower() == "latest-delivered":
        delivered: list[str] = []
        for version in list_release_versions(ph_root=ctx.ph_data_root):
            plan_path = ctx.ph_data_root / "releases" / version / "plan.md"
            meta = parse_plan_front_matter(plan_path=plan_path)
            status = str(meta.get("status") or "").strip().lower()
            if status == "delivered":
                delivered.append(version)
        return delivered[-1] if delivered else None
    return normalize_version(base_norm)


def run_release_draft(
    *,
    ctx: Context,
    version: str,
    sprints: int,
    base: str,
    format: str,
    schema: bool = False,
) -> int:
    planned_sprints = int(sprints or 0) or 3
    fmt = (format or "text").strip().lower()
    if fmt not in {"text", "json"}:
        print("❌ Invalid --format (expected text|json)")
        return 1

    if schema:
        import json as _json

        print(_json.dumps(release_draft_schema(), indent=2))
        return 0

    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    base_release = _resolve_base_release_for_draft(ctx=ctx, base=base)
    base_norm = (base or "").strip().lower()
    if base_norm and base_norm not in {"latest-delivered"} and not base_release:
        print("❌ Unable to resolve --base (expected latest-delivered|current|vX.Y.Z)")
        return 1

    raw_version = (version or "").strip() or "next"
    if raw_version.lower() == "next":
        base_for_version = base_release or get_current_release(ph_root=ctx.ph_data_root)
        if not base_for_version:
            available = list_release_versions(ph_root=ctx.ph_data_root)
            base_for_version = available[-1] if available else "v0.1.0"
        raw_version = bump_version(base_for_version, bump="patch")
    target_version = normalize_version(raw_version)

    base_features: set[str] = set()
    if base_release:
        try:
            base_features = set(load_release_features(ph_root=ctx.ph_data_root, version=base_release).keys())
        except Exception:
            base_features = set()

    features_dir = ctx.ph_data_root / "features"
    candidates: list[dict[str, str]] = []
    if features_dir.exists():
        for feat_dir in sorted([p for p in features_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
            if feat_dir.name in base_features:
                continue
            candidates.append({"feature": feat_dir.name, "stage": _feature_stage(feature_dir=feat_dir)})

    stage_rank = {
        "in_progress": 0,
        "in-progress": 0,
        "developing": 1,
        "approved": 2,
        "planned": 3,
        "proposed": 4,
        "concept": 5,
        "unknown": 6,
    }

    def cand_key(c: dict[str, str]) -> tuple[int, str]:
        st = (c.get("stage") or "unknown").strip().lower()
        rank = stage_rank.get(st, 50)
        return (rank, str(c.get("feature") or ""))

    candidates = sorted(candidates, key=cand_key)

    suggested: list[dict[str, object]] = []
    for idx, cand in enumerate(candidates[: max(0, planned_sprints * 4)]):
        slot = (idx % planned_sprints) + 1
        stage = (cand.get("stage") or "unknown").strip().lower()
        intent = "deliver" if stage in {"in_progress", "in-progress", "developing", "approved"} else "decide"
        commitment = "committed" if idx < planned_sprints else "stretch"
        suggested.append(
            {
                "feature": cand["feature"],
                "stage": cand["stage"],
                "slot": slot,
                "commitment": commitment,
                "intent": intent,
                "priority": "P1",
            }
        )

    operator_questions = [
        "What is the primary outcome theme for this release?",
        "Should we bias toward shipping features or paying down tech debt?",
        "What risk posture should we take (aggressive vs conservative scope)?",
        "Which items are must-commit vs stretch (and why)?",
        "Which decisions must be made before slot 1 execution starts?",
    ]

    if fmt == "json":
        import json as _json

        print(
            _json.dumps(
                build_release_draft_payload(
                    target_version=target_version,
                    planned_sprints=planned_sprints,
                    base_release=base_release,
                    excluded_base_features=sorted(base_features),
                    candidate_features=candidates,
                    suggested_features=suggested,
                    operator_questions=operator_questions,
                ),
                indent=2,
            )
        )
        return 0

    print(f"📦 RELEASE DRAFT ({target_version})")
    if base_release:
        print(f"Base: {base_release} (excluding {len(base_features)} feature(s))")
    print(f"Planned sprints: {planned_sprints}")
    print()

    print("Operator Question Pack (ask during release planning):")
    for q in operator_questions:
        print(f"- {q}")
    print()

    print("Suggested release plan commands:")
    print(f"- ph release plan --version {target_version} --sprints {planned_sprints}")
    print(f"- ph release activate --release {target_version}")
    print()

    print("Suggested feature assignments (local-only; no web research here):")
    if not suggested:
        print("- No candidates found under `.project-handbook/features/`")
        return 0
    for s in suggested:
        print(
            "- "
            f"ph release add-feature --release {target_version} --feature {s['feature']} "
            f"--slot {s['slot']} --commitment {s['commitment']} --intent {s['intent']} "
            f"--priority {s['priority']}"
        )
    print()

    decide = [s for s in suggested if str(s.get("intent")) == "decide"]
    if decide:
        print("Suggested research-discovery tasks (do web/deep research there):")
        for s in decide[:10]:
            print(f"- Feature: {s['feature']} (intent=decide)")
            print(f'  - ph dr add --id DR-XXXX --title "<decision title>" --feature {s["feature"]}')
            print(
                '  - ph task create --title "Investigate: <decision>" --feature '
                f"{s['feature']} --decision DR-XXXX --type research-discovery --points 3 --release current"
            )
        print()

    print("Next (interactive, release planning session):")
    print("- Run `ph onboarding session release-planning` and apply this draft with operator input.")
    return 0


def build_release_draft_payload(
    *,
    target_version: str,
    planned_sprints: int,
    base_release: str | None,
    excluded_base_features: list[str],
    candidate_features: list[dict[str, str]],
    suggested_features: list[dict[str, object]],
    operator_questions: list[str],
) -> dict[str, object]:
    def add_feature_commands() -> list[str]:
        out: list[str] = []
        for s in suggested_features:
            out.append(
                "ph release add-feature "
                f"--release {target_version} --feature {s['feature']} --slot {s['slot']} "
                f"--commitment {s['commitment']} --intent {s['intent']} --priority {s['priority']}"
            )
        return out

    def research_discovery_commands() -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for s in suggested_features:
            if str(s.get("intent")) != "decide":
                continue
            feature = str(s.get("feature") or "").strip()
            if not feature:
                continue
            out.append(
                {
                    "feature": feature,
                    "reason": "intent=decide (requires bounded decision + approval)",
                    "commands": [
                        f'ph dr add --id DR-XXXX --title "<decision title>" --feature {feature}',
                        (
                            'ph task create --title "Investigate: <decision>" --feature '
                            f"{feature} --decision DR-XXXX --type research-discovery --points 3 --release current"
                        ),
                    ],
                }
            )
        return out

    payload: dict[str, object] = {
        "type": "release-draft",
        "schema_version": 1,
        "version": target_version,
        "planned_sprints": planned_sprints,
        "base_release": base_release,
        "excluded_base_features": excluded_base_features,
        "candidate_features": candidate_features,
        "suggested_features": suggested_features,
        "operator_questions": operator_questions,
        "commands": {
            "release_plan": f"ph release plan --version {target_version} --sprints {planned_sprints}",
            "release_activate": f"ph release activate --release {target_version}",
            "release_add_feature": add_feature_commands(),
            "research_discovery": research_discovery_commands(),
        },
    }
    return payload


def release_draft_schema() -> dict[str, object]:
    commitment_enum = ["committed", "stretch"]
    intent_enum = ["deliver", "decide", "enable"]
    priority_enum = ["P0", "P1", "P2", "P3", "P4"]

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ph release draft (JSON output)",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "type",
            "schema_version",
            "version",
            "planned_sprints",
            "base_release",
            "excluded_base_features",
            "candidate_features",
            "suggested_features",
            "operator_questions",
            "commands",
        ],
        "properties": {
            "type": {"type": "string", "const": "release-draft"},
            "schema_version": {"type": "integer", "const": 1},
            "version": {"type": "string", "pattern": r"^v[0-9]+(?:\.[0-9]+){2}.*$"},
            "planned_sprints": {"type": "integer", "minimum": 1},
            "base_release": {"type": ["string", "null"], "pattern": r"^v[0-9]+(?:\.[0-9]+){2}.*$"},
            "excluded_base_features": {"type": "array", "items": {"type": "string"}},
            "candidate_features": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["feature", "stage"],
                    "properties": {"feature": {"type": "string"}, "stage": {"type": "string"}},
                },
            },
            "suggested_features": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["feature", "stage", "slot", "commitment", "intent", "priority"],
                    "properties": {
                        "feature": {"type": "string"},
                        "stage": {"type": "string"},
                        "slot": {"type": "integer", "minimum": 1},
                        "commitment": {"type": "string", "enum": commitment_enum},
                        "intent": {"type": "string", "enum": intent_enum},
                        "priority": {"type": "string", "enum": priority_enum},
                    },
                },
            },
            "operator_questions": {"type": "array", "items": {"type": "string"}},
            "commands": {
                "type": "object",
                "additionalProperties": False,
                "required": ["release_plan", "release_activate", "release_add_feature", "research_discovery"],
                "properties": {
                    "release_plan": {"type": "string"},
                    "release_activate": {"type": "string"},
                    "release_add_feature": {"type": "array", "items": {"type": "string"}},
                    "research_discovery": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["feature", "reason", "commands"],
                            "properties": {
                                "feature": {"type": "string"},
                                "reason": {"type": "string"},
                                "commands": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                },
            },
        },
    }


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
    print("💡 Pointer: releases/current.txt")
    return run_release_status(ctx=ctx, release=version, env=env)


def run_release_clear(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1
    clear_current_release(ph_root=ctx.ph_data_root)
    print("⭐ Cleared current release")
    return 0


def run_release_progress(*, ctx: Context, release: str | None, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    release_arg = (release or "").strip()
    if release_arg and release_arg.lower() != "current":
        version = normalize_version(release_arg)
        if not (ctx.ph_data_root / "releases" / version).exists():
            print(f"❌ Release {version} not found (expected: releases/{version}/)")
            return 1
    else:
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
    sprint_timeline = timeline.get("sprint_ids") if isinstance(timeline.get("sprint_ids"), list) else []
    sprint_timeline = [str(item) for item in sprint_timeline if str(item)]

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
        raw_current_slot = timeline.get("current_sprint_slot")
        current_slot = raw_current_slot if isinstance(raw_current_slot, int) else None
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

    tagged_tasks = collect_release_tagged_tasks(ph_root=ph_root, version=resolved)
    tagged_summary = summarize_tagged_tasks(tasks=tagged_tasks, sprint_timeline=sprint_timeline)

    content += "\n## Release-Tagged Workstream\n"
    if int(tagged_summary.get("tasks_total") or 0) > 0:
        features_touched = tagged_summary.get("features_touched") or []
        features_count = len(features_touched)
        content += (
            f"- Tasks: {tagged_summary.get('tasks_total', 0)} | "
            f"Points: {tagged_summary.get('points_done', 0)}/{tagged_summary.get('points_total', 0)} | "
            f"Completion: {tagged_summary.get('completion', 0)}% | "
            f"Features touched: {features_count}\n"
        )
        gates_total = int(tagged_summary.get("gates_total") or 0)
        if gates_total:
            gates_done = int(tagged_summary.get("gates_done") or 0)
            content += f"- Gates: {gates_done}/{gates_total} complete\n"
    else:
        content += "*No release-tagged tasks tracked yet.*\n"

    content += "\n## Feature Completion (Historical)\n"
    if features and progress.get("feature_completions"):
        for feature_name, feature_data in features.items():
            completion = int(progress.get("feature_completions", {}).get(feature_name, 0) or 0)
            status_emoji = "✅" if completion >= 90 else ("🔄" if completion > 0 else "⭕")
            critical = " (Critical Path)" if bool(feature_data.get("critical_path")) else ""
            content += f"- {status_emoji} {feature_name}: {completion}%{critical}\n"
    else:
        content += "*No release features tracked yet.*\n"

    gates = [
        task
        for task in tagged_tasks
        if bool(task.get("release_gate") is True)
        or str(task.get("release_gate", "")).strip().lower() in {"true", "yes", "1"}
    ]
    gates_done = len([task for task in gates if str(task.get("status", "")).strip().lower() in {"done", "completed"}])

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
    readiness = (
        calculate_release_readiness_gate_first(feature_progress=progress, tagged_summary=tagged_summary)
        if progress is not None
        else "n/a"
    )
    content += f"- Readiness (gate-first): {readiness}\n"

    progress_file.write_text(content.rstrip() + "\n", encoding="utf-8")
    return progress_file


def run_release_show(*, ctx: Context, release: str | None, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    release_arg = (release or "").strip()
    if release_arg and release_arg.lower() != "current":
        version = normalize_version(release_arg)
        if not (ctx.ph_data_root / "releases" / version).exists():
            print(f"❌ Release {version} not found (expected: releases/{version}/)")
            return 1
    else:
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

    exit_code = run_release_status(ctx=ctx, release=version, env=env)

    progress_path = write_release_progress(ph_root=ctx.ph_data_root, version=version, env=env)
    print()
    print(f"📝 Updated: {progress_path.resolve()}")
    return exit_code


def _read_current_release_target(*, ph_root: Path) -> str | None:
    releases_dir = ph_root / "releases"
    current_link = releases_dir / "current"
    if current_link.is_symlink():
        try:
            target = current_link.readlink()
        except OSError:
            target = None
        if target is not None:
            target_name = target.name
            if target_name.startswith("v") and (releases_dir / target).exists():
                return target_name
        current_link.unlink(missing_ok=True)

    return _read_current_release_pointer(ph_root=ph_root)


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

    Expected strict markers (INIT-0001-workflow-foundations):
    - Slot header: "## Slot <n>: <label>"
    - Subsections: "### Slot Goal", "### Enablement", "### Intended Gates"

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
    slot_header_re = re.compile(rf"^##\s+Slot\s+{slot}:\s*(.+)\s*$", re.IGNORECASE)
    next_slot_header_re = re.compile(r"^##\s+Slot\s+\d+:\s*", re.IGNORECASE)

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
    heading_re = re.compile(r"^###\s+", re.IGNORECASE)

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

    goal_lines = section_lines(section_header=re.compile(r"^###\s+Slot\s+Goal\s*$", re.IGNORECASE))
    enablement_lines = section_lines(section_header=re.compile(r"^###\s+Enablement\s*$", re.IGNORECASE))
    intended_gate_lines = section_lines(section_header=re.compile(r"^###\s+Intended\s+Gates\s*$", re.IGNORECASE))

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
        intended_gates = ["- Gate: TBD"]

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
    raw_current_slot = timeline.get("current_sprint_slot")
    current_slot = raw_current_slot if isinstance(raw_current_slot, int) else None
    slot_to_check = current_slot or slot_meta

    if not release or release.lower() in {"null", "none"}:
        warnings.append(f"Current sprint `{current_sprint_id}` is missing `release: {version}` in its front matter.")
    else:
        normalized_release = normalize_version(release)
        if release.strip().lower() == "current":
            warnings.append(
                f"Current sprint `{current_sprint_id}` uses `release: current`; use `release: {version}` for slot "
                "matching."
            )
        elif normalized_release != normalize_version(version):
            warnings.append(
                f"Current sprint `{current_sprint_id}` is aligned to `{normalized_release}`, not `{version}`."
            )

    if slot_meta is None:
        warnings.append(
            f"Current sprint `{current_sprint_id}` is missing `release_sprint_slot: <n>` in its front matter."
        )
    else:
        if slot_meta not in slots:
            warnings.append(
                f"Current sprint `{current_sprint_id}` has `release_sprint_slot: {slot_meta}`, "
                f"but release plan slots are {slots}."
            )
        assigned = assignments.get(slot_meta) if isinstance(assignments, dict) else None
        if assigned and str(assigned) != current_sprint_id:
            warnings.append(
                f"Slot {slot_meta} is assigned to `{assigned}`, but current sprint is `{current_sprint_id}`."
            )
        if current_slot is not None and current_slot != slot_meta:
            warnings.append(
                f"Current sprint `{current_sprint_id}` front matter says slot {slot_meta}, "
                f"but computed current slot is {current_slot}."
            )
        if current_plan_path and not _sprint_plan_has_release_alignment_heading(
            sprint_plan_path=current_plan_path, slot=slot_meta
        ):
            warnings.append(
                f"Current sprint plan is missing required heading: `## Release Alignment (Slot {slot_meta})`."
            )

    if slot_to_check is not None:
        alignment = slot_alignments.get(int(slot_to_check), {})
        if not alignment:
            warnings.append(
                f"Release plan is missing required slot markers for Slot {slot_to_check} "
                f"(expected `## Slot {slot_to_check}: <label>` + subsections)."
            )
        else:
            if _slot_alignment_goal(alignment) == "TBD":
                warnings.append(f"Release plan Slot {slot_to_check} is missing a `### Slot Goal` value.")
            if _slot_alignment_enablement(alignment) == "TBD":
                warnings.append(f"Release plan Slot {slot_to_check} is missing a `### Enablement` value.")

    duplicates = timeline.get("slot_duplicates") if isinstance(timeline.get("slot_duplicates"), dict) else {}
    if duplicates:
        for dup_slot, sprint_ids in sorted(duplicates.items(), key=lambda t: t[0]):
            if not isinstance(dup_slot, int):
                continue
            if not isinstance(sprint_ids, list):
                continue
            warnings.append(
                f"Slot {dup_slot} has multiple sprint assignments: {', '.join(str(s) for s in sprint_ids)}."
            )

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
    gates_by_status: dict[str, int] = {"todo": 0, "doing": 0, "review": 0, "done": 0, "blocked": 0, "other": 0}
    features: set[str] = set()
    in_timeline = 0
    out_of_timeline = 0

    gates_total = 0
    gates_done = 0
    gates_in_timeline = 0
    gates_done_in_timeline = 0

    for task in tasks:
        status = str(task.get("status", "todo")).strip().lower()
        if status == "completed":
            status = "done"
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
            if status not in gates_by_status:
                gates_by_status["other"] += 1
            else:
                gates_by_status[status] += 1
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
        "gates_by_status": gates_by_status,
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


def calculate_release_readiness_gate_first(
    *, feature_progress: dict[str, object] | None, tagged_summary: dict[str, object] | None
) -> str:
    tagged_summary = tagged_summary or {}

    tasks_total = int(tagged_summary.get("tasks_total") or 0)
    points_total = int(tagged_summary.get("points_total") or 0)
    points_done = int(tagged_summary.get("points_done") or 0)
    completion = int(tagged_summary.get("completion") or 0)

    gates_total = int(tagged_summary.get("gates_total") or 0)
    gates_done = int(tagged_summary.get("gates_done") or 0)

    by_status = tagged_summary.get("by_status") if isinstance(tagged_summary.get("by_status"), dict) else {}
    blocked = int(by_status.get("blocked") or 0)

    gates_by_status = (
        tagged_summary.get("gates_by_status") if isinstance(tagged_summary.get("gates_by_status"), dict) else {}
    )
    gates_blocked = int(gates_by_status.get("blocked") or 0)

    if gates_total > 0:
        if gates_blocked > 0:
            return "🔴 RED - Gate blocked"
        if gates_done >= gates_total:
            return "🟢 GREEN - Gates complete (Ready to ship)"
        return f"🟡 YELLOW - Gates incomplete ({gates_done}/{gates_total} complete)"

    if tasks_total > 0:
        if blocked > 0:
            return "🔴 RED - Tagged work blocked"
        if completion >= 100:
            return "🟢 GREEN - Tagged work complete"
        return f"🟡 YELLOW - Tagged work incomplete ({completion}% / {points_done}/{points_total} pts)"

    _ = feature_progress  # historical only; do not promote to readiness
    return "🟡 YELLOW - No release-tagged tasks/gates; readiness unknown (feature completion is historical)"


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


def run_release_status(*, ctx: Context, release: str | None, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    release_arg = (release or "").strip()
    if release_arg and release_arg.lower() != "current":
        version = normalize_version(release_arg)
    else:
        version = _read_current_release_target(ph_root=ctx.ph_data_root)

    if not version:
        prefix = ph_prefix(ctx)
        print("❌ No current release found", file=sys.stderr)
        available = list_release_versions(ph_root=ctx.ph_data_root)
        if available:
            print("📦 Available releases:", file=sys.stderr)
            for name in available:
                print(f"  • {name}", file=sys.stderr)
            print_next_commands(
                commands=[
                    f"{prefix} release list",
                    f"{prefix} release activate --release vX.Y.Z",
                    f"Re-run: {prefix} release status",
                ],
                file=sys.stderr,
            )
        else:
            print_next_commands(
                commands=[
                    f"{prefix} release plan --version v1.2.0 --sprints 3 --activate",
                    f"Re-run: {prefix} release status",
                ],
                file=sys.stderr,
            )
        return 1

    release_dir = ctx.ph_data_root / "releases" / version
    if not release_dir.exists():
        print(f"❌ Release {version} not found (expected: releases/{version}/)")
        return 1

    features = load_release_features(ph_root=ctx.ph_data_root, version=version)
    progress = calculate_release_progress(ph_root=ctx.ph_data_root, version=version, features=features, env=env)

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

    readiness = calculate_release_readiness_gate_first(feature_progress=progress, tagged_summary=tagged_summary)

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
        f"Feature Completion (historical): {progress.get('avg_completion', 0)}% "
        f"({progress.get('started_features', 0)}/{progress.get('total_features', 0)} features started)"
    )
    print(f"Target: {target}")
    print(f"Feature Trajectory (historical): {trajectory}")
    if expected_range and current_sprint_index:
        print(
            f"  Expected completion band: {expected_range[0]}–{expected_range[1]}% "
            f"by end of Sprint {current_sprint_index}/{sprint_count}"
        )
    if tagged_summary.get("tasks_total"):
        features_touched = tagged_summary.get("features_touched") or []
        features_count = len(features_touched)
        print(
            "Release-Tagged Workstream: "
            f"{tagged_summary.get('completion', 0)}% "
            f"({tagged_summary.get('points_done', 0)}/{tagged_summary.get('points_total', 0)} pts) "
            f"across {tagged_summary.get('tasks_total', 0)} tasks ({features_count} features)"
        )
        print(f"Release-Tagged Trajectory: {tagged_trajectory}")
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
    print(f"Release Readiness (gate-first): {readiness}")
    print()

    if features:
        print("🎯 Feature Completion (historical):")
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
        raw_current_slot = timeline.get("current_sprint_slot")
        current_slot = raw_current_slot if isinstance(raw_current_slot, int) else None
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
    slot: int,
    commitment: str,
    intent: str,
    priority: str | None,
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

    plan_path = ctx.ph_data_root / "releases" / version / "plan.md"
    plan_meta = parse_plan_front_matter(plan_path=plan_path)
    planned_sprints = parse_int(plan_meta.get("planned_sprints")) or 0

    try:
        slot_int = int(slot)
    except Exception:
        print("❌ Invalid --slot (expected an integer)")
        return 1
    if planned_sprints and (slot_int < 1 or slot_int > planned_sprints):
        print(f"❌ Invalid --slot {slot_int} (expected 1..{planned_sprints})")
        return 1

    commitment_norm = (commitment or "").strip().lower()
    if commitment_norm not in {"committed", "stretch"}:
        print("❌ Invalid --commitment (expected committed|stretch)")
        return 1

    intent_norm = (intent or "").strip().lower()
    if intent_norm not in {"deliver", "decide", "enable"}:
        print("❌ Invalid --intent (expected deliver|decide|enable)")
        return 1

    prio = (priority or "P1").strip() or "P1"

    features = load_release_features(ph_root=ctx.ph_data_root, version=version)

    feature_type = "epic" if epic else "regular"
    features[feature] = {
        "slot": slot_int,
        "commitment": commitment_norm,
        "intent": intent_norm,
        "type": feature_type,
        "priority": prio,
        "status": "planned",
        "completion": 0,
        "critical_path": critical,
    }

    content = features_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == "features:":
            out.append(line)
            for feat_name, feat_data in features.items():
                out.append(f"  {feat_name}:")
                for key, value in feat_data.items():
                    if isinstance(value, list):
                        value_str = "[" + ", ".join(str(item) for item in value) + "]"
                    else:
                        value_str = str(value)
                    out.append(f"    {key}: {value_str}")
                out.append("")

            # Skip existing features block.
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or nxt.strip().startswith("#"):
                    i += 1
                    continue
                if nxt.startswith(" "):
                    i += 1
                    continue
                break
            continue
        out.append(line)
        i += 1

    rendered = "\n".join(out).rstrip() + "\n"
    features_file.write_text(rendered, encoding="utf-8")

    print(f"{_ADD_FEATURE_SUCCESS_PREFIX} {feature} to release {version}")
    return 0


def _detect_legacy_slot_format(text: str) -> bool:
    if "## Slot Plans" in text:
        return True
    if re.search(r"^###\s+Slot\s+[1-9][0-9]*\b", text, flags=re.IGNORECASE | re.MULTILINE):
        return True
    if "#### Goal / Purpose" in text:
        return True
    return False


def _detect_strict_slot_format(text: str) -> bool:
    return bool(re.search(r"^##\s+Slot\s+[1-9][0-9]*:\s*.+$", text, flags=re.MULTILINE))


def _migrate_legacy_slot_block_to_strict(*, text: str, planned_sprints: int) -> str:
    lines = text.splitlines()

    # If strict slots already exist, migration only needs to remove legacy markers.
    # This keeps manual edits stable while eliminating strict-only validation failures.
    if _detect_strict_slot_format(text):
        if not _detect_legacy_slot_format(text):
            return text

        start_idx: int | None = None
        for i, raw in enumerate(lines):
            if raw.strip() == "## Slot Plans":
                start_idx = i
                break
        if start_idx is None:
            for i, raw in enumerate(lines):
                if re.match(r"^###\s+Slot\s+[1-9][0-9]*\b", raw.strip(), flags=re.IGNORECASE):
                    start_idx = i
                    break
        if start_idx is None:
            return text

        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            if re.match(r"^##\s+(?!Slot\s+\d+:)", lines[j].strip(), flags=re.IGNORECASE):
                end_idx = j
                break

        new_lines = lines[:start_idx] + lines[end_idx:]
        return "\n".join(new_lines).rstrip() + "\n"

    # Otherwise: convert legacy slot content into strict slots.
    legacy_start: int | None = None
    for i, raw in enumerate(lines):
        if raw.strip() == "## Slot Plans":
            legacy_start = i
            break
    if legacy_start is None:
        for i, raw in enumerate(lines):
            if re.match(r"^###\s+Slot\s+[1-9][0-9]*\b", raw.strip(), flags=re.IGNORECASE):
                legacy_start = i
                break
    if legacy_start is None:
        return text

    legacy_end = len(lines)
    for j in range(legacy_start + 1, len(lines)):
        if re.match(r"^##\s+", lines[j].strip()) and lines[j].strip() != "## Slot Plans":
            legacy_end = j
            break

    legacy_lines = lines[legacy_start:legacy_end]

    slot_theme_re = re.compile(r"^\s*-\s+\*\*Slot\s+([1-9][0-9]*)\*\*.*:\s*(.+?)\s*$", flags=re.IGNORECASE)
    slot_labels: dict[int, str] = {}
    for raw in lines:
        m = slot_theme_re.match(raw)
        if not m:
            continue
        try:
            slot_num = int(m.group(1))
        except Exception:
            continue
        theme = m.group(2).strip()
        if theme and theme.lower() != "sprint theme/focus":
            slot_labels[slot_num] = theme

    slot_header_re = re.compile(r"^###\s+Slot\s+([1-9][0-9]*)\b", flags=re.IGNORECASE)
    slot_starts: list[tuple[int, int]] = []
    for idx, raw in enumerate(legacy_lines):
        m = slot_header_re.match(raw.strip())
        if not m:
            continue
        try:
            slot_num = int(m.group(1))
        except Exception:
            continue
        slot_starts.append((slot_num, idx))
    slot_starts.sort(key=lambda t: t[1])

    def _section_slice(*, start: int) -> list[str]:
        end = len(legacy_lines)
        for _, sidx in slot_starts:
            if sidx > start:
                end = min(end, sidx)
        for j2 in range(start + 1, len(legacy_lines)):
            if re.match(r"^##\s+", legacy_lines[j2].strip()):
                end = min(end, j2)
                break
        return legacy_lines[start:end]

    legacy_by_slot: dict[int, list[str]] = {}
    for slot_num, sidx in slot_starts:
        legacy_by_slot[slot_num] = _section_slice(start=sidx)

    def _extract_subsection(*, section: list[str], header: str) -> list[str]:
        h_re = re.compile(rf"^####\s+{re.escape(header)}\s*$", flags=re.IGNORECASE)
        any_h_re = re.compile(r"^####\s+", flags=re.IGNORECASE)
        start: int | None = None
        for i3, raw in enumerate(section):
            if h_re.match(raw.strip()):
                start = i3 + 1
                break
        if start is None:
            return []
        end = len(section)
        for j3 in range(start, len(section)):
            if any_h_re.match(section[j3].strip()) or slot_header_re.match(section[j3].strip()):
                end = j3
                break
        return section[start:end]

    def _first_line(lines_in: list[str]) -> str:
        for raw in lines_in:
            s = raw.strip()
            if not s:
                continue
            if s.startswith(("- ", "* ")):
                return s[2:].strip()
            if s.startswith("-") and len(s) > 1 and s[1].isspace():
                return s[1:].strip()
            return s
        return ""

    def _scope_items(lines_in: list[str], prefix: str) -> list[str]:
        items: list[str] = []
        for raw in lines_in:
            s = raw.strip()
            if not s:
                continue
            if s.startswith(("- ", "* ")):
                s = s[2:].strip()
            if s.lower().startswith(prefix.lower()):
                val = s.split(":", 1)[1].strip() if ":" in s else ""
                if val:
                    items.append(val)
        return items

    strict_block: list[str] = []
    for slot_num in range(1, max(1, int(planned_sprints or 0)) + 1):
        section = legacy_by_slot.get(slot_num) or []

        goal_lines = _extract_subsection(section=section, header="Goal / Purpose")
        enablement_lines = _extract_subsection(section=section, header="Enablement")
        scope_lines = _extract_subsection(section=section, header="Scope boundaries (in/out)")
        gates_lines = _extract_subsection(section=section, header="Intended gate(s)")

        goal = _first_line(goal_lines) or "TBD"
        enablement = _first_line(enablement_lines) or "TBD"
        if enablement.lower().startswith("how this slot advances the release:"):
            enablement = enablement.split(":", 1)[1].strip() or "TBD"

        in_scope = _scope_items(scope_lines, "In") or ["TBD"]
        out_scope = _scope_items(scope_lines, "Out") or ["TBD"]

        gates: list[str] = []
        for raw in gates_lines:
            s = raw.strip()
            if not s:
                continue
            if s.startswith(("- ", "* ")):
                s = s[2:].strip()
            if s.lower() == "tbd":
                continue
            if s.lower().startswith("gate:"):
                gates.append(f"- {s}")
            else:
                gates.append(f"- Gate: {s}")
        if not gates:
            gates = ["- Gate: TBD"]

        label = slot_labels.get(slot_num) or f"Slot {slot_num}"
        strict_block.extend(
            [
                "",
                f"## Slot {slot_num}: {label}",
                "### Slot Goal",
                f"- {goal}",
                "### Enablement",
                f"- {enablement}",
                "### Scope Boundaries",
                "In scope:",
                *[f"- {item}" for item in in_scope],
                "Out of scope:",
                *[f"- {item}" for item in out_scope],
                "### Intended Gates",
                *gates,
                "",
            ]
        )

    # Replace the legacy block with strict block.
    replacement = strict_block
    new_lines = lines[:legacy_start] + replacement + lines[legacy_end:]
    return "\n".join(new_lines).rstrip() + "\n"


def run_release_migrate_slot_format(
    *,
    ctx: Context,
    release: str,
    diff: bool,
    write_back: bool,
    env: dict[str, str],
) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = (release or "").strip()
    if not version:
        print("❌ Missing --release vX.Y.Z")
        return 1
    if not version.startswith("v"):
        version = f"v{version}"

    plan_path = ctx.ph_data_root / "releases" / version / "plan.md"
    if not plan_path.exists():
        print(f"❌ Release plan not found: {plan_path}")
        return 1

    original = plan_path.read_text(encoding="utf-8")
    meta = parse_plan_front_matter(plan_path=plan_path)
    planned_sprints = parse_int(meta.get("planned_sprints")) or 0
    migrated = _migrate_legacy_slot_block_to_strict(text=original, planned_sprints=planned_sprints)

    if migrated == original:
        print("✅ No changes (release plan is already strict, or no legacy slot block was found).")
        return 0

    if diff and not write_back:
        before = original.splitlines(keepends=True)
        after = migrated.splitlines(keepends=True)
        for line in difflib.unified_diff(
            before,
            after,
            fromfile=str(plan_path),
            tofile=str(plan_path) + " (migrated)",
        ):
            print(line.rstrip("\n"))
        return 0

    if write_back:
        plan_path.write_text(migrated, encoding="utf-8")
        code, _out_path, message = run_validate(
            ph_root=ctx.ph_root,
            ph_project_root=ctx.ph_project_root,
            ph_data_root=ctx.ph_data_root,
            scope=ctx.scope,
            quick=True,
            silent_success=False,
        )
        if message:
            print(message, end="")
        if code != 0:
            print("❌ Migration wrote changes, but validation still reports errors. Fix plan.md and re-run validate.")
        else:
            print("✅ Migration applied and validated.")
        return code

    print(migrated, end="")
    print("\nNext:")
    print(f"- Review: {plan_path}")
    print(f"- Apply: ph release migrate-slot-format --release {version} --write-back")
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


def _release_close_preflight(*, ctx: Context, version: str) -> tuple[bool, dict[str, object]]:
    version = normalize_version(version.strip())
    current = _read_current_release_target(ph_root=ctx.ph_data_root)
    is_current = bool(current and normalize_version(current) == version)

    timeline = get_release_timeline_info(ph_root=ctx.ph_data_root, version=version)
    timeline_mode = str(timeline.get("timeline_mode") or "sprint_ids").strip().lower()

    timeline_open: dict[str, object] = {}
    delivered_sprint: str | None = None

    if timeline_mode == "sprint_slots":
        slots_raw = timeline.get("sprint_slots") or []
        if not isinstance(slots_raw, list):
            slots_raw = []
        slots = [
            int(slot)
            for slot in slots_raw
            if isinstance(slot, int) or (isinstance(slot, str) and str(slot).strip().isdigit())
        ]
        assignments = timeline.get("slot_assignments") if isinstance(timeline.get("slot_assignments"), dict) else {}
        duplicates = timeline.get("slot_duplicates") if isinstance(timeline.get("slot_duplicates"), dict) else {}

        unassigned_slots = [slot for slot in slots if slot not in assignments]

        duplicate_slots: dict[int, list[str]] = {}
        for k, v in duplicates.items():
            try:
                slot_int = int(k) if not isinstance(k, int) else k
            except Exception:
                continue
            if isinstance(v, list):
                items = [str(item) for item in v if str(item)]
                if items:
                    duplicate_slots[int(slot_int)] = items

        unarchived_assigned_sprints: list[str] = []
        for slot in slots:
            sprint_id = assignments.get(slot)
            if not sprint_id:
                continue
            sprint_id = str(sprint_id)
            if not is_sprint_archived(ph_root=ctx.ph_data_root, sprint_id=sprint_id):
                unarchived_assigned_sprints.append(sprint_id)
        unarchived_assigned_sprints = sorted(set(unarchived_assigned_sprints))

        if unassigned_slots or duplicate_slots or unarchived_assigned_sprints:
            timeline_open = {
                "unassigned_slots": sorted(unassigned_slots),
                "duplicate_slots": dict(sorted(duplicate_slots.items(), key=lambda t: t[0])),
                "unarchived_assigned_sprints": unarchived_assigned_sprints,
            }
        else:
            if slots:
                last_slot = slots[-1]
                candidate = assignments.get(last_slot)
                if candidate:
                    delivered_sprint = str(candidate)
    else:
        sprint_ids_raw = timeline.get("sprint_ids") or []
        if not isinstance(sprint_ids_raw, list):
            sprint_ids_raw = []
        sprint_ids = [str(item).strip() for item in sprint_ids_raw if str(item).strip()]

        unarchived_sprints = [
            sprint_id
            for sprint_id in sprint_ids
            if not is_sprint_archived(ph_root=ctx.ph_data_root, sprint_id=sprint_id)
        ]
        if unarchived_sprints:
            timeline_open = {"unarchived_sprints": unarchived_sprints}
        else:
            delivered_sprint = sprint_ids[-1] if sprint_ids else None

    def _release_values(task: dict[str, Any]) -> list[str]:
        value = task.get("release")
        if isinstance(value, str):
            return [value.strip()]
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return []

    def _explicitly_matches_version(values: list[str], v: str) -> bool:
        for raw in values:
            if not raw or raw.lower() in {"null", "none"}:
                continue
            if raw.lower() == "current":
                continue
            if normalize_version(raw) == v:
                return True
        return False

    tagged = collect_release_tagged_tasks(ph_root=ctx.ph_data_root, version=version)
    if not is_current:
        filtered: list[dict[str, Any]] = []
        for task in tagged:
            values = _release_values(task)
            if any(v.lower() == "current" for v in values) and not _explicitly_matches_version(values, version):
                continue
            filtered.append(task)
        tagged = filtered

    def _is_gate(task: dict[str, Any]) -> bool:
        return bool(task.get("release_gate") is True) or str(task.get("release_gate", "")).strip().lower() in {
            "true",
            "yes",
            "1",
        }

    incomplete_gates: list[dict[str, Any]] = []
    for task in tagged:
        if not _is_gate(task):
            continue
        status = str(task.get("status", "todo") or "todo").strip().lower()
        if status not in _DONE_STATUSES:
            incomplete_gates.append(task)

    ok = (not timeline_open) and (not incomplete_gates)
    info: dict[str, object] = {
        "version": version,
        "is_current": is_current,
        "timeline_mode": timeline_mode,
        "timeline": timeline,
        "timeline_open": timeline_open,
        "incomplete_gates": incomplete_gates,
        "delivered_sprint": delivered_sprint,
    }
    return ok, info


def _print_release_close_blockers(*, info: dict[str, object], file: TextIO) -> None:
    version = str(info.get("version") or "").strip()
    print("❌ Release close blocked: preflight failed.", file=file)
    print(f"Release: {version}", file=file)

    timeline_open = info.get("timeline_open") if isinstance(info.get("timeline_open"), dict) else {}
    timeline_mode = str(info.get("timeline_mode") or "sprint_ids").strip().lower()
    if timeline_open:
        print("\nTimeline blockers:", file=file)
        print(f"- Mode: {timeline_mode}", file=file)
        if timeline_mode == "sprint_slots":
            unassigned = timeline_open.get("unassigned_slots") or []
            if isinstance(unassigned, list) and unassigned:
                print(f"- Unassigned slot(s): {', '.join(str(s) for s in unassigned)}", file=file)
            duplicates = timeline_open.get("duplicate_slots") or {}
            if isinstance(duplicates, dict) and duplicates:
                for slot in sorted(duplicates.keys(), key=lambda s: int(s) if str(s).isdigit() else str(s)):
                    sprints = duplicates.get(slot) or []
                    if isinstance(sprints, list) and sprints:
                        print(
                            f"- Slot {slot} has multiple sprint assignments: {', '.join(str(s) for s in sprints)}",
                            file=file,
                        )
            unarchived = timeline_open.get("unarchived_assigned_sprints") or []
            if isinstance(unarchived, list) and unarchived:
                print(f"- Unarchived assigned sprint(s): {', '.join(str(s) for s in unarchived)}", file=file)
        else:
            unarchived = timeline_open.get("unarchived_sprints") or []
            if isinstance(unarchived, list) and unarchived:
                print(f"- Unarchived sprint(s): {', '.join(str(s) for s in unarchived)}", file=file)

    incomplete_gates = info.get("incomplete_gates") if isinstance(info.get("incomplete_gates"), list) else []
    if incomplete_gates:
        print("\nGate blockers:", file=file)
        print(f"- Incomplete release gate task(s): {len(incomplete_gates)}", file=file)
        for task in sorted(incomplete_gates, key=lambda t: (str(t.get("sprint") or ""), str(t.get("id") or ""))):
            tid = str(task.get("id") or "TASK-???")
            sprint = str(task.get("sprint") or "SPRINT-???")
            status = str(task.get("status") or "todo").strip().lower()
            directory = str(task.get("directory") or "").strip()
            print(f"  - {tid} ({sprint}) status={status} dir={directory}", file=file)

    print("\nNext commands:", file=file)
    print(f"- ph release status --release {version}", file=file)
    if timeline_open:
        if timeline_mode == "sprint_slots":
            unarchived = timeline_open.get("unarchived_assigned_sprints") or []
            if isinstance(unarchived, list):
                for sprint_id in sorted({str(s) for s in unarchived if str(s)}):
                    print(f"- ph sprint close --sprint {sprint_id}", file=file)
            unassigned = timeline_open.get("unassigned_slots") or []
            if isinstance(unassigned, list) and unassigned:
                for slot in unassigned:
                    print(f"- Assign Slot {slot}: ph sprint plan", file=file)
                    print(
                        f"  then set in sprints/current/plan.md: release: {version}, release_sprint_slot: {slot}",
                        file=file,
                    )
        else:
            unarchived = timeline_open.get("unarchived_sprints") or []
            if isinstance(unarchived, list):
                for sprint_id in [str(s).strip() for s in unarchived if str(s).strip()]:
                    print(f"- ph sprint close --sprint {sprint_id}", file=file)
    if incomplete_gates:
        print(
            "- Complete gate task validations + evidence, then mark gate task(s) done in their archived task.yaml",
            file=file,
        )
    print(f"- Re-run: ph release close --version {version}", file=file)


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

    ok, info = _release_close_preflight(ctx=ctx, version=version)
    if not ok:
        _print_release_close_blockers(info=info, file=sys.stderr)
        return 1
    delivered_sprint = str(info.get("delivered_sprint") or "").strip()
    if not delivered_sprint:
        print(
            "❌ Release close blocked: could not determine delivered sprint from release timeline.",
            file=sys.stderr,
        )
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
    if bool(info.get("is_current")):
        clear_current_release(ph_root=ctx.ph_data_root)
        print(f"⭐ Cleared current release pointer: {version}")
    print("📈 Ready for deployment")

    return 0
