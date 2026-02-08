from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    ph_project_root = ph_root / ".project-handbook"
    config = ph_project_root / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_project_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")

    (ph_root / "package.json").write_text(
        "{\n"
        '  "name": "project-handbook",\n'
        '  "private": true,\n'
        '  "version": "0.0.0"\n'
        "}\n",
        encoding="utf-8",
    )


def test_roadmap_show_preamble_and_stdout_match_legacy(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    roadmap_path = tmp_path / ".project-handbook" / "roadmap" / "now-next-later.md"
    roadmap_path.parent.mkdir(parents=True, exist_ok=True)
    roadmap_path.write_text(
        "\n".join(
            [
                "---",
                "title: Now / Next / Later Roadmap",
                "type: roadmap",
                "---",
                "",
                "# Now / Next / Later Roadmap",
                "",
                "## Now",
                "- now-item",
                "",
                "## Next",
                "- next-item",
                "",
                "## Later",
                "- later-item",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_preamble = f"\n> project-handbook@0.0.0 ph {resolved}\n> ph roadmap show\n\n"
    expected_body = (
        "🗺️  PROJECT ROADMAP\n"
        "==================================================\n"
        "\n"
        "🎯 NOW (Current Sprint)\n"
        "  - now-item\n"
        "\n"
        "⏭️  NEXT (1-2 Sprints)\n"
        "  - next-item\n"
        "\n"
        "🔮 LATER (3+ Sprints)\n"
        "  - later-item\n"
    )
    assert result.stdout == expected_preamble + expected_body
