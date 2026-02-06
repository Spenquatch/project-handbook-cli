from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


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


def _write_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("scope", "base_rel"),
    [
        ("project", ""),
        ("system", ".project-handbook/system"),
    ],
)
def test_sprint_archive_moves_directory_into_sprints_archive(tmp_path: Path, scope: str, base_rel: str) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"]
    planned = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert planned.returncode == 0

    cmd = ["ph", "--root", str(tmp_path)]
    if scope == "system":
        cmd += ["--scope", "system"]
    cmd += ["--no-post-hook", "sprint", "archive"]
    archived = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert archived.returncode == 0

    base = tmp_path if scope == "project" else (tmp_path / base_rel)
    original = base / "sprints" / "2099" / "SPRINT-2099-01-01"
    target = base / "sprints" / "archive" / "2099" / "SPRINT-2099-01-01"
    assert not original.exists()
    assert target.exists()


def test_sprint_archive_stdout_and_index_match_make_convention_for_seq_sprint(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-02-03T04:05:06.789012Z"
    import datetime as dt

    parsed = dt.datetime.fromisoformat(env["PH_FAKE_NOW"].replace("Z", "+00:00"))
    local_tz = dt.datetime.now().astimezone().tzinfo or dt.timezone.utc
    expected_today = parsed.astimezone(local_tz).date().isoformat()

    sprint_id = "SPRINT-SEQ-0004"
    sprint_dir = tmp_path / "sprints" / "SEQ" / sprint_id
    sprint_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "tasks").mkdir(exist_ok=True)
    (sprint_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                f"title: Sprint Plan - {sprint_id}",
                "type: sprint-plan",
                "date: 2099-01-23",
                f"sprint: {sprint_id}",
                "mode: bounded",
                "tags: [sprint, planning]",
                "---",
                "",
                f"# Sprint Plan: {sprint_id}",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    current_link = tmp_path / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    archived = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "archive", "--sprint", sprint_id],
        capture_output=True,
        text=True,
        env=env,
    )
    assert archived.returncode == 0

    target = (tmp_path / "sprints" / "archive" / "SEQ" / sprint_id).resolve()
    expected_stdout = (
        f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n"
        f"> ph sprint archive --sprint {sprint_id}\n\n"
        f"📦 Archived sprint {sprint_id} to {target}\n"
    )
    assert archived.stdout == expected_stdout

    assert not (tmp_path / "sprints" / "SEQ" / sprint_id).exists()
    assert target.exists()
    assert not current_link.exists()

    index_path = tmp_path / "sprints" / "archive" / "index.json"
    expected_index = {
        "sprints": [
            {
                "sprint": sprint_id,
                "archived_at": env["PH_FAKE_NOW"],
                "path": f"sprints/archive/SEQ/{sprint_id}",
                "start": "2099-01-23",
                "end": expected_today,
            }
        ]
    }
    assert index_path.read_text(encoding="utf-8") == json.dumps(expected_index, indent=2) + "\n"
