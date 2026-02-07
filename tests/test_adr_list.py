from __future__ import annotations

import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def test_adr_list_prints_id_status_date_title(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    r1 = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0010",
            "--title",
            "Tenth Decision",
            "--status",
            "accepted",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0

    r2 = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0007",
            "--title",
            "Seventh Decision",
            "--status",
            "draft",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "list",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert "ADR-0007 | draft | 2099-01-01 | Seventh Decision" in lines
    assert "ADR-0010 | accepted | 2099-01-02 | Tenth Decision" in lines
    assert lines.index("ADR-0007 | draft | 2099-01-01 | Seventh Decision") < lines.index(
        "ADR-0010 | accepted | 2099-01-02 | Tenth Decision"
    )


def test_adr_list_empty_is_ok(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "list",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No ADRs found." in result.stdout

