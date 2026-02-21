from __future__ import annotations

import subprocess


def _usage_line(*cmd: str) -> str:
    result = subprocess.run(["ph", *cmd, "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    first = result.stdout.splitlines()[0].strip()
    assert first
    return first


def test_usage_placeholder_top_level() -> None:
    assert _usage_line() == "usage: ph <options> <command> ..."


def test_usage_placeholder_group_command() -> None:
    assert _usage_line("release") == "usage: ph release <options> <subcommand> ..."


def test_usage_placeholder_leaf_no_positionals() -> None:
    assert _usage_line("init") == "usage: ph init <options>"


def test_usage_placeholder_leaf_optional_positional() -> None:
    assert _usage_line("help") == "usage: ph help <options> [topic]"


def test_usage_placeholder_leaf_remainder_positional() -> None:
    assert _usage_line("evidence", "run") == "usage: ph evidence run <options> cmd ..."

