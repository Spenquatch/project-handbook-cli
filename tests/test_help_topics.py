from __future__ import annotations

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


def test_help_includes_scope_system_hint(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--scope system" in result.stdout


def test_help_topics_exist(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    for topic in ("sprint", "task", "feature", "release", "backlog", "parking", "validation", "utilities", "roadmap"):
        result = subprocess.run(["ph", "help", topic, "--root", str(tmp_path)], capture_output=True, text=True)
        assert result.returncode == 0, (topic, result.returncode, result.stdout, result.stderr)


def test_help_unknown_topic_exits_non_zero(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "nope", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
