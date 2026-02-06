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


def test_roadmap_validate_fails_for_broken_links_then_passes(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    (tmp_path / "valid.md").write_text("ok\n", encoding="utf-8")

    roadmap_path = tmp_path / "roadmap" / "now-next-later.md"
    roadmap_path.parent.mkdir(parents=True, exist_ok=True)
    roadmap_path.write_text(
        "- [Valid](../valid.md)\n- [Broken](../missing.md)\n",
        encoding="utf-8",
    )

    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "validate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "❌ Roadmap validation failed:" in result.stdout
    assert "  - Broken link: Broken -> ../missing.md" in result.stdout

    (tmp_path / "missing.md").write_text("ok\n", encoding="utf-8")

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "validate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "✅ Roadmap validation passed"


def test_roadmap_validate_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "roadmap", "validate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Roadmap is project-scope only. Use: ph --scope project roadmap ..."
