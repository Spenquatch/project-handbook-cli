from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
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

    (ph_root / "package.json").write_text(
        "{\n"
        '  "name": "project-handbook",\n'
        '  "private": true,\n'
        '  "version": "0.0.0"\n'
        "}\n",
        encoding="utf-8",
    )


def test_roadmap_create_preamble_stdout_and_file_match_legacy(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "create"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    roadmap_path = resolved / "roadmap" / "now-next-later.md"

    expected_stdout = (
        f"\n> project-handbook@0.0.0 ph {resolved}\n"
        "> ph roadmap create\n\n"
        f"📋 Created roadmap template: {roadmap_path}\n"
    )
    assert result.stdout == expected_stdout

    expected_file = (
        "\n".join(
            [
                "---",
                "title: Now / Next / Later Roadmap",
                "type: roadmap",
                "date: 2099-01-01",
                "tags: [roadmap]",
                "links: []",
                "---",
                "",
                "# Project Roadmap",
                "",
                "## Now (Current Sprint)",
                "- feature-1: Brief description [link](../features/feature-1/status.md)",
                "",
                "## Next (1-2 Sprints)",
                "- feature-2: Brief description [link](../features/feature-2/status.md)",
                "",
                "## Later (3+ Sprints)",
                "- feature-3: Future work [link](../features/feature-3/status.md)",
                "",
                "## Completed",
                "- ✅ Initial project setup",
            ]
        )
        + "\n"
    )
    assert roadmap_path.read_text(encoding="utf-8") == expected_file

    roadmap_path.write_text("CHANGED\n", encoding="utf-8")
    result2 = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "create"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result2.returncode == 0
    assert result2.stdout == expected_stdout
    assert roadmap_path.read_text(encoding="utf-8") == expected_file
