from __future__ import annotations

import datetime as dt
from pathlib import Path

from .clock import today as clock_today
from .context import Context
from .feature_status_updater import calculate_feature_metrics, collect_all_sprint_tasks

_SYSTEM_SCOPE_REMEDIATION = "Releases are project-scope only. Use: ph --scope project release ..."

_PLAN_HINT_LINES = (
    "Release plan saved under releases/current/plan.md",
    "  - Review lanes/dependencies + feature priorities in releases/current/plan.md",
    "  - Confirm sprint alignment via 'ph release status'",
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
    elif current_link.exists():
        current_link.unlink(missing_ok=True)

    available = list_release_versions(ph_root=ph_root)
    if not available:
        return None
    latest = available[-1]
    try:
        current_link.symlink_to(latest)
    except OSError:
        pass
    return latest


def calculate_sprint_range(*, start_sprint: str, sprint_count: int, explicit: list[str] | None = None) -> list[str]:
    if explicit:
        return list(explicit)

    parts = start_sprint.split("-")
    sprint_ids: list[str] = []

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
    sprint_count: int,
    start_sprint: str,
    sprint_ids: list[str] | None,
    env: dict[str, str],
) -> Path:
    if not version.startswith("v"):
        version = f"v{version}"

    releases_dir = ph_root / "releases"
    release_dir = releases_dir / version
    release_dir.mkdir(parents=True, exist_ok=True)

    timeline = calculate_sprint_range(start_sprint=start_sprint, sprint_count=sprint_count, explicit=sprint_ids)
    end_sprint = timeline[-1]
    today = clock_today(env=env).strftime("%Y-%m-%d")

    plan_path = release_dir / "plan.md"
    if not plan_path.exists():
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
*Use `make release-add-feature` to assign features to this release*

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
        features_content = f"""# Feature assignments for {version}
# Auto-managed by release commands

version: {version}
start_sprint: {start_sprint}
end_sprint: {end_sprint}
planned_sprints: {sprint_count}

features:
  # Features will be added with: make release-add-feature
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

        current_active = _resolve_current_sprint_id(ph_root=ph_root, fallback=start_sprint)
        for i, sprint_id in enumerate(timeline, 1):
            status = "✅ Complete" if i == 1 else ("🔄 In Progress" if sprint_id == current_active else "⭕ Planned")
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

    current_link = releases_dir / "current"
    if current_link.exists() or current_link.is_symlink():
        current_link.unlink(missing_ok=True)
    current_link.symlink_to(version)

    return release_dir


def run_release_plan(
    *,
    ctx: Context,
    version: str | None,
    bump: str,
    sprints: int,
    start_sprint: str | None,
    sprint_ids: str | None,
    env: dict[str, str],
) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    raw_version = (version or "next").strip()
    raw_bump = (bump or "patch").strip()

    explicit_sprint_ids = _parse_sprint_ids_csv(sprint_ids)
    if not start_sprint and explicit_sprint_ids:
        start_sprint = explicit_sprint_ids[0]

    sprint_count = int(sprints) if sprints else 3
    if explicit_sprint_ids:
        sprint_count = len(explicit_sprint_ids)

    if start_sprint is None:
        start_sprint = f"SPRINT-{clock_today(env=env):%Y-%m-%d}"

    if raw_version in {"next", "auto"}:
        current = get_current_release(ph_root=ctx.ph_root)
        available = list_release_versions(ph_root=ctx.ph_root)
        base = current or (available[-1] if available else "v0.1.0")
        raw_version = bump_version(base, bump=raw_bump)

    if not raw_version.startswith("v"):
        raw_version = f"v{raw_version}"

    release_dir = _ensure_release_files_exist(
        ph_root=ctx.ph_root,
        version=raw_version,
        sprint_count=sprint_count,
        start_sprint=start_sprint,
        sprint_ids=explicit_sprint_ids,
        env=env,
    )

    print(f"✅ Created release plan: {raw_version}")
    print(f"📁 Location: {release_dir}")
    if explicit_sprint_ids:
        print(f"📅 Timeline: {len(explicit_sprint_ids)} custom sprint(s) → {', '.join(explicit_sprint_ids)}")
    else:
        print(f"📅 Timeline: {sprint_count} sprints starting {start_sprint}")
    print("📝 Next steps:")
    print(f"   1. Edit {release_dir}/plan.md to define release goals")
    print(f"   2. Add features: ph release add-feature --release {raw_version} --feature feature-name")
    print("   3. Review timeline and adjust if needed")
    print()
    for line in _PLAN_HINT_LINES:
        print(line)
    return 0


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
    for feature_name in features.keys():
        tasks = tasks_by_feature.get(feature_name)
        if tasks:
            metrics = calculate_feature_metrics(tasks=tasks, env=env)
            raw = metrics.get("completion_percentage", 0)
            try:
                feature_completions[feature_name] = int(raw)  # type: ignore[arg-type]
            except Exception:
                feature_completions[feature_name] = 0
        else:
            feature_completions[feature_name] = 0

    total_features = len(features)
    completed_features = 0
    total_completion = 0
    critical_path_complete = True

    for feature_name, feature_data in features.items():
        completion = feature_completions.get(feature_name, 0)
        total_completion += completion

        if completion >= 90:
            completed_features += 1

        if bool(feature_data.get("critical_path")) and completion < 90:
            critical_path_complete = False

    avg_completion = total_completion // total_features if total_features > 0 else 0

    if avg_completion >= 90 and critical_path_complete:
        health = "🟢 GREEN - Ready for release"
    elif avg_completion >= 70 and critical_path_complete:
        health = "🟡 YELLOW - On track"
    elif critical_path_complete:
        health = "🟡 YELLOW - Some features behind"
    else:
        health = "🔴 RED - Critical path at risk"

    return {
        "total_features": total_features,
        "completed_features": completed_features,
        "avg_completion": avg_completion,
        "critical_path_complete": critical_path_complete,
        "health": health,
        "feature_completions": feature_completions,
    }


def run_release_list(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    releases_dir = ctx.ph_root / "releases"
    if not releases_dir.exists():
        print("📦 No releases directory")
        return 0

    releases = list_release_versions(ph_root=ctx.ph_root)
    if not releases:
        print("📦 No releases found")
        return 0

    current = _read_current_release_target(ph_root=ctx.ph_root)

    print("📦 RELEASES")
    for release in releases:
        indicator = " (current)" if current and release == current else ""
        print(f"  {release}{indicator}")
    return 0


def run_release_status(*, ctx: Context, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    version = _read_current_release_target(ph_root=ctx.ph_root)
    if not version:
        print("❌ No current release found")
        available = list_release_versions(ph_root=ctx.ph_root)
        if available:
            print("📦 Available releases:")
            for name in available:
                print(f"  • {name}")
            print("💡 Set one active with: ln -s <release> releases/current or re-run ph release plan")
        else:
            print("💡 Create one with: ph release plan --version v1.2.0 --sprints 3")
        return 1

    release_dir = ctx.ph_root / "releases" / version
    if not release_dir.exists():
        print(f"❌ Release {version} not found")
        return 1

    features = load_release_features(ph_root=ctx.ph_root, version=version)
    progress = calculate_release_progress(ph_root=ctx.ph_root, version=version, features=features, env=env)

    plan_file = release_dir / "plan.md"
    sprint_count = 3
    start_sprint = _resolve_current_sprint_id(ph_root=ctx.ph_root, fallback=f"SPRINT-{clock_today(env=env):%Y-%m-%d}")

    plan_meta = parse_plan_front_matter(plan_path=plan_file)
    if plan_meta:
        try:
            sprint_count = int(plan_meta.get("planned_sprints", sprint_count))  # type: ignore[arg-type]
        except Exception:
            pass
        start_sprint = str(plan_meta.get("start_sprint", start_sprint))
        explicit_timeline = plan_meta.get("sprint_ids")
        if isinstance(explicit_timeline, list):
            sprint_timeline = calculate_sprint_range(
                start_sprint=start_sprint,
                sprint_count=len(explicit_timeline),
                explicit=[str(item) for item in explicit_timeline if str(item)],
            )
            sprint_count = len(sprint_timeline)
        else:
            sprint_timeline = calculate_sprint_range(
                start_sprint=start_sprint, sprint_count=sprint_count, explicit=None
            )
    else:
        sprint_timeline = calculate_sprint_range(start_sprint=start_sprint, sprint_count=sprint_count, explicit=None)

    current_sprint = _resolve_current_sprint_id(ph_root=ctx.ph_root, fallback=start_sprint)
    try:
        current_sprint_index = sprint_timeline.index(current_sprint) + 1
    except ValueError:
        current_sprint_index = 1

    print(f"📦 RELEASE STATUS: {version}")
    print("=" * 60)
    print(f"Sprint: {current_sprint_index} of {sprint_count} ({current_sprint})")
    print(f"Overall Progress: {progress.get('avg_completion', 0)}% complete")
    print(f"Target: {sprint_timeline[-1] if sprint_timeline else 'TBD'}")
    print(f"Release Health: {progress.get('health', 'Unknown')}")
    print()

    if features:
        print("🎯 Feature Progress:")
        for feature_name, feature_data in features.items():
            completion = int(progress.get("feature_completions", {}).get(feature_name, 0))
            status_emoji = "✅" if completion >= 90 else ("🔄" if completion > 0 else "⭕")
            critical_indicator = " (Critical Path)" if bool(feature_data.get("critical_path")) else ""
            print(f"{status_emoji} {feature_name:<20} {completion:3d}% complete{critical_indicator}")
        print()

    print("📅 Sprint Breakdown:")
    for i, sprint_id in enumerate(sprint_timeline, 1):
        if sprint_id == current_sprint:
            status = "🔄 In progress"
        elif i < current_sprint_index:
            status = "✅ Complete"
        else:
            status = "⭕ Planned"
        print(f"{status} {sprint_id} (Sprint {i} of {sprint_count})")
    return 0


def _release_features_yaml_path(*, ph_root: Path, version: str) -> Path:
    if not version.startswith("v"):
        version = f"v{version}"
    return ph_root / "releases" / version / "features.yaml"


def _upsert_feature_block(
    *, lines: list[str], feature: str, updates: dict[str, str], insert_if_missing: bool
) -> list[str]:
    if not lines:
        return lines

    try:
        features_start = next(i for i, line in enumerate(lines) if line.strip() == "features:")
    except StopIteration:
        return lines

    feature_headers: list[tuple[str, int]] = []
    for i in range(features_start + 1, len(lines)):
        line = lines[i]
        if line.startswith("  ") and not line.startswith("    ") and ":" in line:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            name = stripped.split(":", 1)[0].strip()
            if name:
                feature_headers.append((name, i))

    block_ranges: dict[str, tuple[int, int]] = {}
    for idx, (name, start_i) in enumerate(feature_headers):
        end_i = feature_headers[idx + 1][1] if idx + 1 < len(feature_headers) else len(lines)
        block_ranges[name] = (start_i, end_i)

    if feature not in block_ranges:
        if not insert_if_missing:
            return lines
        ensured = list(lines)
        ensured.append(f"  {feature}:\n")
        for key, value in updates.items():
            ensured.append(f"    {key}: {value}\n")
        ensured.append("\n")
        return ensured

    start_i, end_i = block_ranges[feature]
    out = list(lines)

    key_line_index: dict[str, int] = {}
    for i in range(start_i + 1, end_i):
        line = out[i]
        if line.startswith("    ") and ":" in line and not line.strip().startswith("#"):
            key = line.strip().split(":", 1)[0].strip()
            if key:
                key_line_index[key] = i

    for key, value in updates.items():
        if key in key_line_index:
            out[key_line_index[key]] = f"    {key}: {value}\n"
        else:
            insert_at = end_i
            while insert_at > start_i and not out[insert_at - 1].strip():
                insert_at -= 1
            out.insert(insert_at, f"    {key}: {value}\n")
            for k, existing_i in list(key_line_index.items()):
                if existing_i >= insert_at:
                    key_line_index[k] = existing_i + 1
            end_i += 1

    return out


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

    features_file = _release_features_yaml_path(ph_root=ctx.ph_root, version=version)
    if not features_file.exists():
        print(f"❌ Release {version} not found. Create with: ph release plan")
        return 1

    feature_type = "epic" if epic else "regular"
    updates = {
        "type": feature_type,
        "priority": "P1",
        "status": "planned",
        "completion": "0",
        "critical_path": "true" if critical else "false",
    }

    existing_lines = features_file.read_text(encoding="utf-8").splitlines(keepends=True)
    updated_lines = _upsert_feature_block(
        lines=existing_lines, feature=feature, updates=updates, insert_if_missing=True
    )
    features_file.write_text("".join(updated_lines), encoding="utf-8")

    print(f"{_ADD_FEATURE_SUCCESS_PREFIX} {feature} to release {version}")
    return 0


def run_release_suggest(*, ctx: Context, version: str) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    print(f"💡 SUGGESTED FEATURES FOR {version}")
    print("=" * 50)

    features_dir = ctx.ph_root / "features"
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

    release_dir = ctx.ph_root / "releases" / version
    if not release_dir.exists():
        print(f"❌ Release {version} not found")
        return 1

    delivered_sprint = _resolve_required_current_sprint_id(ph_root=ctx.ph_root)
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

    features = load_release_features(ph_root=ctx.ph_root, version=version)
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

    delivered_dir = ctx.ph_root / "releases" / "delivered"
    delivered_dir.mkdir(parents=True, exist_ok=True)

    print(f"✅ Release {version} closed")
    print(f"📋 Generated changelog: {release_dir}/changelog.md")
    if plan_file.exists():
        print(f"📝 Updated plan status: {plan_file}")
    print("📈 Ready for deployment")

    return 0
