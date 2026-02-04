from __future__ import annotations

import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": "1",\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _expected_help_sprint_stdout(*, resolved: Path) -> bytes:
    return (
        "\n"
        f"> project-handbook@0.0.0 make {resolved}\n"
        "> make -- help sprint\n"
        "\n"
        "Sprint workflow commands\n"
        "  make sprint-plan      - Create a new sprint skeleton (auto-updates sprints/current)\n"
        "  make sprint-open      - Switch sprints/current to an existing sprint\n"
        "  make sprint-status    - Show day-of-sprint, health, and next suggested task\n"
        "  make sprint-tasks     - List every task under the active sprint\n"
        "  make burndown         - Generate an ASCII burndown chart and save to sprint dir\n"
        "  make sprint-close     - Produce retrospective, archive sprint, summarize velocity\n"
        "  make sprint-capacity  - Display sprint telemetry (points + lanes; not a scope cap)\n"
        "  make sprint-archive   - Manually archive a specific sprint (reruns only)\n"
    ).encode()


def _expected_help_task_stdout(*, resolved: Path) -> bytes:
    return (
        "\n"
        f"> project-handbook@0.0.0 make {resolved}\n"
        "> make -- help task\n"
        "\n"
        "Task workflow commands\n"
        "  make task-create title='X' feature=foo decision=ADR-001 [points=5] [owner=@alice] "
        "[lane=handbook/automation] [release=current|vX.Y.Z] [gate=true]\n"
        "                        - Scaffold a new sprint task directory with docs/checklists\n"
        "  make task-list        - Show all tasks in the current sprint\n"
        "  make task-show id=TASK-### - Print task metadata + file locations\n"
        "  make task-status id=TASK-### status=doing [force=true]\n"
        "                        - Update status with dependency validation\n"
    ).encode()


def test_help_stdout_matches_legacy_make_help(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "--root", str(tmp_path)], capture_output=True)
    assert result.returncode == 0
    expected = (
        "Project Handbook quick help\n"
        "\n"
        "Most-used flows:\n"
        "  • Daily briefing          : make daily | make onboarding session continue-session\n"
        "  • Sprint lifecycle        : make sprint-plan / sprint-status / sprint-close\n"
        "  • Task execution          : make task-create / task-status\n"
        "  • Feature + release work  : make feature-create / release-plan\n"
        "  • Validation & status     : make validate-quick | make status\n"
        "\n"
        "Need the full command list for a workflow?\n"
        "  make help sprint      # sprint planning & health\n"
        "  make help task        # sprint tasks\n"
        "  make help feature     # feature lifecycle\n"
        "  make help release     # release coordination\n"
        "  make help backlog     # issue backlog & triage\n"
        "  make help parking     # parking lot ideas\n"
        "  make help validation  # validation / status / test\n"
        "  make help utilities   # daily tools, onboarding, cleanup\n"
        "\n"
        "Tip: most workflows print next-step guidance after they run.\n"
    ).encode()
    assert result.stdout == expected


def test_help_sprint_stdout_matches_legacy_pnpm_make_help_sprint(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()
    result = subprocess.run(["ph", "help", "sprint", "--root", str(tmp_path)], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_sprint_stdout(resolved=resolved)
    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    assert history_log.stat().st_size > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_sprint_accepts_root_before_command(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()
    result = subprocess.run(["ph", "--root", str(tmp_path), "help", "sprint"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_sprint_stdout(resolved=resolved)
    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    assert history_log.stat().st_size > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_task_stdout_matches_legacy_pnpm_make_help_task(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()
    result = subprocess.run(["ph", "--root", str(tmp_path), "help", "task"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_task_stdout(resolved=resolved)
    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    assert history_log.stat().st_size > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_topics_exist(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    for topic in ("sprint", "task", "feature", "release", "backlog", "parking", "validation", "utilities", "roadmap"):
        result = subprocess.run(["ph", "help", topic, "--root", str(tmp_path)], capture_output=True, text=True)
        assert result.returncode == 0, (topic, result.returncode, result.stdout, result.stderr)


def test_help_unknown_topic_exits_non_zero(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "nope", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
