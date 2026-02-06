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


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def test_hooks_install_emits_make_output_and_exit_code(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    (tmp_path / ".git" / "hooks").mkdir(parents=True, exist_ok=True)

    # Force quick validation to report errors.
    (tmp_path / "INVALID.md").write_text("# Missing front matter\n", encoding="utf-8")

    result = subprocess.run(["ph", "hooks", "install", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_prefix = (
        "\n"
        f"> project-handbook@0.0.0 ph {resolved}\n"
        "> ph hooks install\n"
        "\n"
        "Git hooks installed!\n"
    )
    assert result.stdout.startswith(expected_prefix)
    assert "validation:" in result.stdout
    assert f"{resolved}/status/validation.json" in result.stdout
