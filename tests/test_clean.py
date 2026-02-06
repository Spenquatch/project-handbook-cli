from __future__ import annotations

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


def test_clean_removes_pyc_and_pycache(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    pyc = tmp_path / "a.pyc"
    pyc.write_text("x", encoding="utf-8")

    pycache_dir = tmp_path / "pkg" / "__pycache__"
    pycache_dir.mkdir(parents=True, exist_ok=True)
    (pycache_dir / "b.cpython-312.pyc").write_text("x", encoding="utf-8")

    result = subprocess.run(["ph", "clean", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == "Cleaned Python cache files\n"
    assert not pyc.exists()
    assert not pycache_dir.exists()
