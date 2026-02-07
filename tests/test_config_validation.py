from __future__ import annotations

import subprocess
from pathlib import Path


def _write_config(ph_root: Path, *, schema: int = 1, requires: str = ">=0.0.1,<0.1.0") -> None:
    marker = ph_root / ".project-handbook" / "config.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        f'{{\n  "handbook_schema_version": {schema},\n  "requires_ph_version": "{requires}",\n  "repo_root": "."\n}}\n',
        encoding="utf-8",
    )


def test_schema_mismatch_exits_nonzero_with_remediation(tmp_path: Path) -> None:
    _write_config(tmp_path, schema=999)
    result = subprocess.run(["ph", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "uv tool install project-handbook" in result.stderr


def test_version_mismatch_exits_nonzero_with_remediation(tmp_path: Path) -> None:
    _write_config(tmp_path, requires=">=9.9.9")
    result = subprocess.run(["ph", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "uv tool install project-handbook" in result.stderr
