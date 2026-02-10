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


def test_release_plan_creates_files_and_hints(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    plan_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "plan.md"
    progress_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "progress.md"
    features_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "features.yaml"
    assert plan_path.exists()
    assert progress_path.exists()
    assert features_path.exists()

    current_link = tmp_path / ".project-handbook" / "releases" / "current"
    assert not current_link.exists()

    plan_text = plan_path.read_text(encoding="utf-8")
    assert "date: 2099-01-01" in plan_text
    assert "timeline_mode: sprint_slots" in plan_text
    assert "planned_sprints: 2" in plan_text
    assert "sprint_slots: [1, 2]" in plan_text
    assert "## Slot Plans" in plan_text
    assert "### Slot 1" in plan_text
    assert "### Slot 2" in plan_text
    assert plan_text.count("#### Goal / Purpose") == 2
    assert plan_text.count("#### Scope boundaries (in/out)") == 2
    assert plan_text.count("#### Intended gate(s)") == 2
    assert plan_text.count("#### Enablement") == 2

    features_text = features_path.read_text(encoding="utf-8")
    assert "timeline_mode: sprint_slots" in features_text
    assert "start_sprint_slot: 1" in features_text
    assert "end_sprint_slot: 2" in features_text

    progress_text = progress_path.read_text(encoding="utf-8")
    assert "- **Slot 1**: ⭕ Planned" in progress_text
    assert "- **Slot 2**: ⭕ Planned" in progress_text

    resolved_release_dir = (tmp_path / ".project-handbook" / "releases" / "v1.2.3").resolve()
    resolved_plan_path = (tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "plan.md").resolve()
    expected_stdout = "\n".join(
        [
            "✅ Created release plan: v1.2.3",
            f"📁 Location: {resolved_release_dir}",
            "📅 Timeline: 2 sprint slot(s) (decoupled from calendar dates)",
            "📝 Next steps:",
            f"   1. Edit {resolved_plan_path} to define release goals",
            "   2. Add features: ph release add-feature --release v1.2.3 --feature feature-name",
            "   3. Activate when ready: ph release activate --release v1.2.3",
            "   4. Review timeline and adjust if needed",
            "Release plan scaffold created under .project-handbook/releases/<version>/plan.md",
            "  - Assign features via 'ph release add-feature --release <version> --feature <name>'",
            "  - Activate when ready via 'ph release activate --release <version>'",
            "  - Confirm sprint alignment via 'ph release status' (requires an active release)",
            "  - Run 'ph validate --quick' before sharing externally",
            "",
        ]
    )
    assert result.stdout == expected_stdout


def test_release_plan_activate_sets_current(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "plan", "--version", "v1.2.3", "--activate"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    current_link = tmp_path / ".project-handbook" / "releases" / "current"
    assert current_link.is_symlink()
    assert current_link.readlink().name == "v1.2.3"


def test_release_plan_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--scope", "system", "--no-post-hook", "release", "plan"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Releases are project-scope only. Use: ph --scope project release ..."


def test_release_plan_does_not_overwrite_existing_plan_md(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    plan_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "plan.md"
    plan_path.write_text("custom-plan\n", encoding="utf-8")

    env["PH_FAKE_TODAY"] = "2099-01-02"
    rerun = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "plan",
            "--version",
            "v1.2.3",
            "--sprints",
            "2",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert rerun.returncode == 0
    assert plan_path.read_text(encoding="utf-8") == "custom-plan\n"
