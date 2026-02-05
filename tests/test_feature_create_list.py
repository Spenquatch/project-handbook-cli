from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


def _write_minimal_ph_root(ph_root: Path, *, routing_rules: dict | None = None) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    system_scope_config = {"routing_rules": routing_rules or {}}
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        json.dumps(system_scope_config), encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


@pytest.mark.parametrize(
    ("scope", "hint_lines"),
    [
        (
            "project",
            [
                "Next steps for features/feat-a/:",
                "  1. Flesh out overview.md + status.md with owner, goals, and risks",
                "  2. Draft architecture/implementation/testing docs before assigning sprint work",
                "  3. Run 'make validate-quick' so docs stay lint-clean",
            ],
        ),
        (
            "system",
            [
                "Next steps for .project-handbook/system/features/feat-a/:",
                "  1. Flesh out overview.md + status.md with owner, goals, and risks",
                "  2. Draft architecture/implementation/testing docs before assigning sprint work",
                "  3. Run 'ph --scope system validate --quick' so docs stay lint-clean",
            ],
        ),
    ],
)
def test_feature_create_and_list(tmp_path: Path, scope: str, hint_lines: list[str]) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "list"]

    listed = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert listed.returncode == 0
    assert listed.stdout.splitlines() == [
        "📁 No features found",
        "💡 Create one with: ph feature create --name my-feature",
    ]

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "create", "--name", "feat-a"]
    created = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert created.returncode == 0
    assert created.stdout.splitlines()[-4:] == hint_lines

    base = tmp_path if scope == "project" else (tmp_path / ".project-handbook" / "system")
    feature_dir = base / "features" / "feat-a"
    assert (base / "features" / "implemented").exists()
    assert feature_dir.exists()

    expected_dirs = {"architecture", "implementation", "testing", "fdr", "decision-register"}
    assert expected_dirs.issubset({p.name for p in feature_dir.iterdir() if p.is_dir()})

    expected_files = {
        "overview.md",
        "status.md",
        "changelog.md",
        "risks.md",
        "architecture/ARCHITECTURE.md",
        "implementation/IMPLEMENTATION.md",
        "testing/TESTING.md",
    }
    assert expected_files.issubset(
        {str(p.relative_to(feature_dir)).replace(os.sep, "/") for p in feature_dir.rglob("*") if p.is_file()}
    )

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "feature", "list"]
    listed = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert listed.returncode == 0
    lines = listed.stdout.splitlines()
    assert lines[:2] == ["📋 FEATURES OVERVIEW", "=" * 60]
    assert any(line.startswith("📦 feat-a") for line in lines)


def test_feature_create_guardrail_rejects_system_scoped_names_in_project_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(
        tmp_path,
        routing_rules={"feature_name_prefixes_for_system_scope": ["handbook-", "ph-"]},
    )

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = [
        "ph",
        "--root",
        str(tmp_path),
        "--no-post-hook",
        "feature",
        "create",
        "--name",
        "handbook-test",
    ]
    created = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert created.returncode == 1
    assert created.stdout.strip() == "Use: ph --scope system feature create --name handbook-test"


def test_feature_list_prints_pnpm_make_preamble_when_package_json_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "feature", "list"]
    listed = subprocess.run(cmd, capture_output=True, text=True)
    assert listed.returncode == 0

    expected_root = str(tmp_path.resolve())
    assert listed.stdout.splitlines() == [
        "",
        f"> project-handbook@0.0.0 make {expected_root}",
        "> make -- feature-list",
        "",
        "📁 No features found",
        "💡 Create one with: ph feature create --name my-feature",
    ]


def test_feature_create_prints_pnpm_make_preamble_when_package_json_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    cmd = ["ph", "--root", str(tmp_path), "--no-post-hook", "feature", "create", "--name", "feat-a"]
    created = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert created.returncode == 0

    expected_root = str(tmp_path.resolve())
    assert created.stdout.splitlines()[:4] == [
        "",
        f"> project-handbook@0.0.0 make {expected_root}",
        "> make -- feature-create name\\=feat-a",
        "",
    ]
