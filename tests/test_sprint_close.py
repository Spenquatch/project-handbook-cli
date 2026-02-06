from __future__ import annotations

import json
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


def _write_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _extract_completed_task_lines(retro_text: str) -> list[str]:
    lines = retro_text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line.strip() == "## Completed Tasks":
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.startswith("- ✅ "):
                out.append(line)
    return out


def test_sprint_close_stdout_archive_and_retrospective_match_make_convention(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)

    # Seed backlog + parking-lot so the guardrail refresh prints stable counts.
    bug_dir = tmp_path / "backlog" / "bugs" / "BUG-001"
    bug_dir.mkdir(parents=True, exist_ok=True)
    (bug_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "title: Bug 001",
                "severity: P1",
                "created: 2099-01-01",
                "---",
                "",
                "Body",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parking_dir = tmp_path / "parking-lot" / "features" / "PARK-001"
    parking_dir.mkdir(parents=True, exist_ok=True)
    (parking_dir / "README.md").write_text(
        "\n".join(
            [
                "---",
                "title: Parking 001",
                "type: features",
                "created: 2099-01-02",
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Seed a bounded SEQ sprint + current pointer.
    sprint_id = "SPRINT-SEQ-0004"
    sprint_dir = tmp_path / "sprints" / "SEQ" / sprint_id
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                f"title: Sprint Plan - {sprint_id}",
                "type: sprint-plan",
                "date: 2099-01-23",
                f"sprint: {sprint_id}",
                "mode: bounded",
                "release: v0.6.0",
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

    # Create tasks in a non-sorted order; legacy retrospective follows raw iterdir order.
    created_task_dirs: list[str] = [
        "TASK-003-third",
        "TASK-001-first",
        "TASK-002-second",
    ]
    for dirname in created_task_dirs:
        task_dir = tasks_dir / dirname
        task_dir.mkdir(parents=True, exist_ok=True)
        task_num = dirname.split("-", 2)[1]
        (task_dir / "task.yaml").write_text(
            "\n".join(
                [
                    f"id: TASK-{task_num}",
                    f"title: Task {task_num}",
                    "status: done",
                    "story_points: 1",
                    "depends_on: [FIRST_TASK]",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    expected_done_lines: list[str] = []
    for entry in tasks_dir.iterdir():
        if not entry.is_dir():
            continue
        meta = (entry / "task.yaml").read_text(encoding="utf-8")
        task_id = ""
        title = ""
        for raw in meta.splitlines():
            if raw.startswith("id:"):
                task_id = raw.split(":", 1)[1].strip()
            if raw.startswith("title:"):
                title = raw.split(":", 1)[1].strip()
        expected_done_lines.append(f"- ✅ {task_id}: {title}")

    current_link = tmp_path / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    (tmp_path / "releases" / "v0.6.0").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-02-03T04:05:06.789012Z"
    env["PH_FAKE_TODAY"] = "2099-02-03"  # should be ignored for retrospective date (legacy uses local today)

    import datetime as dt

    parsed = dt.datetime.fromisoformat(env["PH_FAKE_NOW"].replace("Z", "+00:00"))
    local_tz = dt.datetime.now().astimezone().tzinfo or dt.timezone.utc
    expected_today = parsed.astimezone(local_tz).date().isoformat()

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0

    resolved_root = tmp_path.resolve()
    archived_dir = resolved_root / "sprints" / "archive" / "SEQ" / sprint_id
    retro_path = resolved_root / "sprints" / "SEQ" / sprint_id / "retrospective.md"
    progress_path = resolved_root / "releases" / "v0.6.0" / "progress.md"

    expected_stdout = (
        f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph sprint close\n\n"
        "📊 Updated backlog index: 1 items\n"
        "📊 Updated parking lot index: 1 items\n"
        f"Created retrospective: {retro_path}\n"
        "Sprint velocity: 3/3 points (100%)\n"
        f"📦 Archived sprint {sprint_id} to {archived_dir}\n"
        f"📝 Updated: {progress_path}\n"
        "📦 Release progress refreshed for v0.6.0.\n"
        "Sprint closed! Next steps:\n"
        "  1. Share the new retrospective and velocity summary\n"
        "  2. Update roadmap/releases with completed scope\n"
        "  3. Run 'ph status' so status/current_summary.md reflects the close-out\n"
        "  4. Kick off the next sprint via 'ph sprint plan' when ready\n"
        "  5. Capture any loose ends inside parking lot or backlog\n"
    )
    assert res.stdout == expected_stdout

    assert not current_link.exists()
    assert archived_dir.exists()

    archive_index = json.loads((tmp_path / "sprints" / "archive" / "index.json").read_text(encoding="utf-8"))
    entry = next(e for e in archive_index.get("sprints", []) if e.get("sprint") == sprint_id)
    assert entry["archived_at"] == env["PH_FAKE_NOW"]
    assert entry["path"] == f"sprints/archive/SEQ/{sprint_id}"
    assert entry["start"] == "2099-01-23"
    assert entry["end"] == expected_today

    retro_text = (archived_dir / "retrospective.md").read_text(encoding="utf-8")
    assert f"date: {expected_today}\n" in retro_text
    assert _extract_completed_task_lines(retro_text) == expected_done_lines
