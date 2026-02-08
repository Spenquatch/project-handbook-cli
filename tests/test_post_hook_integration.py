from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    ph_project_root = ph_root / ".project-handbook"
    config = ph_project_root / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_project_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_doctor_success_runs_post_hook_validation(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "doctor"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_no_validate_flag_skips_auto_validation(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-validate"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (tmp_path / ".project-handbook" / "history.log").exists()
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_env_var_skips_post_hook_entirely(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_SKIP_POST_HOOK"] = "1"
    result = subprocess.run(
        ["ph", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert not (tmp_path / ".project-handbook" / "history.log").exists()
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()
