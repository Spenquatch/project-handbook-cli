from __future__ import annotations

import json
from pathlib import Path

from .clock import today as clock_today
from .context import Context


def _maybe_print_pnpm_make_preamble(*, ctx: Context, make_args: str) -> None:
    package_json_path = ctx.ph_root / "package.json"
    if not package_json_path.exists():
        return

    try:
        package_json = json.loads(package_json_path.read_text(encoding="utf-8"))
    except Exception:
        return

    name = str(package_json.get("name") or "").strip()
    version = str(package_json.get("version") or "").strip()
    if not name or not version:
        return

    print()
    print(f"> {name}@{version} make {ctx.ph_root}")
    print(f"> make -- {make_args}")
    print()


def _feature_name_prefixes_for_system_scope(*, ph_root: Path) -> list[str]:
    config_path = ph_root / "process" / "automation" / "system_scope_config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rules = config.get("routing_rules", {})
    if not isinstance(rules, dict):
        return []
    prefixes = rules.get("feature_name_prefixes_for_system_scope", [])
    if not isinstance(prefixes, list):
        return []
    return [str(p) for p in prefixes if str(p)]


def is_system_scoped_feature(*, ph_root: Path, name: str) -> bool:
    name = str(name)
    return any(name.startswith(prefix) for prefix in _feature_name_prefixes_for_system_scope(ph_root=ph_root))


def _feature_hint_block(*, ctx: Context, name: str) -> list[str]:
    if ctx.scope == "system":
        return [
            f"Next steps for .project-handbook/system/features/{name}/:",
            "  1. Flesh out overview.md + status.md with owner, goals, and risks",
            "  2. Draft architecture/implementation/testing docs before assigning sprint work",
            "  3. Run 'ph --scope system validate --quick' so docs stay lint-clean",
        ]
    return [
        f"Next steps for features/{name}/:",
        "  1. Flesh out overview.md + status.md with owner, goals, and risks",
        "  2. Draft architecture/implementation/testing docs before assigning sprint work",
        "  3. Run 'make validate-quick' so docs stay lint-clean",
    ]


def _ensure_feature_roots(*, ph_data_root: Path) -> tuple[Path, Path]:
    features_dir = ph_data_root / "features"
    implemented_dir = features_dir / "implemented"
    implemented_dir.mkdir(parents=True, exist_ok=True)
    return features_dir, implemented_dir


