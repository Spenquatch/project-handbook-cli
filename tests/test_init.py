from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path


def test_init_creates_root_marker_and_is_idempotent(tmp_path: Path) -> None:
    result = subprocess.run(
        ["ph", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "Created: .project-handbook/config.json"

    marker = tmp_path / ".project-handbook" / "config.json"
    assert marker.exists()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data == {
        "handbook_schema_version": 1,
        "requires_ph_version": ">=0.0.1,<0.1.0",
        "repo_root": ".",
    }

    data_root = tmp_path / ".project-handbook"

    assert (data_root / "process" / "checks" / "validation_rules.json").exists()
    assert (data_root / "process" / "automation" / "system_scope_config.json").exists()
    assert (data_root / "process" / "automation" / "reset_spec.json").exists()
    assert (data_root / "process" / "sessions" / "templates").exists()
    templates_dir = data_root / "process" / "sessions" / "templates"
    for name in [
        "sprint-planning",
        "task-execution",
        "research-discovery",
        "research-planning",
        "task-docs-deep-dive",
        "pre-execution-audit",
        "quality-gate",
        "release-planning",
        "sprint-closing",
    ]:
        assert (templates_dir / f"{name}.md").exists()
    assert (data_root / "process" / "playbooks").exists()
    assert (data_root / "process" / "AI_AGENT_START_HERE.md").exists()
    assert (data_root / "process" / "sessions" / "logs" / "latest_summary.md").exists()
    assert (data_root / "process" / "sessions" / "session_end" / "session_end_index.json").exists()
    assert (data_root / "ONBOARDING.md").exists()

    assert (data_root / ".gitkeep").exists()
    assert (data_root / "adr").exists()
    assert (data_root / "assets" / ".gitkeep").exists()
    assert (data_root / "backlog" / "bugs").exists()
    assert (data_root / "backlog" / "index.json").exists()
    assert (data_root / "features" / "implemented").exists()
    assert (data_root / "releases").exists()
    assert (data_root / "roadmap" / "now-next-later.md").exists()
    assert (data_root / "sprints" / "archive").exists()
    assert (data_root / "sprints" / "archive" / "index.json").exists()
    assert (data_root / "status" / "daily").exists()
    assert (data_root / "parking-lot" / "index.json").exists()
    assert (data_root / "docs" / "logs" / ".gitkeep").exists()
    assert (data_root / "tools" / ".gitkeep").exists()

    gitignore_path = tmp_path / ".gitignore"
    assert gitignore_path.exists()
    gitignore_text = gitignore_path.read_text(encoding="utf-8")
    assert ".project-handbook/history.log" in gitignore_text

    result2 = subprocess.run(
        ["ph", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0
    assert result2.stdout.strip() == "Already exists: .project-handbook/config.json"

    result_list = subprocess.run(
        ["ph", "onboarding", "session", "list", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result_list.returncode == 0
    assert "  - sprint-planning\n" in result_list.stdout
    assert "  - task-execution\n" in result_list.stdout
    assert "  - research-discovery\n" in result_list.stdout
    assert "  - research-planning\n" in result_list.stdout
    assert "  - task-docs-deep-dive\n" in result_list.stdout
    assert "  - pre-execution-audit\n" in result_list.stdout
    assert "  - quality-gate\n" in result_list.stdout
    assert "  - release-planning\n" in result_list.stdout
    assert "  - sprint-closing\n" in result_list.stdout


def test_init_uses_root_override(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / "target"
    target.mkdir()

    result = subprocess.run(
        ["ph", "--root", str(target), "init"],
        cwd=outside,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (target / ".project-handbook" / "config.json").exists()


def test_init_no_gitignore_flag_does_not_write_gitignore(tmp_path: Path) -> None:
    result = subprocess.run(
        ["ph", "init", "--no-gitignore"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert not (tmp_path / ".gitignore").exists()


def test_init_sprint_plan_is_bounded_by_default(tmp_path: Path) -> None:
    assert subprocess.run(["ph", "init"], cwd=tmp_path, capture_output=True, text=True).returncode == 0

    sprint_id = "SPRINT-2026-W01"
    result = subprocess.run(
        ["ph", "sprint", "plan", "--sprint", sprint_id],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    plan_path = tmp_path / ".project-handbook" / "sprints" / "2026" / sprint_id / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "\nmode: bounded\n" in plan_text
    assert "\nstart:" not in plan_text
    assert "\nend:" not in plan_text
    assert "## Boundaries (Lanes)\n" in plan_text
    assert "## Integration Tasks\n" in plan_text


def test_sprint_plan_defaults_to_bounded_when_rules_omit_sprint_management(tmp_path: Path) -> None:
    assert subprocess.run(["ph", "init"], cwd=tmp_path, capture_output=True, text=True).returncode == 0

    rules_path = tmp_path / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    existing = json.loads(rules_path.read_text(encoding="utf-8"))
    assert "sprint_management" in existing
    without_sprint_management = dict(existing)
    without_sprint_management.pop("sprint_management", None)
    rules_path.write_text(json.dumps(without_sprint_management), encoding="utf-8")

    sprint_id = "SPRINT-2026-W02"
    result = subprocess.run(
        ["ph", "sprint", "plan", "--sprint", sprint_id],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    plan_path = tmp_path / ".project-handbook" / "sprints" / "2026" / sprint_id / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "\nmode: bounded\n" in plan_text
    assert "\nstart:" not in plan_text
    assert "\nend:" not in plan_text


def test_sprint_plan_is_timeboxed_only_when_explicitly_configured(tmp_path: Path) -> None:
    assert subprocess.run(["ph", "init"], cwd=tmp_path, capture_output=True, text=True).returncode == 0

    rules_path = tmp_path / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    sprint_management = rules.get("sprint_management")
    if not isinstance(sprint_management, dict):
        sprint_management = {}
        rules["sprint_management"] = sprint_management
    sprint_management["mode"] = "timeboxed"
    rules_path.write_text(json.dumps(rules), encoding="utf-8")

    sprint_id = "SPRINT-2026-01-05"
    result = subprocess.run(
        ["ph", "sprint", "plan", "--sprint", sprint_id],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    plan_path = tmp_path / ".project-handbook" / "sprints" / "2026" / sprint_id / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "\nmode: timeboxed\n" in plan_text

    start_match = re.search(r"^start: (?P<start>\d{4}-\d{2}-\d{2})$", plan_text, re.MULTILINE)
    end_match = re.search(r"^end: (?P<end>\d{4}-\d{2}-\d{2})$", plan_text, re.MULTILINE)
    assert start_match is not None
    assert end_match is not None
    start_date = dt.datetime.strptime(start_match.group("start"), "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(end_match.group("end"), "%Y-%m-%d").date()
    assert end_date == start_date + dt.timedelta(days=4)
    assert "## Sprint Duration" in plan_text
