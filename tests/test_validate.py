from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


def _write_basic_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / ".project-handbook" / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / ".project-handbook" / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")


def test_validate_project_scope_writes_report_and_silent_success(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "validate", "--quick", "--silent-success", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_validate_system_scope_writes_report_and_silent_success(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "validate", "--quick", "--silent-success", "--scope", "system", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert (tmp_path / ".project-handbook" / "system" / "status" / "validation.json").exists()


def test_validate_flags_task_type_session_mismatch(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    init = subprocess.run(["ph", "init"], cwd=tmp_path, capture_output=True, text=True, env=env)
    assert init.returncode == 0, init.stdout + init.stderr

    sprint = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert sprint.returncode == 0, sprint.stdout + sprint.stderr

    dr = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0001",
            "--title",
            "Decision Title",
            "--date",
            "2099-01-01",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert dr.returncode == 0, dr.stdout + dr.stderr

    created = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "task",
            "create",
            "--title",
            "T",
            "--feature",
            "f",
            "--decision",
            "DR-0001",
            "--type",
            "research-discovery",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert created.returncode == 0, created.stdout + created.stderr

    m = re.search(r"^📁 Location: (?P<path>.+)$", created.stdout, flags=re.MULTILINE)
    assert m is not None, created.stdout
    task_dir = Path(m.group("path"))
    task_yaml_path = task_dir / "task.yaml"
    text = task_yaml_path.read_text(encoding="utf-8")
    assert "task_type: research-discovery\n" in text

    # Session is deprecated but still validated for mismatch if present.
    # Add a session line, then flip task_type to force a mismatch.
    if "session: research-discovery\n" not in text:
        text = text.replace("decision: DR-0001\n", "decision: DR-0001\nsession: research-discovery\n")

    updated = text.replace("task_type: research-discovery\n", "task_type: implementation\n")
    task_yaml_path.write_text(updated, encoding="utf-8")

    validate = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert validate.returncode == 1

    report_path = tmp_path / ".project-handbook" / "status" / "validation.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    issues = report.get("issues", [])
    assert any(
        i.get("code") == "task_type_session_mismatch"
        and i.get("task_type") == "implementation"
        and i.get("expected") == "task-execution"
        and i.get("found") == "research-discovery"
        for i in issues
    ), issues
