from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ScopeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Context:
    ph_root: Path
    scope: str
    ph_data_root: Path


def resolve_scope(*, cli_scope: str | None) -> str:
    if cli_scope is not None:
        scope = cli_scope
    else:
        scope = os.environ.get("PH_SCOPE") or "project"

    if scope not in {"project", "system"}:
        raise ScopeError(f"Invalid scope: {scope!r} (expected 'project' or 'system')\n")

    return scope


def build_context(*, ph_root: Path, scope: str) -> Context:
    ph_root = ph_root.resolve()
    ph_data_root = ph_root if scope == "project" else (ph_root / ".project-handbook" / "system")

    if scope == "system":
        for forbidden in ("roadmap", "releases"):
            forbidden_path = ph_data_root / forbidden
            if forbidden_path.exists():
                raise ScopeError(
                    "System scope MUST NOT create or operate on roadmap/releases.\n"
                    f"Found forbidden path: {forbidden_path}\n"
                )

    return Context(ph_root=ph_root, scope=scope, ph_data_root=ph_data_root)


def assert_scope_allows_domain(*, ctx: Context, domain: str) -> None:
    if ctx.scope == "system" and domain in {"roadmap", "releases"}:
        raise ScopeError(f"System scope MUST NOT operate on {domain}.\n")
