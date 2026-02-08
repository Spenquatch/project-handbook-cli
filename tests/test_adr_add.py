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


def test_adr_add_creates_strict_adr_file(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(
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
            "Tribuence Mini v2 (Federated GraphQL + Context Service)",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    rel = ".project-handbook/adr/0007-tribuence-mini-v2-federated-graphql-context-service.md"
    assert result.stdout.strip().endswith(rel)

    path = tmp_path / rel
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    assert "id: ADR-0007" in text
    assert "title: Tribuence Mini v2 (Federated GraphQL + Context Service)" in text
    assert "type: adr" in text
    assert "status: draft" in text
    assert "date: 2099-01-01" in text

    for heading in [
        "# Context",
        "# Decision",
        "# Consequences",
        "# Rollout",
        "# Acceptance Criteria",
    ]:
        assert heading in text


def test_adr_add_refuses_to_overwrite_without_force_and_is_idempotent_with_force(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    first = subprocess.run(
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
            "Decision Title",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0
    rel = ".project-handbook/adr/0010-decision-title.md"
    path = tmp_path / rel
    assert path.exists()
    original = path.read_text(encoding="utf-8")

    blocked = subprocess.run(
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
            "Decision Title",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert blocked.returncode != 0
    assert "refusing to overwrite" in (blocked.stdout + blocked.stderr).lower()
    assert path.read_text(encoding="utf-8") == original

    forced = subprocess.run(
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
            "Decision Title",
            "--date",
            "2099-01-02",
            "--force",
        ],
        capture_output=True,
        text=True,
    )
    assert forced.returncode == 0
    assert forced.stdout.strip().endswith(rel)
    assert path.read_text(encoding="utf-8") == original


def test_adr_add_help_hides_force_flag() -> None:
    result = subprocess.run(
        ["ph", "adr", "add", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    combined = (result.stdout + result.stderr).lower()
    assert "--force" not in combined


def test_adr_add_rejects_invalid_id(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-7",
            "--title",
            "Bad id",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "expected adr-nnnn" in (result.stdout + result.stderr).lower()


def test_adr_add_superseded_requires_superseded_by_and_existing_target(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    missing = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0002",
            "--title",
            "Superseded ADR",
            "--status",
            "superseded",
        ],
        capture_output=True,
        text=True,
    )
    assert missing.returncode != 0
    assert "superseded-by" in (missing.stdout + missing.stderr).lower()

    missing_target = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0002",
            "--title",
            "Superseded ADR",
            "--status",
            "superseded",
            "--superseded-by",
            "ADR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert missing_target.returncode != 0
    assert "does not exist" in (missing_target.stdout + missing_target.stderr).lower()

    create_target = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0001",
            "--title",
            "Target ADR",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert create_target.returncode == 0

    ok = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0002",
            "--title",
            "Superseded ADR",
            "--status",
            "superseded",
            "--superseded-by",
            "ADR-0001",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0
    rel = ok.stdout.strip()
    assert rel.startswith(".project-handbook/adr/")
    text = (tmp_path / rel).read_text(encoding="utf-8")
    assert "status: superseded" in text
    assert "superseded_by: ADR-0001" in text
