from __future__ import annotations

import os
import re
from pathlib import Path

from . import clock
from .context import Context

_SYSTEM_SCOPE_REMEDIATION = "Roadmap is project-scope only. Use: ph --scope project roadmap ..."
_MISSING_ROADMAP_MESSAGE = "❌ No roadmap found. Run 'ph roadmap create' to create one."

def _roadmap_template(*, env: dict[str, str] | None = None) -> str:
    date_text = clock.today(env=env).isoformat()
    return (
        "\n".join(
            [
                "---",
                "title: Now / Next / Later Roadmap",
                "type: roadmap",
                f"date: {date_text}",
                "tags: [roadmap]",
                "links: []",
                "---",
                "",
                "# Project Roadmap",
                "",
                "## Now (Current Sprint)",
                "- feature-1: Brief description [link](../features/feature-1/status.md)",
                "",
                "## Next (1-2 Sprints)",
                "- feature-2: Brief description [link](../features/feature-2/status.md)",
                "",
                "## Later (3+ Sprints)",
                "- feature-3: Future work [link](../features/feature-3/status.md)",
                "",
                "## Completed",
                "- ✅ Initial project setup",
            ]
        )
        + "\n"
    )


def _roadmap_path(*, ph_root: Path) -> Path:
    return ph_root / "roadmap" / "now-next-later.md"


def run_roadmap_create(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    roadmap_path = _roadmap_path(ph_root=ctx.ph_root)
    roadmap_path.parent.mkdir(parents=True, exist_ok=True)
    roadmap_path.write_text(_roadmap_template(env=os.environ), encoding="utf-8")
    print(f"📋 Created roadmap template: {roadmap_path.resolve()}")
    return 0


def run_roadmap_show(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    roadmap_path = _roadmap_path(ph_root=ctx.ph_root)
    if not roadmap_path.exists():
        print(_MISSING_ROADMAP_MESSAGE)
        return 1

    content = roadmap_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    in_now = False
    in_next = False
    in_later = False

    print("🗺️  PROJECT ROADMAP")
    print("=" * 50)

    for line in lines:
        if line.startswith("## Now"):
            print("\n🎯 NOW (Current Sprint)")
            in_now = True
            in_next = in_later = False
        elif line.startswith("## Next"):
            print("\n⏭️  NEXT (1-2 Sprints)")
            in_now = False
            in_next = True
            in_later = False
        elif line.startswith("## Later"):
            print("\n🔮 LATER (3+ Sprints)")
            in_now = in_next = False
            in_later = True
        elif line.startswith("## "):
            in_now = in_next = in_later = False
        elif (in_now or in_next or in_later) and line.startswith("- "):
            print(f"  {line}")

    return 0


def run_roadmap_validate(*, ctx: Context) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    roadmap_path = _roadmap_path(ph_root=ctx.ph_root)
    if not roadmap_path.exists():
        print("❌ No roadmap found")
        return 1

    content = roadmap_path.read_text(encoding="utf-8", errors="ignore")
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

    roadmap_dir = roadmap_path.parent
    ph_root = ctx.ph_root.resolve()

    broken: list[tuple[str, str]] = []
    for text, target in links:
        raw_target = target.strip()
        if not raw_target:
            continue

        target_lower = raw_target.lower()
        if target_lower.startswith(("http://", "https://", "mailto:", "tel:")):
            continue

        normalized = raw_target
        if normalized.startswith("<") and normalized.endswith(">"):
            normalized = normalized[1:-1].strip()
            if not normalized:
                continue

        if normalized.startswith("#"):
            continue

        path_part = normalized.split("#", 1)[0].strip()
        if not path_part:
            continue

        resolved = (roadmap_dir / path_part).resolve()
        if not resolved.is_relative_to(ph_root):
            broken.append((text, raw_target))
            continue

        if not resolved.exists():
            broken.append((text, raw_target))

    if broken:
        print("❌ Roadmap validation failed:")
        for text, target in broken:
            print(f"  - Broken link: {text} -> {target}")
        return 1

    print("✅ Roadmap validation passed")
    return 0