def run_feature_create(
    *,
    ph_root: Path,
    ctx: Context,
    name: str,
    epic: bool,
    owner: str,
    stage: str,
    env: dict[str, str],
) -> int:
    name = (name or "").strip()
    owner = (owner or "@owner").strip() or "@owner"
    stage = (stage or "proposed").strip() or "proposed"

    if ctx.scope == "project" and is_system_scoped_feature(ph_root=ph_root, name=name):
        print(f"Use: ph --scope system feature create --name {name}")
        return 1

    features_dir, _implemented_dir = _ensure_feature_roots(ph_data_root=ctx.ph_data_root)
    feature_dir = features_dir / name

    if feature_dir.exists():
        print(f"❌ Feature '{name}' already exists")
        return 1

    today = clock_today(env=env)
    today_str = today.strftime("%Y-%m-%d")

    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "architecture").mkdir(exist_ok=True)
    (feature_dir / "implementation").mkdir(exist_ok=True)
    (feature_dir / "testing").mkdir(exist_ok=True)
    (feature_dir / "fdr").mkdir(exist_ok=True)
    (feature_dir / "decision-register").mkdir(exist_ok=True)

    overview_content = f"""---
title: {name.replace("-", " ").title()}
type: overview
feature: {name}
date: {today_str}
tags: [feature]
links: [./architecture/ARCHITECTURE.md, ./implementation/IMPLEMENTATION.md, ./testing/TESTING.md]
dependencies: []
backlog_items: []  # Related P0-P4 issues from backlog
parking_lot_origin: null  # Original parking lot ID if promoted
capacity_impact: planned  # planned (80%) or reactive (20%)
epic: {str(epic).lower()}
---

# {name.replace("-", " ").title()}

## Purpose
Brief description of this feature's value and scope.

## Outcomes
- Key outcome 1
- Key outcome 2

## State
- Stage: {stage}
- Owner: {owner}

## Backlog Integration
- Related Issues: []  # List any P0-P4 items this addresses
- Capacity Type: planned  # Uses 80% allocation
- Parking Lot Origin: null  # Set if promoted from parking lot

## Key Links
- [Architecture](./architecture/ARCHITECTURE.md)
- [Implementation](./implementation/IMPLEMENTATION.md)
- [Testing](./testing/TESTING.md)
- [Status](./status.md)
- [Changelog](./changelog.md)
"""

    (feature_dir / "overview.md").write_text(overview_content, encoding="utf-8")

    files_to_create = {
        "architecture/ARCHITECTURE.md": f"""---
title: {name.replace("-", " ").title()} Architecture
type: architecture
feature: {name}
date: {today_str}
tags: [architecture]
links: []
---

# Architecture: {name.replace("-", " ").title()}

## Overview
High-level architecture description.

## Components
- Component 1: Description
- Component 2: Description

## Data Flow
Describe how data flows through the system.

## Dependencies
- External dependency 1
- External dependency 2
""",
        "implementation/IMPLEMENTATION.md": f"""---
title: {name.replace("-", " ").title()} Implementation
type: implementation
feature: {name}
date: {today_str}
tags: [implementation]
links: []
---

# Implementation: {name.replace("-", " ").title()}

## Development Plan
1. Phase 1: Core functionality
2. Phase 2: Extended features
3. Phase 3: Polish and optimization

## Technical Decisions
- Decision 1: Rationale
- Decision 2: Rationale

## Implementation Notes
Detailed implementation guidance.
""",
        "testing/TESTING.md": f"""---
title: {name.replace("-", " ").title()} Testing
type: testing
feature: {name}
date: {today_str}
tags: [testing]
links: []
---

# Testing: {name.replace("-", " ").title()}

## Test Strategy
- Unit tests: Coverage expectations
- Integration tests: Key scenarios
- E2E tests: User journeys

## Test Cases
1. Test case 1: Description
2. Test case 2: Description

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
""",
        "status.md": f"""---
title: {name.replace("-", " ").title()} Status
type: status
feature: {name}
date: {today_str}
tags: [status]
links: []
---

# Status: {name.replace("-", " ").title()}

Stage: {stage}

## Now
- Planning and initial design

## Next
- Architecture definition
- Implementation start

## Risks
- Risk 1: Description and mitigation
- Risk 2: Description and mitigation

## Recent
- Feature created
""",
        "changelog.md": f"""---
title: {name.replace("-", " ").title()} Changelog
type: changelog
feature: {name}
date: {today_str}
tags: [changelog]
links: []
---

# Changelog: {name.replace("-", " ").title()}

## Unreleased
- Initial feature creation

## [Future Versions]
- To be determined based on implementation progress
""",
        "risks.md": f"""---
title: {name.replace("-", " ").title()} Risks
type: risks
feature: {name}
date: {today_str}
tags: [risks]
links: []
---

# Risk Register: {name.replace("-", " ").title()}

## High Priority Risks
- **Risk 1**: Description
  - Impact: High/Medium/Low
  - Probability: High/Medium/Low
  - Mitigation: Action plan

## Medium Priority Risks
- **Risk 2**: Description
  - Impact: Medium
  - Probability: Medium
  - Mitigation: Action plan

## Risk Mitigation Strategies
- Strategy 1: Description
- Strategy 2: Description
""",
    }

    for relative, content in files_to_create.items():
        (feature_dir / relative).write_text(content, encoding="utf-8")

    epic_note = " (Epic)" if epic else ""
    print(f"✅ Created feature '{name}'{epic_note} with complete directory structure")
    print(f"📁 Location: {feature_dir}")
    print("📝 Next steps:")
    print(f"   1. Edit {feature_dir}/overview.md to define the feature")
    print(f"   2. Update {feature_dir}/status.md with current status")
    if ctx.scope == "system":
        print("   3. Run 'ph --scope system validate' to check structure")
    else:
        print("   3. Run 'make validate' to check structure")

    for line in _feature_hint_block(ctx=ctx, name=name):
        print(line)

    return 0


def run_feature_list(*, ctx: Context, with_preamble: bool = True) -> int:
    if with_preamble:
        _maybe_print_pnpm_make_preamble(ctx=ctx, make_args="feature-list")

    features_dir, _implemented_dir = _ensure_feature_roots(ph_data_root=ctx.ph_data_root)
    feature_dirs = [d for d in features_dir.iterdir() if d.is_dir() and d.name != "implemented"]

    if not feature_dirs:
        print("📁 No features found")
        print("💡 Create one with: ph feature create --name my-feature")
        return 0

    print("📋 FEATURES OVERVIEW")
    print("=" * 60)

    for feature_dir in sorted(feature_dirs):
        name = feature_dir.name
        status_file = feature_dir / "status.md"
        overview_file = feature_dir / "overview.md"

        stage = "unknown"
        if status_file.exists():
            try:
                content = status_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("Stage:"):
                        stage = line.split(":", 1)[1].strip()
                        break
            except Exception:
                pass

        epic = False
        if overview_file.exists():
            try:
                content = overview_file.read_text(encoding="utf-8")
                if "epic: true" in content.lower():
                    epic = True
            except Exception:
                pass

        epic_indicator = "🎯" if epic else "📦"
        print(f"{epic_indicator} {name:<25} Stage: {stage}")

    return 0


def run_feature_status(*, ctx: Context, name: str, stage: str, env: dict[str, str]) -> int:
    name = (name or "").strip()
    stage = (stage or "").strip()

    status_file = ctx.ph_data_root / "features" / name / "status.md"
    if not status_file.exists():
        print(f"❌ Feature '{name}' not found")
        return 1

    today_str = clock_today(env=env).strftime("%Y-%m-%d")

    content = status_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    for idx, line in enumerate(lines):
        if line.startswith("Stage:"):
            lines[idx] = f"Stage: {stage}"
            break

    for idx, line in enumerate(lines):
        if line.startswith("date:"):
            lines[idx] = f"date: {today_str}"
            break

    status_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Updated '{name}' stage to '{stage}'")
    return 0
