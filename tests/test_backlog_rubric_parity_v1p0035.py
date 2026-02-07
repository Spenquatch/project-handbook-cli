from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_RUBRIC = (
    "\n📏 ISSUE SEVERITY RUBRIC\n"
    "================================================================================\n"
    "\n"
    "🔴 P0 - Critical\n"
    "----------------------------------------\n"
    "Action: Always interrupts current sprint\n"
    "\n"
    "Criteria:\n"
    "  • Production outage affecting >50% of users\n"
    "  • Active security exploit\n"
    "  • Data loss or corruption\n"
    "  • Complete feature failure in production\n"
    "\n"
    "🟠 P1 - High\n"
    "----------------------------------------\n"
    "Action: Addressed in next sprint\n"
    "\n"
    "Criteria:\n"
    "  • Service degradation affecting 10-50% of users\n"
    "  • Major feature broken but workaround exists\n"
    "  • Security vulnerability (not actively exploited)\n"
    "  • Significant performance degradation\n"
    "\n"
    "🟡 P2 - Medium\n"
    "----------------------------------------\n"
    "Action: Queued in backlog\n"
    "\n"
    "Criteria:\n"
    "  • Issue affecting <10% of users\n"
    "  • Minor feature malfunction\n"
    "  • UI/UX issues with moderate impact\n"
    "  • Non-critical performance issues\n"
    "\n"
    "🟢 P3 - Low\n"
    "----------------------------------------\n"
    "Action: Backlog queue, low priority\n"
    "\n"
    "Criteria:\n"
    "  • Cosmetic issues\n"
    "  • Developer experience improvements\n"
    "  • Documentation gaps\n"
    "  • Nice-to-have enhancements\n"
    "\n"
    "⚪ P4 - Wishlist\n"
    "----------------------------------------\n"
    "Action: Consider for parking lot\n"
    "\n"
    "Criteria:\n"
    "  • Future enhancements\n"
    "  • Experimental features\n"
    "  • Long-term improvements\n"
    "\n"
    "================================================================================\n"
    "\n"
    "💡 Guidelines:\n"
    "  • P0 issues ALWAYS interrupt the current sprint\n"
    "  • P1 issues are addressed in the next sprint\n"
    "  • P2-P3 issues queue in the backlog\n"
    "  • P4 issues are candidates for the parking lot\n"
    "  • Use 'ph backlog triage' for P0 decision support\n"
)


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
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
def test_backlog_rubric_stdout_matches_legacy_v1p0035(tmp_path: Path, scope: str) -> None:
    _write_minimal_ph_root(tmp_path)

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
        expected = _RUBRIC
    else:
        expected_root = tmp_path.resolve()
        expected = (
            f"\n> project-handbook@0.0.0 ph {expected_root}\n> ph backlog rubric\n\n" + _RUBRIC
        )

    cmd += ["--no-post-hook", "backlog", "rubric"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert result.stdout == expected
