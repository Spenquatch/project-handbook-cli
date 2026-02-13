from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_ph_root_for_migrate(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    data_root = config.parent
    (data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)

    (data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (data_root / "process" / "automation" / "system_scope_config.json").write_text(
        json.dumps(
            {
                "routing_rules": {
                    "feature_name_prefixes_for_system_scope": ["handbook-"],
                    "task_lane_prefixes_for_system_scope": ["handbook/"],
                    "adr_tags_triggering_system_scope": ["system-scope-tag"],
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_migrate_system_scope_moves_artifacts_and_emits_json_contract(tmp_path: Path) -> None:
    _write_ph_root_for_migrate(tmp_path)

    feature_dir = tmp_path / ".project-handbook" / "features" / "handbook-a"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "overview.md").write_text(
        "---\ntitle: handbook-a\ntags: [feature]\n---\n",
        encoding="utf-8",
    )

    adr_dir = tmp_path / ".project-handbook" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / "ADR-2099-system.md").write_text(
        "---\n"
        "title: ADR-2099 system\n"
        "tags: [system-scope-tag]\n"
        "links:\n"
        "  - ../features/handbook-a/overview.md\n"
        "---\n"
        "\n"
        "# ADR\n"
        "See [feature](../features/handbook-a/overview.md)\n",
        encoding="utf-8",
    )

    task_dir = tmp_path / ".project-handbook" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks" / "TASK-001-x"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "id: TASK-001\nlane: handbook/automation\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "migrate",
            "system-scope",
            "--confirm",
            "RESET",
            "--force",
            "true",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    data = json.loads(result.stdout)
    assert set(data.keys()) == {"moved", "skipped", "errors"}

    def _assert_rel_posix(value: str) -> None:
        assert value
        assert not value.startswith("/")
        assert "\\" not in value

    for entry in data["moved"]:
        _assert_rel_posix(entry["from"])
        _assert_rel_posix(entry["to"])
    for entry in data["skipped"]:
        _assert_rel_posix(entry["path"])
    for entry in data["errors"]:
        _assert_rel_posix(entry["path"])

    assert not (tmp_path / ".project-handbook" / "features" / "handbook-a").exists()
    assert (tmp_path / ".project-handbook" / "system" / "features" / "handbook-a").exists()

    assert not (tmp_path / ".project-handbook" / "adr" / "ADR-2099-system.md").exists()
    assert (tmp_path / ".project-handbook" / "system" / "adr" / "ADR-2099-system.md").exists()

    assert not task_dir.exists()
    assert (
        tmp_path / ".project-handbook" / "system" / "sprints" / "2099" / "SPRINT-2099-01-01" / "tasks" / "TASK-001-x"
    ).exists()


def test_migrate_system_scope_requires_exact_confirmations(tmp_path: Path) -> None:
    _write_ph_root_for_migrate(tmp_path)
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "migrate", "system-scope"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert result.stdout == ""
