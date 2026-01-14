from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "cli_plan" / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_sprint_close_prints_project_hint_block(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    planned = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert planned.returncode == 0

    closed = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert closed.returncode == 0
    assert closed.stdout.splitlines()[-6:] == [
        "Sprint closed! Next steps:",
        "  1. Share the new retrospective and velocity summary",
        "  2. Update roadmap/releases with completed scope",
        "  3. Run 'ph status' so status/current_summary.md reflects the close-out",
        "  4. Kick off the next sprint via 'ph sprint plan' when ready",
        "  5. Capture any loose ends inside parking lot or backlog",
    ]

    archived_dir = tmp_path / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01"
    assert archived_dir.exists()
    assert (archived_dir / "retrospective.md").exists()


def test_sprint_close_does_not_print_hint_block_in_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    planned = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "sprint",
            "plan",
            "--sprint",
            "SPRINT-2099-01-01",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert planned.returncode == 0

    closed = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert closed.returncode == 0
    assert "Sprint closed! Next steps:" not in closed.stdout
