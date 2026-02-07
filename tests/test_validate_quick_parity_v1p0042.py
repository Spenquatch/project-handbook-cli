from __future__ import annotations

import subprocess
from pathlib import Path


def _write_legacy_like_config(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('{\n  "repo_root": "/tmp"\n}\n', encoding="utf-8")


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_minimal_validation_rules(ph_root: Path) -> None:
    rules_path = ph_root / "process" / "checks" / "validation_rules.json"
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text("{}", encoding="utf-8")


def test_validate_quick_stdout_and_report_match_make_validate_quick(tmp_path: Path) -> None:
    _write_legacy_like_config(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    _write_minimal_validation_rules(tmp_path)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "validate", "--quick"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_stdout = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph validate --quick\n"
        "\n"
        f"validation: 0 error(s), 0 warning(s), report: {resolved}/status/validation.json\n"
    )
    assert result.stdout == expected_stdout

    report = tmp_path / "status" / "validation.json"
    assert report.exists()
    assert report.read_text(encoding="utf-8") == '{\n  "issues": []\n}\n'
