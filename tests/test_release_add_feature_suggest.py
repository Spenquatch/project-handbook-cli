from __future__ import annotations

import os
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


def test_release_add_feature_updates_yaml_and_suggest_lists_feature(tmp_path: Path) -> None:
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

    feature_dir = tmp_path / "features" / "feat-a"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "status.md").write_text("Stage: developing\n", encoding="utf-8")

    add_feature = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "add-feature",
            "--release",
            "v1.2.3",
            "--feature",
            "feat-a",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add_feature.returncode == 0

    features_yaml = (tmp_path / "releases" / "v1.2.3" / "features.yaml").read_text(encoding="utf-8")
    assert "  feat-a:" in features_yaml
    assert "    type: regular" in features_yaml
    assert "    critical_path: False" in features_yaml

    suggest = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "release", "suggest", "--version", "v1.2.3"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert suggest.returncode == 0
    expected = "\n".join(
        [
            "💡 SUGGESTED FEATURES FOR v1.2.3",
            "=" * 50,
            f"📦 {'feat-a':<20} Stage: developing - Good candidate",
            "",
        ]
    )
    assert suggest.stdout == expected


def test_release_add_feature_rejects_system_scope(tmp_path: Path) -> None:
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
            "suggest",
            "--version",
            "v1.2.3",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "Releases are project-scope only. Use: ph --scope project release ..."


def test_release_add_feature_matches_legacy_duplication_bug(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    (tmp_path / "releases" / "v0.0.1").mkdir(parents=True, exist_ok=True)
    features_path = tmp_path / "releases" / "v0.0.1" / "features.yaml"
    features_path.write_text(
        "\n".join(
            [
                "# Feature assignments for v0.0.1",
                "# Auto-managed by release commands",
                "",
                "version: v0.0.1",
                "timeline_mode: sprint_slots",
                "start_sprint_slot: 1",
                "end_sprint_slot: 2",
                "planned_sprints: 2",
                "",
                "features:",
                "  feat-one:",
                "    type: regular",
                "    priority: P1",
                "    status: planned",
                "    completion: 0",
                "    critical_path: False",
                "",
                "  feat-two:",
                "    type: regular",
                "    priority: P1",
                "    status: planned",
                "    completion: 0",
                "    critical_path: True",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    add_feature = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--no-post-hook",
            "release",
            "add-feature",
            "--release",
            "v0.0.1",
            "--feature",
            "feat-new",
            "--epic",
            "--critical",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert add_feature.returncode == 0
    assert add_feature.stdout.strip() == "✅ Added feat-new to release v0.0.1"

    expected = "\n".join(
        [
            "# Feature assignments for v0.0.1",
            "# Auto-managed by release commands",
            "",
            "version: v0.0.1",
            "timeline_mode: sprint_slots",
            "start_sprint_slot: 1",
            "end_sprint_slot: 2",
            "planned_sprints: 2",
            "",
            "features:",
            "  feat-one:",
            "    type: regular",
            "    priority: P1",
            "    status: planned",
            "    completion: 0",
            "    critical_path: False",
            "",
            "  feat-two:",
            "    type: regular",
            "    priority: P1",
            "    status: planned",
            "    completion: 0",
            "    critical_path: True",
            "",
            "  feat-new:",
            "    type: epic",
            "    priority: P1",
            "    status: planned",
            "    completion: 0",
            "    critical_path: True",
            "",
            "  feat-two:",
            "    type: regular",
            "    priority: P1",
            "    status: planned",
            "    completion: 0",
            "    critical_path: True",
        ]
    )
    actual_bytes = features_path.read_bytes()
    assert not actual_bytes.endswith(b"\n")
    assert actual_bytes.decode("utf-8") == expected
