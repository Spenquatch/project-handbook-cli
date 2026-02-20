from __future__ import annotations

from typing import TextIO

from .context import Context


def ph_prefix(ctx: Context) -> str:
    if ctx.scope == "system":
        return "ph --scope system"
    return "ph"


def print_next_commands(*, commands: list[str], file: TextIO) -> None:
    if not commands:
        return
    print("\nNext commands:", file=file)
    for command in commands:
        command = str(command).strip()
        if command:
            print(f"- {command}", file=file)


def suggest_sprint_open_commands(*, ctx: Context, limit: int = 3) -> list[str]:
    sprints_root = ctx.ph_data_root / "sprints"
    if not sprints_root.exists():
        return []

    sprint_ids: set[str] = set()
    for entry in sorted(sprints_root.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        if entry.name in {"archive", "current"}:
            continue

        # Some layouts store sprints directly under sprints/, others under sprints/<year>/.
        if entry.name.startswith("SPRINT-"):
            sprint_ids.add(entry.name)
            continue

        for child in sorted(entry.iterdir(), key=lambda p: p.name):
            if child.is_dir() and child.name.startswith("SPRINT-"):
                sprint_ids.add(child.name)

    if not sprint_ids:
        return []

    prefix = ph_prefix(ctx)
    suggested = sorted(sprint_ids, reverse=True)[: max(0, int(limit))]
    return [f"{prefix} sprint open --sprint {sprint_id}" for sprint_id in suggested]


def next_commands_no_active_sprint(*, ctx: Context, extra: list[str] | None = None) -> list[str]:
    prefix = ph_prefix(ctx)
    commands = [f"{prefix} sprint plan", f"{prefix} next"]
    commands.extend(suggest_sprint_open_commands(ctx=ctx))
    if extra:
        commands.extend([str(cmd).strip() for cmd in extra if str(cmd).strip()])
    return commands
