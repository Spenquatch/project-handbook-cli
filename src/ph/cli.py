from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import ConfigError, load_handbook_config, validate_handbook_config
from .context import ScopeError, build_context, resolve_scope
from .doctor import run_doctor
from .root import RootResolutionError, resolve_ph_root


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="Path to the handbook instance repo root")
    common.add_argument("--scope", choices=["project", "system"], help="Select data scope (default: project)")

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
    try:
        ph_root = resolve_ph_root(override=args.root)
    except RootResolutionError as exc:
        print(str(exc), file=sys.stderr, end="")
        return 2

    result = run_doctor(ph_root)
    stream = sys.stdout if result.exit_code == 0 else sys.stderr
    print(result.output, file=stream, end="")
    return result.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "_handler", None)
    if handler is not None:
        return handler(args)

    try:
        ph_root = resolve_ph_root(override=args.root)
    except RootResolutionError as exc:
        print(str(exc), file=sys.stderr, end="")
        return 2

    try:
        config = load_handbook_config(ph_root)
        validate_handbook_config(config)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr, end="")
        return 2

    try:
        scope = resolve_scope(cli_scope=args.scope)
        _ctx = build_context(ph_root=ph_root, scope=scope)
    except ScopeError as exc:
        print(str(exc), file=sys.stderr, end="")
        return 2

    if args.command is None:
        parser.print_help()
    return 0
