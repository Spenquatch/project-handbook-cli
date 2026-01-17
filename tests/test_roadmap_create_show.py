from __future__ import annotations

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

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_roadmap_show_missing_then_create_and_show(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)

    show_missing = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert show_missing.returncode == 1
    assert show_missing.stdout.strip() == "❌ No roadmap found. Run 'ph roadmap create' to create one."

    create = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "create"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert create.returncode == 0

    roadmap_path = tmp_path / "roadmap" / "now-next-later.md"
    assert roadmap_path.exists()
    assert roadmap_path.read_text(encoding="utf-8").startswith("---")

    lines = roadmap_path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    for line in lines:
        updated.append(line)
        if line == "## Now":
            updated.append("- now-item")
        elif line == "## Next":
            updated.append("- next-item")
        elif line == "## Later":
            updated.append("- later-item")
    roadmap_path.write_text("\n".join(updated) + "\n", encoding="utf-8")

    show = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert show.returncode == 0
    assert "🗺️  PROJECT ROADMAP" in show.stdout
    assert "\n🎯 NOW (Current Sprint)" in show.stdout
    assert "\n⏭️  NEXT (1-2 Sprints)" in show.stdout
    assert "\n🔮 LATER (3+ Sprints)" in show.stdout


def test_roadmap_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "roadmap", "show"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Roadmap is project-scope only. Use: ph --scope project roadmap ..."
