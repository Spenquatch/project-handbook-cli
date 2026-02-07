from __future__ import annotations

from pathlib import Path

import pytest
from ph.context import ScopeError, assert_scope_allows_domain, build_context, resolve_scope


def test_scope_defaults_to_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PH_SCOPE", raising=False)
    assert resolve_scope(cli_scope=None) == "project"


def test_project_scope_data_root_is_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PH_SCOPE", raising=False)
    scope = resolve_scope(cli_scope=None)
    assert scope == "project"
    ctx = build_context(ph_root=tmp_path, scope=scope)
    assert ctx.ph_data_root == tmp_path.resolve()


def test_system_scope_data_root(tmp_path: Path) -> None:
    ctx = build_context(ph_root=tmp_path, scope="system")
    assert ctx.ph_data_root == (tmp_path / ".project-handbook" / "system").resolve()


def test_system_scope_rejects_roadmap_and_releases(tmp_path: Path) -> None:
    ctx = build_context(ph_root=tmp_path, scope="system")
    with pytest.raises(ScopeError):
        assert_scope_allows_domain(ctx=ctx, domain="roadmap")
    with pytest.raises(ScopeError):
        assert_scope_allows_domain(ctx=ctx, domain="releases")
