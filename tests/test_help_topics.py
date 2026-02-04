from __future__ import annotations

import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": "1",\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def test_help_stdout_matches_legacy_make_help(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "--root", str(tmp_path)], capture_output=True)
    assert result.returncode == 0
    expected = (
        "Project Handbook quick help\n"
        "\n"
        "Most-used flows:\n"
        "  • Daily briefing          : make daily | make onboarding session continue-session\n"
        "  • Sprint lifecycle        : make sprint-plan / sprint-status / sprint-close\n"
        "  • Task execution          : make task-create / task-status\n"
        "  • Feature + release work  : make feature-create / release-plan\n"
        "  • Validation & status     : make validate-quick | make status\n"
        "\n"
        "Need the full command list for a workflow?\n"
        "  make help sprint      # sprint planning & health\n"
        "  make help task        # sprint tasks\n"
        "  make help feature     # feature lifecycle\n"
        "  make help release     # release coordination\n"
        "  make help backlog     # issue backlog & triage\n"
        "  make help parking     # parking lot ideas\n"
        "  make help validation  # validation / status / test\n"
        "  make help utilities   # daily tools, onboarding, cleanup\n"
        "\n"
        "Tip: most workflows print next-step guidance after they run.\n"
    ).encode()
    assert result.stdout == expected


def test_help_topics_exist(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    for topic in ("sprint", "task", "feature", "release", "backlog", "parking", "validation", "utilities", "roadmap"):
        result = subprocess.run(["ph", "help", topic, "--root", str(tmp_path)], capture_output=True, text=True)
        assert result.returncode == 0, (topic, result.returncode, result.stdout, result.stderr)


def test_help_unknown_topic_exits_non_zero(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "nope", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
