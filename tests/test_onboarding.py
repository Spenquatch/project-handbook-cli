from __future__ import annotations

import subprocess
from pathlib import Path


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


def test_onboarding_prints_onboarding_md(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    onboarding_path = tmp_path / "ONBOARDING.md"
    onboarding_path.write_text("---\ntitle: Onboarding\n---\n# Hello\n", encoding="utf-8")

    result = subprocess.run(["ph", "onboarding", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == "---\ntitle: Onboarding\n---\n# Hello\n"


def test_onboarding_session_list_sorts_topics(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    templates = tmp_path / "process" / "sessions" / "templates"
    (templates / "b-topic.md").write_text("---\ntitle: B\n---\nB\n", encoding="utf-8")
    (templates / "a-topic.md").write_text("---\ntitle: A\n---\nA\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "onboarding", "session", "list", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == (
        "Available onboarding topics:\n"
        "  - a-topic\n"
        "  - b-topic\n"
        "Special topics:\n"
        "  - continue-session (print the latest session summary)\n"
    )


def test_onboarding_session_renders_template(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    templates = tmp_path / "process" / "sessions" / "templates"
    (templates / "sprint-planning.md").write_text("---\ntitle: Sprint\n---\n# Sprint\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "onboarding", "session", "sprint-planning", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "---\ntitle: Sprint\n---\n# Sprint\n"


def test_onboarding_continue_session_missing_has_remediation(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "onboarding", "session", "continue-session", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ph end-session" in result.stderr


def test_onboarding_unknown_session_topic_has_remediation(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "onboarding", "session", "nope", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ph onboarding session list" in result.stderr
