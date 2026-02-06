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


def test_release_list_parity_v1p0059_exact_output(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    releases_dir = tmp_path / "releases"
    for version in ["v0.6.0", "v0.5.2", "v0.5.1", "v0.5.0", "v0.4.1", "v0.4.0", "v0.3.0"]:
        (releases_dir / version).mkdir(parents=True, exist_ok=True)
    (releases_dir / "current").symlink_to("v0.6.0")

    env = dict(os.environ)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "list"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert (
        result.stdout
        == "📦 RELEASES\n"
        "  v0.3.0\n"
        "  v0.4.0\n"
        "  v0.4.1\n"
        "  v0.5.0\n"
        "  v0.5.1\n"
        "  v0.5.2\n"
        "  v0.6.0 (current)\n"
    )

