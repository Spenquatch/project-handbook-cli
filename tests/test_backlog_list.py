from __future__ import annotations

import json
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


def _add_two_issues(*, ph_root: Path, scope: str, env: dict[str, str]) -> tuple[str, str]:
    bug_id = "BUG-P1-20990101-090000"
    work_id = "WORK-P3-20990101-090000"

    base = ["ph", "--root", str(ph_root)]
    if scope == "system":
        base += ["--scope", "system"]

    for args in (
        [
            "--no-post-hook",
            "backlog",
            "add",
            "--type",
            "bug",
            "--title",
            "Bug",
            "--severity",
            "P1",
            "--desc",
            "D",
        ],
        [
            "--no-post-hook",
            "backlog",
            "add",
            "--type",
            "work-items",
            "--title",
            "Work",
            "--severity",
            "P3",
            "--desc",
            "D",
        ],
    ):
        result = subprocess.run(base + args, capture_output=True, text=True, env=env)
        assert result.returncode == 0

    return bug_id, work_id


def test_backlog_list_json_and_filters_project(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    bug_id, work_id = _add_two_issues(ph_root=tmp_path, scope="project", env=env)

    json_result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "list", "--format", "json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert json_result.returncode == 0
    parsed = json.loads(json_result.stdout)
    assert parsed["total_items"] == 2

    severity_result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "list", "--severity", "P1"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert severity_result.returncode == 0
    assert bug_id in severity_result.stdout
    assert work_id not in severity_result.stdout

    category_result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "backlog", "list", "--category", "work-items"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert category_result.returncode == 0
    assert work_id in category_result.stdout
    assert bug_id not in category_result.stdout


def test_backlog_list_filter_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2099-01-01"

    bug_id, work_id = _add_two_issues(ph_root=tmp_path, scope="system", env=env)

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "backlog",
            "list",
            "--category",
            "work-items",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert work_id in result.stdout
    assert bug_id not in result.stdout
