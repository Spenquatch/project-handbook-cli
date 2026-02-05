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

    (ph_root / "package.json").write_text(
        "{\n"
        '  "name": "project-handbook",\n'
        '  "private": true,\n'
        '  "version": "0.0.0",\n'
        '  "scripts": { "make": "make" }\n'
        "}\n",
        encoding="utf-8",
    )


def test_roadmap_validate_stdout_matches_legacy_when_pnpm_reporter_silent(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    (tmp_path / "valid.md").write_text("ok\n", encoding="utf-8")

    roadmap_path = tmp_path / "roadmap" / "now-next-later.md"
    roadmap_path.parent.mkdir(parents=True, exist_ok=True)
    roadmap_path.write_text("- [Valid](../valid.md)\n", encoding="utf-8")

    env = dict(os.environ)
    env["npm_config_reporter"] = "silent"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "roadmap", "validate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout == "✅ Roadmap validation passed\n"

