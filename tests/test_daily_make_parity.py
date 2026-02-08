from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_legacy_like_config(ph_root: Path) -> None:
    # Legacy handbook repos may have only repo_root (and it may be absolute).
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "repo_root": "/tmp"\n}\n',
        encoding="utf-8",
    )


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_sprint_with_done_tasks(ph_root: Path) -> None:
    sprint_dir = ph_root / ".project-handbook" / "sprints" / "SEQ" / "SPRINT-SEQ-0004"
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # 10 done tasks totaling 28 points.
    points = [3, 3, 3, 3, 3, 3, 3, 3, 2, 2]
    for i, pts in enumerate(points, start=1):
        task_id = f"TASK-{i:03d}"
        task_dir = tasks_dir / f"{task_id}-example"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "task.yaml").write_text(
            "\n".join(
                [
                    f"id: {task_id}",
                    f"title: Example {task_id}",
                    "status: done",
                    f"story_points: {pts}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    current_link = ph_root / ".project-handbook" / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(sprint_dir)


def _write_backlog_index(ph_root: Path) -> None:
    backlog = ph_root / ".project-handbook" / "backlog"
    backlog.mkdir(parents=True, exist_ok=True)
    (backlog / "index.json").write_text(
        '{\n  "items": [\n    {"severity": "P1"},\n    {"severity": "P1"}\n  ]\n}\n',
        encoding="utf-8",
    )

EXPECTED_DAILY_STATUS_2026_02_04 = (
    "---\n"
    "title: Daily Status - 2026-02-04\n"
    "type: status-daily\n"
    "date: 2026-02-04\n"
    "sprint: SPRINT-SEQ-0004\n"
    "tags: [status, daily]\n"
    "links: [../../../sprints/current.md]\n"
    "---\n"
    "\n"
    "# Daily Status - Wednesday, February 04, 2026\n"
    "\n"
    "## Sprint: SPRINT-SEQ-0004\n"
    "**Weekday**: Wednesday (daily status is date-based; sprint planning may be bounded)\n"
    "\n"
    "## Progress\n"
    "- [ ] No tasks currently in progress\n"
    "\n"
    "## Completed Today\n"
    "- [ ] (Update with completed tasks)\n"
    "\n"
    "## Blockers\n"
    "- None\n"
    "\n"
    "## Backlog Impact\n"
    "- P1 Issues: 2 high priority for next sprint\n"
    "- New issues discovered: (Update if any)\n"
    "\n"
    "## Decisions\n"
    "- (Document any technical decisions made today)\n"
    "\n"
    "## Next Focus\n"
    "- Continue current work\n"
    "\n"
    "## Sprint Telemetry\n"
    "- Total Points: 28\n"
    "- Completed: 28\n"
    "- In Progress: 0\n"
    "- Velocity: 28/28 (100%)\n"
)


def test_daily_generate_stdout_and_file_match_make_daily(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_sprint_with_done_tasks(tmp_path)
    _write_backlog_index(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2026-02-04"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "daily", "generate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph daily generate\n"
        "\n"
        f"Created daily status: {resolved}/.project-handbook/status/daily/2026/02/04.md\n"
    )
    assert result.stdout == expected_stdout

    out_path = tmp_path / ".project-handbook" / "status" / "daily" / "2026" / "02" / "04.md"
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == EXPECTED_DAILY_STATUS_2026_02_04


def test_daily_generate_force_stdout_matches_make_daily_force(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_sprint_with_done_tasks(tmp_path)
    _write_backlog_index(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2026-02-04"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "daily", "generate", "--force"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph daily generate --force\n"
        "\n"
        f"Created daily status: {resolved}/.project-handbook/status/daily/2026/02/04.md\n"
    )
    assert result.stdout == expected_stdout

    out_path = tmp_path / ".project-handbook" / "status" / "daily" / "2026" / "02" / "04.md"
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == EXPECTED_DAILY_STATUS_2026_02_04


def test_daily_check_verbose_stdout_matches_make_daily_check(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2026-02-04"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "daily", "check", "--verbose"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 2

    resolved = tmp_path.resolve()
    script = (resolved / ".project-handbook" / "process" / "automation" / "daily_status_check.py").resolve()
    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph daily check --verbose\n"
        "\n"
        "⚠️  No daily status found!\n"
        f"Run: python3 {script} --generate\n"
        "\u2009ELIFECYCLE\u2009 Command failed with exit code 2.\n"
    )
    assert result.stdout == expected_stdout
