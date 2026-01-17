from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
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


@pytest.mark.parametrize("scope", ["project", "system"])
def test_backlog_rubric_prints_expected_header(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "backlog", "rubric"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0
    assert "📏 ISSUE SEVERITY RUBRIC" in result.stdout.splitlines()


def test_backlog_stats_prints_expected_header_and_total(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    for args in (
        ["--type", "bug", "--title", "Bug", "--severity", "P1", "--desc", "D"],
        ["--type", "work-items", "--title", "Work", "--severity", "P3", "--desc", "D"],
    ):
        created = subprocess.run(
            ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "add", *args],
            capture_output=True,
            text=True,
            env=env,
        )
        assert created.returncode == 0

    stats = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "stats"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert stats.returncode == 0
    assert "📊 BACKLOG STATISTICS" in stats.stdout.splitlines()
    assert "Total Issues: 2" in stats.stdout
