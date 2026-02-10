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

    ph_data_root = config.parent
    (ph_data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_data_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_data_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _create_feature(tmp_path: Path, *, name: str) -> None:
    created = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "feature",
            "create",
            "--name",
            name,
        ],
        capture_output=True,
        text=True,
    )
    assert created.returncode == 0, created.stdout + created.stderr


def _create_dr(tmp_path: Path, *, dr_id: str, title: str) -> str:
    created = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            dr_id,
            "--title",
            title,
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    return created.stdout.strip()


def test_fdr_add_creates_feature_scoped_doc_and_passes_validate_quick(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_feature(tmp_path, name="my-feature")
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "fdr",
            "add",
            "--feature",
            "my-feature",
            "--id",
            "FDR-0007",
            "--title",
            "Use Postgres for durable state",
            "--dr",
            "DR-0001",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    rel = ".project-handbook/features/my-feature/fdr/0007-use-postgres-for-durable-state.md"
    assert result.stdout.strip().endswith(rel)

    path = tmp_path / rel
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    assert "id: FDR-0007" in text
    assert "title: Use Postgres for durable state" in text
    assert "type: fdr" in text
    assert "date: 2099-01-02" in text
    assert "decision-register/DR-0001-upstream-decision.md" in text

    for heading in [
        "# Context",
        "# Decision",
        "# Consequences",
        "# Rollout",
        "# Acceptance Criteria",
    ]:
        assert heading in text

    validated = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "validate",
            "--quick",
            "--silent-success",
        ],
        capture_output=True,
        text=True,
    )
    assert validated.returncode == 0, validated.stdout + validated.stderr


def test_fdr_add_links_to_feature_scoped_dr_when_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_feature(tmp_path, name="my-feature")

    created_dr = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0001",
            "--title",
            "Feature DR",
            "--feature",
            "my-feature",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert created_dr.returncode == 0, created_dr.stdout + created_dr.stderr

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "fdr",
            "add",
            "--feature",
            "my-feature",
            "--id",
            "FDR-0001",
            "--title",
            "Uses feature DR",
            "--dr",
            "DR-0001",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    rel = ".project-handbook/features/my-feature/fdr/0001-uses-feature-dr.md"
    path = tmp_path / rel
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "features/my-feature/decision-register/DR-0001-feature-dr.md" in text


def test_fdr_add_fails_when_dr_is_missing(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_feature(tmp_path, name="my-feature")

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "fdr",
            "add",
            "--feature",
            "my-feature",
            "--id",
            "FDR-0001",
            "--title",
            "Missing upstream DR",
            "--dr",
            "DR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "referenced dr does not exist" in combined
    assert "remediation" in combined


def test_fdr_add_rejects_invalid_id(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_feature(tmp_path, name="my-feature")
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "fdr",
            "add",
            "--feature",
            "my-feature",
            "--id",
            "FDR-7",
            "--title",
            "Bad id",
            "--dr",
            "DR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "expected" in (result.stdout + result.stderr).lower()


def test_fdr_add_requires_existing_feature(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "fdr",
            "add",
            "--feature",
            "missing-feature",
            "--id",
            "FDR-0001",
            "--title",
            "Bad feature",
            "--dr",
            "DR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "feature does not exist" in combined
    assert "remediation" in combined
