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


def test_release_close_updates_plan_and_creates_changelog(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = subprocess.run(
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
            "--start-sprint",
            "SPRINT-2099-01-01",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0

    plan_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "plan.md"
    assert "# Release v1.2.3" in plan_path.read_text(encoding="utf-8")

    # Release timeline is `sprint_ids` (start_sprint + planned_sprints). Closing is blocked unless all
    # planned sprints are archived under sprints/archive/.
    (tmp_path / ".project-handbook" / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01").mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / ".project-handbook" / "sprints" / "archive" / "2099" / "SPRINT-2099-01-08").mkdir(
        parents=True, exist_ok=True
    )

    (tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "features.yaml").write_text(
        "\n".join(
            [
                "version: v1.2.3",
                "",
                "features:",
                "  alpha:",
                "    critical_path: true",
                "  beta:",
                "    critical_path: false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    close = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "close", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert close.returncode == 0
    assert close.stdout == "\n".join(
        [
            "✅ Release v1.2.3 closed",
            f"📋 Generated changelog: {tmp_path}/.project-handbook/releases/v1.2.3/changelog.md",
            f"📝 Updated plan status: {tmp_path}/.project-handbook/releases/v1.2.3/plan.md",
            "📈 Ready for deployment",
            "",
        ]
    )

    changelog_path = tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "changelog.md"
    assert changelog_path.exists()
    assert changelog_path.read_text(encoding="utf-8") == "\n".join(
        [
            "---",
            "title: Release v1.2.3 Changelog",
            "type: changelog",
            "version: v1.2.3",
            "date: 2099-01-01",
            "tags: [changelog, release]",
            "links: []",
            "---",
            "",
            "# Changelog: v1.2.3",
            "",
            "## Release Summary",
            "Released on January 01, 2099",
            "",
            "## Features Delivered",
            "- **alpha**: Feature description",
            "- **beta**: Feature description",
            "",
            "",
            "## Tasks Completed",
            "*Auto-generated from sprint tasks*",
            "",
            "## Breaking Changes",
            "- None",
            "",
            "## Migration Guide",
            "- No migration required",
            "",
            "## Known Issues",
            "- None",
            "",
            "## Contributors",
            "- Team members who contributed",
            "",
        ]
    )

    updated_plan = plan_path.read_text(encoding="utf-8")
    assert "status: delivered" in updated_plan
    assert "delivered_sprint: SPRINT-2099-01-08" in updated_plan
    assert "delivered_date: 2099-01-01" in updated_plan
    assert "> Release status: **delivered** (marked delivered in `SPRINT-2099-01-08`, on 2099-01-01)." in updated_plan


def test_release_close_clears_current_release_pointer_when_current(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    plan = subprocess.run(
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
            "1",
            "--start-sprint",
            "SPRINT-2099-01-01",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0

    (tmp_path / ".project-handbook" / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01").mkdir(
        parents=True, exist_ok=True
    )

    # Simulate active current release pointer (symlink + txt).
    releases_dir = tmp_path / ".project-handbook" / "releases"
    current_link = releases_dir / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("v1.2.3"))
    (releases_dir / "current.txt").write_text("v1.2.3\n", encoding="utf-8")

    (tmp_path / ".project-handbook" / "releases" / "v1.2.3" / "features.yaml").write_text(
        "\n".join(
            [
                "version: v1.2.3",
                "",
                "features:",
                "  alpha:",
                "    critical_path: true",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    close = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "close", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert close.returncode == 0
    assert close.stdout.splitlines() == [
        "✅ Release v1.2.3 closed",
        f"📋 Generated changelog: {tmp_path}/.project-handbook/releases/v1.2.3/changelog.md",
        f"📝 Updated plan status: {tmp_path}/.project-handbook/releases/v1.2.3/plan.md",
        "⭐ Cleared current release pointer: v1.2.3",
        "📈 Ready for deployment",
    ]
    assert not (releases_dir / "current").exists()
    assert not (releases_dir / "current.txt").exists()


def test_release_close_rejects_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "release",
            "close",
            "--version",
            "v1.2.3",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Releases are project-scope only. Use: ph --scope project release ..."
