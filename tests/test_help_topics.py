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


def _expected_help_feature_stdout(*, resolved: Path) -> bytes:
    return (
        "\n"
        f"> project-handbook@0.0.0 make {resolved}\n"
        "> make -- help feature\n"
        "\n"
        "Feature management commands\n"
        "  make feature-list             - List features with owner, stage, and links\n"
        "  make feature-create name=foo [epic=true] [owner=@alice]\n"
        "                                - Scaffold architecture/implementation/testing docs\n"
        "  make feature-status name=foo stage=in_progress\n"
        "  make feature-update-status    - Sync status.md files from sprint/task data\n"
        "  make feature-summary          - Aggregate progress for reporting\n"
        "  make feature-archive name=foo [force=true]\n"
        "                                - Completeness check + move to features/implemented/\n"
    ).encode()


def _expected_help_release_stdout(*, resolved: Path) -> bytes:
    return (
        "\n"
        f"> project-handbook@0.0.0 make {resolved}\n"
        "> make -- help release\n"
        "\n"
        "Release coordination commands\n"
        "  make release-plan [version=v1.2.0|version=next] [bump=patch|minor|major] [sprints=3] "
        '[sprint_ids="SPRINT-...,SPRINT-..."] [activate=true]\n'
        "                                - Generate a release plan scaffold (optionally activate)\n"
        "  make release-activate release=v1.2.0\n"
        "                                - Set releases/current to an existing release\n"
        "  make release-clear             - Unset current release pointer\n"
        "  make release-status           - Summaries + health for current release\n"
        "  make release-show             - Print releases/current/plan.md + computed status "
        "(best for sprint planning/closing)\n"
        "  make release-progress         - Refresh releases/current/progress.md "
        "(auto-generated; no need to edit manually)\n"
        "  make release-add-feature release=v1.2.0 feature=auth [epic=true] [critical=true]\n"
        "  make release-suggest version=v1.2.0 - Recommend features based on status data\n"
        "  make release-list             - List every release folder + status\n"
        "  make release-close version=v1.2.0 - Close and document retro notes\n"
    ).encode()


def _expected_help_backlog_stdout(*, resolved: Path) -> bytes:
    return (
        "\n"
        f"> project-handbook@0.0.0 make {resolved}\n"
        "> make -- help backlog\n"
        "\n"
        "Issue backlog + triage commands\n"
        "  make backlog-add type=bug|wildcards|work-items title='X' severity=P1 desc='Y' [owner=@alice]\n"
        "  make backlog-list [severity=P1] [category=ops] [format=table]\n"
        "  make backlog-triage issue=BUG-001 - AI-assisted rubric + action items\n"
        "  make backlog-assign issue=BUG-001 sprint=current\n"
        "  make backlog-rubric            - Print P0-P4 criteria\n"
        "  make backlog-stats             - Metrics grouped by severity/category\n"
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


def test_help_feature_stdout_matches_legacy_pnpm_make_help_feature(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()

    result = subprocess.run(["ph", "--root", str(tmp_path), "help", "feature"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_feature_stdout(resolved=resolved)

    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    first_lines = history_log.read_text(encoding="utf-8").splitlines()
    assert len(first_lines) > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()

    result_2 = subprocess.run(["ph", "--root", str(tmp_path), "help", "feature"], capture_output=True)
    assert result_2.returncode == 0
    second_lines = history_log.read_text(encoding="utf-8").splitlines()
    assert len(second_lines) > len(first_lines)
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_release_stdout_matches_legacy_pnpm_make_help_release(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()

    result = subprocess.run(["ph", "--root", str(tmp_path), "help", "release"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_release_stdout(resolved=resolved)

    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    assert history_log.stat().st_size > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_backlog_stdout_matches_legacy_pnpm_make_help_backlog(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()

    result = subprocess.run(["ph", "--root", str(tmp_path), "help", "backlog"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_backlog_stdout(resolved=resolved)

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
