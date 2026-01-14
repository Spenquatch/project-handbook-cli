from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ph", description="Project Handbook CLI")
    subparsers = parser.add_subparsers(dest="command")

    version_parser = subparsers.add_parser("version", help="Print installed ph version")
    version_parser.set_defaults(_handler=_handle_version)
    return parser


def _handle_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "_handler", None)
    if handler is not None:
        return handler(args)

    if args.command is None:
        parser.print_help()
    return 0
