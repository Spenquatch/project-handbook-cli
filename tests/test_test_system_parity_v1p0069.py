from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
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


def _write_minimal_roadmap(ph_root: Path) -> None:
    roadmap_dir = ph_root / "roadmap"
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    roadmap_path = roadmap_dir / "now-next-later.md"
    roadmap_path.write_text(
        "\n".join(
            [
                "---",
                "title: Now / Next / Later Roadmap",
                "type: roadmap",
                "date: 2026-02-04",
                "tags: [roadmap]",
                "links: []",
                "---",
                "",
                "# Project Roadmap",
                "",
                "## Now (Current Sprint)",
                "- feature-a: core",
                "",
                "## Next (1-2 Sprints)",
                "- feature-b: follow-up",
                "",
                "## Later (3+ Sprints)",
                "- feature-c: someday",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_test_system_parity_v1p0069(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_minimal_roadmap(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2026-02-04T09:00:00Z"
    env["PH_FAKE_TODAY"] = "2026-02-04"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "test", "system"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    validation_json = (tmp_path / "status" / "validation.json").resolve()
    current_json = (tmp_path / "status" / "current.json").resolve()
    summary_md = (tmp_path / "status" / "current_summary.md").resolve()
    daily_script = (tmp_path / "process" / "automation" / "daily_status_check.py").resolve()

    expected = (
        f"\n> project-handbook@0.0.0 make {resolved}\n"
        "> make -- test-system\n\n"
        "Testing validation...\n"
        f"validation: 0 error(s), 0 warning(s), report: {validation_json}\n"
        "\n"
        "Testing status generation...\n"
        f"Generated: {current_json}\n"
        f"Updated: {summary_md}\n"
        "\n===== status/current_summary.md =====\n\n"
        "# Current Sprint\n\n_No active sprint_\n"
        "\n====================================\n\n"
        "Updated feature status files\n"
        "\n"
        "Testing daily status check...\n"
        "⚠️  No daily status found!\n"
        f"Run: python3 {daily_script} --generate\n"
        "  (Expected - no daily status yet)\n"
        "\n"
        "Testing sprint status...\n"
        "No active sprint\n"
        "\n"
        "Testing feature management...\n"
        "📁 No features found\n"
        "💡 Create one with: ph feature create --name my-feature\n"
        "\n"
        "Testing roadmap...\n"
        "🗺️  PROJECT ROADMAP\n"
        f"{'=' * 50}\n"
        "\n🎯 NOW (Current Sprint)\n"
        "  - feature-a: core\n"
        "\n⏭️  NEXT (1-2 Sprints)\n"
        "  - feature-b: follow-up\n"
        "\n🔮 LATER (3+ Sprints)\n"
        "  - feature-c: someday\n"
        "\n"
        "✅ All systems operational\n"
    )
    assert result.stdout == expected

    payload = json.loads((tmp_path / "status" / "current.json").read_text(encoding="utf-8"))
    assert payload["generated_at"] == "2026-02-04T09:00:00Z"
