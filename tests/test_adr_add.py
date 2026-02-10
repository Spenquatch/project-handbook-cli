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


def test_adr_add_creates_strict_adr_file(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")

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
            "--dr",
            "DR-0001",
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
    assert "decision-register/DR-0001-upstream-decision.md" in text

    for heading in [
        "# Context",
        "# Decision",
        "# Consequences",
        "# Rollout",
        "# Acceptance Criteria",
    ]:
        assert heading in text


def test_adr_add_fails_when_dr_is_missing(tmp_path: Path) -> None:
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
            "ADR-0001",
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
    assert "dr-first workflow gate" in combined
    assert "remediation" in combined


def test_adr_add_fails_when_dr_is_ambiguous_across_project_and_feature_scopes(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / ".project-handbook" / "features" / "alpha").mkdir(parents=True, exist_ok=True)
    _create_dr(tmp_path, dr_id="DR-0001", title="Project decision")
    created_feature = subprocess.run(
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
            "Feature decision",
            "--feature",
            "alpha",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert created_feature.returncode == 0, created_feature.stdout + created_feature.stderr

    result = subprocess.run(
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
            "Ambiguous upstream DR",
            "--dr",
            "DR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "ambiguous" in combined
    assert "decision-register/dr-0001-" in combined
    assert "features/alpha/decision-register/dr-0001-" in combined


def test_adr_add_accepts_feature_scoped_dr_and_links_to_it(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / ".project-handbook" / "features" / "alpha").mkdir(parents=True, exist_ok=True)
    created_dr_path = subprocess.run(
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
            "Feature decision",
            "--feature",
            "alpha",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert created_dr_path.returncode == 0, created_dr_path.stdout + created_dr_path.stderr
    assert created_dr_path.stdout.strip().endswith(
        ".project-handbook/features/alpha/decision-register/DR-0001-feature-decision.md"
    )

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "adr",
            "add",
            "--id",
            "ADR-0003",
            "--title",
            "Uses feature DR",
            "--dr",
            "DR-0001",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    rel = ".project-handbook/adr/0003-uses-feature-dr.md"
    path = tmp_path / rel
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "features/alpha/decision-register/DR-0001-feature-decision.md" in text


def test_adr_add_refuses_to_overwrite_without_force_and_is_idempotent_with_force(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")
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
            "--dr",
            "DR-0001",
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
            "--dr",
            "DR-0001",
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
            "--dr",
            "DR-0001",
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
            "--dr",
            "DR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "expected adr-nnnn" in (result.stdout + result.stderr).lower()


def test_adr_add_superseded_requires_superseded_by_and_existing_target(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")

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
            "--dr",
            "DR-0001",
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
            "--dr",
            "DR-0001",
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
            "--dr",
            "DR-0001",
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
            "--dr",
            "DR-0001",
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


def test_adr_add_requires_dr_flag(tmp_path: Path) -> None:
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
            "ADR-0001",
            "--title",
            "Missing DR",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "--dr" in combined
    assert "required" in combined


def test_adr_add_rejects_invalid_dr_id(tmp_path: Path) -> None:
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
            "ADR-0001",
            "--title",
            "Bad DR",
            "--dr",
            "DR-1",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "expected dr-nnnn" in (result.stdout + result.stderr).lower()


def test_adr_add_fails_when_dr_does_not_exist(tmp_path: Path) -> None:
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
            "ADR-0001",
            "--title",
            "Nonexistent DR",
            "--dr",
            "DR-0001",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "dr-first" in combined or "referenced dr" in combined


def test_adr_add_produces_file_that_passes_validate_quick(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _create_dr(tmp_path, dr_id="DR-0001", title="Upstream decision")

    created = subprocess.run(
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
            "Validate Quick",
            "--dr",
            "DR-0001",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert created.returncode == 0, created.stdout + created.stderr

    validate = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr
