from __future__ import annotations

from pathlib import Path

from ph.context import Context
from ph.orchestration import run_check_all, run_test_system


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], bool]] = []

    def run(self, argv: list[str], *, no_post_hook: bool) -> int:
        self.calls.append((list(argv), bool(no_post_hook)))
        return 0


def test_check_all_invocation_sequence(tmp_path: Path) -> None:
    ph_project_root = tmp_path / ".project-handbook"
    ctx = Context(ph_root=tmp_path, scope="project", ph_project_root=ph_project_root, ph_data_root=ph_project_root)
    runner = FakeRunner()

    exit_code = run_check_all(ph_root=tmp_path, ctx=ctx, env={}, runner=runner)
    assert exit_code == 0
    assert runner.calls == [
        (["validate"], True),
        (["status"], True),
    ]


def test_test_system_invocation_sequence(tmp_path: Path) -> None:
    ph_project_root = tmp_path / ".project-handbook"
    ctx = Context(ph_root=tmp_path, scope="project", ph_project_root=ph_project_root, ph_data_root=ph_project_root)
    runner = FakeRunner()

    exit_code = run_test_system(ph_root=tmp_path, ctx=ctx, env={}, runner=runner)
    assert exit_code == 0
    assert runner.calls == [
        (["validate"], True),
        (["status"], True),
        (["daily", "check", "--verbose"], True),
        (["sprint", "status"], True),
        (["feature", "list"], True),
        (["roadmap", "show"], True),
    ]


def test_orchestration_rejects_system_scope(tmp_path: Path, capsys) -> None:
    ph_project_root = tmp_path / ".project-handbook"
    ctx = Context(
        ph_root=tmp_path,
        scope="system",
        ph_project_root=ph_project_root,
        ph_data_root=ph_project_root / "system",
    )
    runner = FakeRunner()

    assert run_check_all(ph_root=tmp_path, ctx=ctx, env={}, runner=runner) == 1
    out = capsys.readouterr().out.strip()
    assert out == "check-all is project-scope only. Use: ph --scope project check-all"
    assert runner.calls == []

    assert run_test_system(ph_root=tmp_path, ctx=ctx, env={}, runner=runner) == 1
    out = capsys.readouterr().out.strip()
    assert out == "test system is project-scope only. Use: ph --scope project test system"
