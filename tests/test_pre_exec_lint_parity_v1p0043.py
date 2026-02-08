from __future__ import annotations

import subprocess
from pathlib import Path


def _write_legacy_like_config(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('{\n  "repo_root": "/tmp"\n}\n', encoding="utf-8")


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_passing_task(ph_root: Path) -> None:
    task_dir = (
        ph_root / ".project-handbook" / "sprints" / "current" / "tasks" / "TASK-001-parity-pre-exec-lint"
    )
    task_dir.mkdir(parents=True, exist_ok=True)

    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Parity task",
                "owner: '@a'",
                "lane: ops",
                "feature: f",
                "decision: ADR-0001",
                "session: task-execution",
                "story_points: 1",
                "depends_on: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "task_id: TASK-001",
                "session: task-execution",
                "feature: f",
                "---",
                "",
                "# TASK-001",
                "",
                "Decision: ADR-0001",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "steps.md").write_text(
        "\n".join(
            [
                "# Steps",
                "",
                "1) Do the thing for TASK-001",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "commands.md").write_text(
        "\n".join(
            [
                "# Commands",
                "",
                "Evidence path: status/evidence/TASK-001/command-output.txt",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "checklist.md").write_text(
        "\n".join(
            [
                "# Checklist",
                "",
                "- [x] TASK-001 complete",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "validation.md").write_text(
        "\n".join(
            [
                "# Validation",
                "",
                "Expected evidence file: status/evidence/TASK-001/secret-scan.txt",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (task_dir / "references.md").write_text(
        "\n".join(
            [
                "# References",
                "",
                "### Decision Context",
                "- **Decision**: ADR-0001",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_pre_exec_lint_stdout_matches_make_pre_exec_lint_preamble(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_passing_task(tmp_path)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "pre-exec", "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph pre-exec lint\n"
        "\n"
        "\n"
        "PRE-EXEC LINT PASSED\n"
    )
    assert result.stdout == expected_stdout
