from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path, *, validation_rules: str = "{}") -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    ph_data_root = config.parent
    (ph_data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_data_root / "process" / "checks" / "validation_rules.json").write_text(validation_rules, encoding="utf-8")
    (ph_data_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_data_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _read_validation_issues(ph_root: Path) -> list[dict]:
    report_path = ph_root / ".project-handbook" / "status" / "validation.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    issues = data.get("issues")
    assert isinstance(issues, list)
    return issues


def test_validate_quick_passes_with_generated_sprint_plan(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    plan = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0, plan.stdout + "\n" + plan.stderr

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0, res.stdout + "\n" + res.stderr


def test_validate_quick_errors_on_heading_pasted_into_list(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    plan = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0, plan.stdout + "\n" + plan.stderr

    plan_path = tmp_path / ".project-handbook" / "sprints" / "current" / "plan.md"
    text = plan_path.read_text(encoding="utf-8")
    damaged = text.replace(
        "- List explicit cross-lane integration tasks and their dependencies.",
        "- ## Release Gates (Burn-up)",
        1,
    )
    if damaged == text:
        damaged = text + "\n- ## Release Gates (Burn-up)\n"
    plan_path.write_text(damaged, encoding="utf-8")

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 1, res.stdout + "\n" + res.stderr

    issues = _read_validation_issues(tmp_path)
    assert any(i.get("code") == "sprint_plan_heading_inside_list" for i in issues)


def test_validate_quick_errors_when_required_heading_missing(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    plan = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0, plan.stdout + "\n" + plan.stderr

    plan_path = tmp_path / ".project-handbook" / "sprints" / "current" / "plan.md"
    text = plan_path.read_text(encoding="utf-8")
    text = text.replace("## Integration Tasks\n", "", 1)
    plan_path.write_text(text, encoding="utf-8")

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 1, res.stdout + "\n" + res.stderr

    issues = _read_validation_issues(tmp_path)
    assert any(
        i.get("code") == "sprint_plan_missing_heading" and i.get("expected_heading") == "## Integration Tasks"
        for i in issues
    )
