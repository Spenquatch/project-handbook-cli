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


def test_dr_add_creates_strict_dr_file(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0007",
            "--title",
            "Cosmo / MinIO Baseline Topology",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    rel = ".project-handbook/decision-register/DR-0007-cosmo-minio-baseline-topology.md"
    assert result.stdout.strip().endswith(rel)

    path = tmp_path / rel
    assert path.exists()
    text = path.read_text(encoding="utf-8")

    assert "title: DR-0007 — Cosmo / MinIO Baseline Topology" in text
    assert "type: decision-register" in text
    assert "date: 2099-01-01" in text
    assert "tags: [decision-register]" in text
    assert "links: []" in text

    assert "# Decision Register Entry" in text
    assert "### DR-0007 — Cosmo / MinIO Baseline Topology" in text
    for marker in [
        "**Problem / Context**",
        "**Option A — <name>**",
        "**Option B — <name>**",
        "**Recommendation**",
        "**Follow-up tasks (explicit)**",
    ]:
        assert marker in text


def test_dr_add_feature_scoped_writes_under_feature_decision_register(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / ".project-handbook" / "features" / "alpha").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0010",
            "--title",
            "Decision Title",
            "--feature",
            "alpha",
            "--date",
            "2099-01-02",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    rel = ".project-handbook/features/alpha/decision-register/DR-0010-decision-title.md"
    assert result.stdout.strip().endswith(rel)
    assert (tmp_path / rel).exists()


def test_dr_add_refuses_to_overwrite_without_force_and_is_idempotent_with_force(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    first = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0011",
            "--title",
            "Decision Title",
            "--date",
            "2099-01-03",
        ],
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0

    rel = ".project-handbook/decision-register/DR-0011-decision-title.md"
    path = tmp_path / rel
    assert path.exists()
    original = path.read_text(encoding="utf-8")

    blocked = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0011",
            "--title",
            "Decision Title",
            "--date",
            "2099-01-03",
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
            "dr",
            "add",
            "--id",
            "DR-0011",
            "--title",
            "Decision Title",
            "--date",
            "2099-01-03",
            "--force",
        ],
        capture_output=True,
        text=True,
    )
    assert forced.returncode == 0
    assert forced.stdout.strip().endswith(rel)
    assert path.read_text(encoding="utf-8") == original


def test_dr_add_help_hides_force_flag() -> None:
    result = subprocess.run(
        ["ph", "dr", "add", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    combined = (result.stdout + result.stderr).lower()
    assert "--force" not in combined


def test_dr_add_rejects_invalid_id(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-7",
            "--title",
            "Bad id",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "expected dr-nnnn" in (result.stdout + result.stderr).lower()


def test_dr_add_feature_requires_existing_feature_dir(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
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
            "Title",
            "--feature",
            "missing",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "feature does not exist" in (result.stdout + result.stderr).lower()


def test_dr_add_produces_file_that_passes_validate_quick(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    created = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "dr",
            "add",
            "--id",
            "DR-0002",
            "--title",
            "Validate Me",
            "--date",
            "2099-01-01",
        ],
        capture_output=True,
        text=True,
    )
    assert created.returncode == 0

    validate = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "validate",
            "--quick",
        ],
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0
