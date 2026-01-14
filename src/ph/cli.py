from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import ConfigError, load_handbook_config, validate_handbook_config
from .context import ScopeError, build_context, resolve_scope
from .doctor import run_doctor
from .history import append_history, format_history_entry
from .root import RootResolutionError, resolve_ph_root


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="Path to the handbook instance repo root")
    common.add_argument("--scope", choices=["project", "system"], help="Select data scope (default: project)")
    common.add_argument("--no-post-hook", action="store_true", help="Disable post-command hook (history + validate)")
    common.add_argument("--no-history", action="store_true", help="Disable history logging")

    parser = argparse.ArgumentParser(prog="ph", description="Project Handbook CLI", parents=[common])
    subparsers = parser.add_subparsers(dest="command")

    version_parser = subparsers.add_parser("version", help="Print installed ph version", parents=[common])
    version_parser.set_defaults(_handler=_handle_version)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check repo compatibility and required assets",
        parents=[common],
    )
    doctor_parser.set_defaults(_handler=_handle_doctor)
    return parser


def _handle_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    raise RuntimeError("doctor is dispatched by main()")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    invocation_args = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(argv)

    if args.command == "version":
        return _handle_version(args)

    try:
        ph_root = resolve_ph_root(override=args.root)
    except RootResolutionError as exc:
        print(str(exc), file=sys.stderr, end="")
        return 2

    history_enabled = not args.no_post_hook and not args.no_history
    history_entry = format_history_entry(command=args.command, invocation_args=invocation_args)

    if args.command == "doctor":
        result = run_doctor(ph_root)
        stream = sys.stdout if result.exit_code == 0 else sys.stderr
        print(result.output, file=stream, end="")
        if history_enabled:
            append_history(ph_root=ph_root, entry=history_entry)
        return result.exit_code

    exit_code = 0
    try:
        config = load_handbook_config(ph_root)
        validate_handbook_config(config)

        scope = resolve_scope(cli_scope=args.scope)
        _ctx = build_context(ph_root=ph_root, scope=scope)

        if args.command is None:
            parser.print_help()
            exit_code = 0
        else:
            print(f"Unknown command: {args.command}\n", file=sys.stderr, end="")
            exit_code = 2
    except (ConfigError, ScopeError) as exc:
        print(str(exc), file=sys.stderr, end="")
        exit_code = 2

    if history_enabled:
        append_history(ph_root=ph_root, entry=history_entry)

    return exit_code
