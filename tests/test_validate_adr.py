from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_basic_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    rules_path = ph_root / ".project-handbook" / "process" / "checks" / "validation_rules.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text("{}", encoding="utf-8")


def _run_validate_and_read_report(ph_root: Path) -> tuple[int, dict]:
    result = subprocess.run(
        ["ph", "validate", "--quick", "--root", str(ph_root)],
        capture_output=True,
        text=True,
    )
    report_path = ph_root / ".project-handbook" / "status" / "validation.json"
    assert report_path.exists()
    return result.returncode, json.loads(report_path.read_text(encoding="utf-8"))


def _write_adr(
    path: Path,
    *,
    adr_id: str,
    status: str | None = None,
    superseded_by: str | None = None,
    include_superseded_by_key: bool = True,
    links: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if links is None:
        links = ["decision-register/DR-0000-placeholder.md"]
    front_matter = [
        "---",
        f"id: {adr_id}",
        "title: Test ADR",
        "type: adr",
        f"links: [{', '.join(links)}]" if links else "links: []",
    ]
    if status is not None:
        front_matter.append(f"status: {status}")
    if include_superseded_by_key and superseded_by is not None:
        front_matter.append(f"superseded_by: {superseded_by}")
    elif include_superseded_by_key and superseded_by is None and status is not None:
        front_matter.append("superseded_by: null")

    path.write_text(
        "\n".join(
            [
                *front_matter,
                "---",
                "",
                "# Context",
                "",
                "x",
                "",
                "# Decision",
                "",
                "x",
                "",
                "# Consequences",
                "",
                "x",
                "",
                "# Rollout",
                "",
                "x",
                "",
                "# Acceptance Criteria",
                "",
                "x",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_validate_adr_valid_passes(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    _write_adr(tmp_path / ".project-handbook" / "adr" / "0001-valid-adr.md", adr_id="ADR-0001")

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 0
    assert report == {"issues": []}


def test_validate_adr_missing_rollout_is_warning(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    adr_path = tmp_path / ".project-handbook" / "adr" / "0002-no-rollout.md"
    _write_adr(adr_path, adr_id="ADR-0002")
    text = adr_path.read_text(encoding="utf-8").replace("\n# Rollout\n\nx\n", "\n")
    adr_path.write_text(text, encoding="utf-8")

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 0
    issues = report["issues"]
    assert any(i.get("code") == "adr_missing_recommended_h1" and i.get("severity") == "warning" for i in issues)
    warn = next(i for i in issues if i.get("code") == "adr_missing_recommended_h1")
    assert warn.get("missing") == ["Rollout"]
    assert "expected" not in warn
    assert "found" not in warn


def test_validate_adr_missing_required_h1_is_error(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    adr_path = tmp_path / ".project-handbook" / "adr" / "0003-missing-consequences.md"
    _write_adr(adr_path, adr_id="ADR-0003")
    text = adr_path.read_text(encoding="utf-8").replace("\n# Consequences\n\nx\n", "\n")
    adr_path.write_text(text, encoding="utf-8")

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_missing_required_h1")
    assert err.get("severity") == "error"
    assert err.get("missing") == ["Consequences"]
    assert "found_h1" in err


def test_validate_adr_filename_and_id_mismatch_is_error(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    _write_adr(tmp_path / ".project-handbook" / "adr" / "0002-mismatch.md", adr_id="ADR-0003")

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_filename_id_mismatch")
    assert err.get("severity") == "error"
    assert err.get("expected_id") == "ADR-0002"
    assert err.get("found_id") == "ADR-0003"
    assert err.get("expected_filename_prefix") == "0003"
    assert err.get("found_filename_prefix") == "0002"


def test_validate_adr_filename_invalid_includes_expected_found(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    _write_adr(tmp_path / ".project-handbook" / "adr" / "ADR-0006-bad.md", adr_id="ADR-0006")

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_filename_invalid")
    assert err.get("severity") == "error"
    assert err.get("expected") == "NNNN-<slug>.md"
    assert err.get("found") == "ADR-0006-bad.md"
    assert "expected:" in str(err.get("message", ""))
    assert "found:" in str(err.get("message", ""))


def test_validate_adr_duplicate_id_across_files_is_error_and_mentions_both_paths(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    a = tmp_path / ".project-handbook" / "adr" / "0001-first.md"
    b = tmp_path / ".project-handbook" / "adr" / "0001-second.md"
    _write_adr(a, adr_id="ADR-0001")
    _write_adr(b, adr_id="ADR-0001")

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_duplicate_id")
    assert err.get("severity") == "error"
    assert err.get("id") == "ADR-0001"
    ph_data_root = tmp_path / ".project-handbook"
    assert sorted(err.get("paths", [])) == sorted(
        [
            a.relative_to(ph_data_root).as_posix(),
            b.relative_to(ph_data_root).as_posix(),
        ]
    )

    msg = str(err.get("message", ""))
    assert "ADR-0001" in msg
    assert a.relative_to(ph_data_root).as_posix() in msg
    assert b.relative_to(ph_data_root).as_posix() in msg


def test_validate_adr_superseded_without_superseded_by_is_error_with_actionable_message(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    _write_adr(
        tmp_path / ".project-handbook" / "adr" / "0007-superseded-missing-target.md",
        adr_id="ADR-0007",
        status="superseded",
        superseded_by=None,
        include_superseded_by_key=False,
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_superseded_missing_superseded_by")
    assert err.get("severity") == "error"
    assert err.get("missing") == ["superseded_by"]
    assert err.get("status") == "superseded"
    assert "superseded_by" in str(err.get("message", ""))


def test_validate_adr_superseded_by_missing_target_is_error_with_actionable_message(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    _write_adr(
        tmp_path / ".project-handbook" / "adr" / "0008-superseded-bad-target.md",
        adr_id="ADR-0008",
        status="superseded",
        superseded_by="ADR-9999",
        include_superseded_by_key=True,
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_superseded_by_target_missing")
    assert err.get("severity") == "error"
    assert err.get("superseded_by") == "ADR-9999"
    assert err.get("expected") == {"id": "ADR-9999", "exists": True}
    assert err.get("found") == {"id": "ADR-9999", "exists": False}
    assert "ADR-9999" in str(err.get("message", ""))


def test_validate_adr_requires_dr_backlink(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    _write_adr(tmp_path / ".project-handbook" / "adr" / "0001-valid-adr.md", adr_id="ADR-0001", links=[])

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "adr_missing_dr_backlink")
    assert err.get("severity") == "error"
    assert err.get("path") == "adr/0001-valid-adr.md"


def test_validate_fdr_requires_dr_backlink(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    fdr = tmp_path / ".project-handbook" / "features" / "f" / "fdr" / "0001-test.md"
    fdr.parent.mkdir(parents=True, exist_ok=True)
    fdr.write_text(
        "\n".join(
            [
                "---",
                "id: FDR-0001",
                "title: Test FDR",
                "type: fdr",
                "date: 2099-01-01",
                "links: []",
                "---",
                "",
                "# FDR",
                "",
            ]
        ),
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 1
    err = next(i for i in report["issues"] if i.get("code") == "fdr_missing_dr_backlink")
    assert err.get("severity") == "error"
    assert err.get("path") == "features/f/fdr/0001-test.md"


def test_validate_fdr_with_dr_backlink_passes(tmp_path: Path) -> None:
    _write_basic_ph_root(tmp_path)
    fdr = tmp_path / ".project-handbook" / "features" / "f" / "fdr" / "0001-test.md"
    fdr.parent.mkdir(parents=True, exist_ok=True)
    fdr.write_text(
        "\n".join(
            [
                "---",
                "id: FDR-0001",
                "title: Test FDR",
                "type: fdr",
                "date: 2099-01-01",
                "links: [decision-register/DR-0001-placeholder.md]",
                "---",
                "",
                "# FDR",
                "",
            ]
        ),
        encoding="utf-8",
    )

    code, report = _run_validate_and_read_report(tmp_path)
    assert code == 0
    assert report == {"issues": []}
