from __future__ import annotations

from typing import Any, TextIO

from .remediation_hints import print_next_commands


def list_subcommands(subparsers_action: Any) -> list[tuple[str, str]]:
    """
    Return (name, help) pairs for an argparse subparsers action, preserving
    argparse insertion order.

    Uses argparse internals (`_choices_actions`) because argparse does not expose
    a stable public API for ordered subcommand help text.
    """
    items: list[tuple[str, str]] = []
    actions = getattr(subparsers_action, "_choices_actions", None)
    if not actions:
        choices = getattr(subparsers_action, "choices", {}) or {}
        for name in choices.keys():
            items.append((str(name), ""))
        return items

    for action in actions:
        name = getattr(action, "dest", None) or getattr(action, "name", None) or ""
        help_text = getattr(action, "help", None) or ""
        name = str(name).strip()
        help_text = str(help_text).strip()
        if name:
            items.append((name, help_text))
    return items


def print_group_overview(
    *,
    prefix: str,
    subcommands: list[tuple[str, str]],
    next_cmds: list[str],
    file: TextIO,
    root_missing_note: str | None = None,
) -> None:
    """
    Print a compact "missing subcommand" UX for group commands (e.g. `ph release`).
    """
    print(f"Usage: {prefix} <subcommand>", file=file)
    print("", file=file)
    print("Subcommands:", file=file)

    if not subcommands:
        print("  (none)", file=file)
    else:
        max_len = max(len(name) for name, _ in subcommands)
        pad = max(10, max_len)
        for name, help_text in subcommands:
            if help_text:
                print(f"  {name:<{pad}}  {help_text}", file=file)
            else:
                print(f"  {name}", file=file)

    if root_missing_note:
        print("", file=file)
        print(str(root_missing_note).rstrip(), file=file)

    print_next_commands(commands=next_cmds, file=file)

