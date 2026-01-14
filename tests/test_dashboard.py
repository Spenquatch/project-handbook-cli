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


def _daily_section_lines(stdout: str) -> list[str]:
    lines = stdout.splitlines()
    idx = lines.index("Recent Daily Status:")
    out: list[str] = []
    for line in lines[idx + 1 :]:
        if line == "":
            break
        out.append(line)
    return out


def test_dashboard_banner_matches_project_and_system(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    project = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "dashboard"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert project.returncode == 0
    project_lines = project.stdout.splitlines()
    assert project_lines[:4] == [
        "════════════════════════════════════════════════",
        "           PROJECT HANDBOOK DASHBOARD           ",
        "════════════════════════════════════════════════",
        "",
    ]

    system = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "dashboard"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert system.returncode == 0
    system_lines = system.stdout.splitlines()
    assert system_lines[:4] == [
        "════════════════════════════════════════════════",
        "        PROJECT HANDBOOK DASHBOARD (HB)         ",
        "════════════════════════════════════════════════",
        "",
    ]


def test_dashboard_prints_only_last_three_daily_files(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    daily_dir = tmp_path / "status" / "daily"
    daily_dir.mkdir(parents=True)
    for name in ("2026-01-01.md", "2026-01-02.md", "2026-01-03.md", "2026-01-04.md"):
        (daily_dir / name).write_text("---\ntitle: test\n---\n\n# Daily\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "dashboard"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert result.returncode == 0
    assert _daily_section_lines(result.stdout) == [
        "status/daily/2026-01-02.md",
        "status/daily/2026-01-03.md",
        "status/daily/2026-01-04.md",
    ]


def test_dashboard_prints_empty_daily_message_when_none_exist(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "dashboard"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert result.returncode == 0
    assert _daily_section_lines(result.stdout) == ["  No daily status files yet"]
