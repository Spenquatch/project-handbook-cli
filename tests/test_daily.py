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

def _expected_sprint_plan_link(*, scope_root: Path, daily_file: Path) -> str:
    target = scope_root / "sprints" / "current.md"
    year_dir = daily_file.parent.parent
    return os.path.relpath(str(target), str(year_dir)).replace(os.sep, "/")


def test_daily_generate_skips_weekends_unless_forced(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-03"  # Saturday

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "daily", "generate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert not (tmp_path / ".project-handbook" / "status" / "daily" / "2099" / "01" / "03.md").exists()

    forced = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "daily", "generate", "--force"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert forced.returncode == 0
    assert (tmp_path / ".project-handbook" / "status" / "daily" / "2099" / "01" / "03.md").exists()


def test_daily_generate_writes_under_scope_root(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-05"  # Monday

    project = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "daily", "generate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert project.returncode == 0
    project_root = tmp_path / ".project-handbook"
    project_file = project_root / "status" / "daily" / "2099" / "01" / "05.md"
    assert project_file.exists()
    project_text = project_file.read_text(encoding="utf-8")
    assert (
        f"links: [{_expected_sprint_plan_link(scope_root=project_root, daily_file=project_file)}]"
        in project_text
    )

    system = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "daily", "generate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert system.returncode == 0
    system_file = tmp_path / ".project-handbook" / "system" / "status" / "daily" / "2099" / "01" / "05.md"
    assert system_file.exists()
    system_text = system_file.read_text(encoding="utf-8")
    system_root = tmp_path / ".project-handbook" / "system"
    assert f"links: [{_expected_sprint_plan_link(scope_root=system_root, daily_file=system_file)}]" in system_text
