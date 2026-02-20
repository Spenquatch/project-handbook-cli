from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    ph_data_root = config.parent
    (ph_data_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_data_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_data_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_data_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_data_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


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
    ph_data_root = tmp_path / ".project-handbook"

    # Seed backlog + parking-lot so the guardrail refresh prints stable counts.
    bug_dir = ph_data_root / "backlog" / "bugs" / "BUG-001"
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

    parking_dir = ph_data_root / "parking-lot" / "features" / "PARK-001"
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
    sprint_dir = ph_data_root / "sprints" / "SEQ" / sprint_id
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
        task_type_line = "task_type: sprint-gate" if task_num == "001" else "task_type: implementation"
        (task_dir / "task.yaml").write_text(
            "\n".join(
                [
                    f"id: TASK-{task_num}",
                    f"title: Task {task_num}",
                    task_type_line,
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

    current_link = ph_data_root / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    (ph_data_root / "releases" / "v0.6.0").mkdir(parents=True, exist_ok=True)

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
    archived_dir = resolved_root / ".project-handbook" / "sprints" / "archive" / "SEQ" / sprint_id
    retro_path = resolved_root / ".project-handbook" / "sprints" / "SEQ" / sprint_id / "retrospective.md"
    progress_path = resolved_root / ".project-handbook" / "releases" / "v0.6.0" / "progress.md"

    expected_stdout = (
        f"\n> project-handbook@0.0.0 ph {tmp_path.resolve()}\n> ph sprint close\n\n"
        "📊 Updated backlog index: 1 items\n"
        "📊 Updated parking lot index: 1 items\n"
        f"Created retrospective: {retro_path}\n"
        "Sprint velocity: 3/3 points (100%)\n"
        f"📦 Archived sprint {sprint_id} to {archived_dir}\n"
        f"📝 Updated: {progress_path}\n"
        "📦 Release progress refreshed for v0.6.0.\n"
        "Deterministic sprint close checklist:\n"
        "Pre-close (recommended):\n"
        "- ph sprint status\n"
        "- ph sprint burndown\n"
        "- ph task list\n"
        "- ph feature summary\n"
        "- ph release status\n"
        "- ph validate --quick\n"
        "Optional (evidence bundle):\n"
        "- ph pre-exec lint\n"
        "- ph pre-exec audit\n"
        "Post-close (recommended):\n"
        "- ph status\n"
        "- ph validate --quick\n"
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

    archive_index = json.loads((ph_data_root / "sprints" / "archive" / "index.json").read_text(encoding="utf-8"))
    entry = next(e for e in archive_index.get("sprints", []) if e.get("sprint") == sprint_id)
    assert entry["archived_at"] == env["PH_FAKE_NOW"]
    assert entry["path"] == f"sprints/archive/SEQ/{sprint_id}"
    assert entry["start"] == "2099-01-23"
    assert entry["end"] == expected_today

    retro_text = (archived_dir / "retrospective.md").read_text(encoding="utf-8")
    assert f"date: {expected_today}\n" in retro_text
    assert _extract_completed_task_lines(retro_text) == expected_done_lines


def test_sprint_close_prints_release_close_hint_when_last_slot_completes(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    # Seed backlog + parking-lot so the guardrail refresh prints stable counts.
    bug_dir = ph_data_root / "backlog" / "bugs" / "BUG-001"
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

    parking_dir = ph_data_root / "parking-lot" / "features" / "PARK-001"
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

    version = "v1.2.3"
    release_dir = ph_data_root / "releases" / version
    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                f"title: Release Plan - {version}",
                "type: release-plan",
                "date: 2099-01-01",
                f"version: {version}",
                "timeline_mode: sprint_slots",
                "planned_sprints: 1",
                "sprint_slots: [1]",
                "---",
                "",
                f"# Release {version}",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    sprint_id = "SPRINT-SEQ-0001"
    sprint_dir = ph_data_root / "sprints" / "SEQ" / sprint_id
    tasks_dir = sprint_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "plan.md").write_text(
        "\n".join(
            [
                "---",
                f"title: Sprint Plan - {sprint_id}",
                "type: sprint-plan",
                "date: 2099-01-01",
                f"sprint: {sprint_id}",
                "mode: bounded",
                f"release: {version}",
                "release_sprint_slot: 1",
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

    gate_dir = tasks_dir / "TASK-001-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Gate task",
                "task_type: sprint-gate",
                "status: done",
                "story_points: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    current_link = ph_data_root / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-02-03T04:05:06.789012Z"

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0

    hint = f"Consider closing release: ph release close --version {version}\n"
    assert res.stdout.count(hint) == 1
    assert "Deterministic sprint close checklist:\n" in res.stdout
    assert res.stdout.index(hint) < res.stdout.index("Deterministic sprint close checklist:\n")
    assert res.stdout.index("Deterministic sprint close checklist:\n") < res.stdout.index(
        "Sprint closed! Next steps:\n"
    )


def test_sprint_close_blocks_when_sprint_gates_missing(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    sprint_id = "SPRINT-SEQ-0005"
    sprint_dir = ph_data_root / "sprints" / "SEQ" / sprint_id
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

    task_dir = tasks_dir / "TASK-001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Task 001",
                "task_type: implementation",
                "status: done",
                "story_points: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    current_link = ph_data_root / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert res.returncode == 1
    assert "❌ Sprint close blocked: sprint gates missing/incomplete." in res.stdout
    assert "No sprint gate tasks found (task_type: sprint-gate)." in res.stdout

    assert current_link.exists()
    assert sprint_dir.exists()
    assert not (sprint_dir / "retrospective.md").exists()
    assert not (ph_data_root / "sprints" / "archive" / "SEQ" / sprint_id).exists()


def test_sprint_close_blocks_when_any_sprint_gate_incomplete(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    sprint_id = "SPRINT-SEQ-0006"
    sprint_dir = ph_data_root / "sprints" / "SEQ" / sprint_id
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

    gate_dir = tasks_dir / "TASK-001-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Gate task",
                "task_type: sprint-gate",
                "status: doing",
                "story_points: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    current_link = ph_data_root / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    assert res.returncode == 1
    assert "❌ Sprint close blocked: sprint gates missing/incomplete." in res.stdout
    assert "sprint gate task(s) are not status: done." in res.stdout
    assert "TASK-001: Gate task (status: doing)" in res.stdout

    assert current_link.exists()
    assert sprint_dir.exists()
    assert not (ph_data_root / "sprints" / "archive" / "SEQ" / sprint_id).exists()


def test_sprint_close_override_allows_close_without_gates(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_package_json(tmp_path)
    ph_data_root = tmp_path / ".project-handbook"

    sprint_id = "SPRINT-SEQ-0007"
    sprint_dir = ph_data_root / "sprints" / "SEQ" / sprint_id
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

    task_dir = tasks_dir / "TASK-001"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Task 001",
                "task_type: implementation",
                "status: done",
                "story_points: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    current_link = ph_data_root / "sprints" / "current"
    current_link.parent.mkdir(parents=True, exist_ok=True)
    current_link.symlink_to(Path("SEQ") / sprint_id)

    env = dict(os.environ)
    env["PH_SPRINT_CLOSE_ALLOW_INCOMPLETE_GATES"] = "1"
    res = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "close"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0
    assert "skipping sprint gate checks (PH_SPRINT_CLOSE_ALLOW_INCOMPLETE_GATES=1)." in res.stdout
    assert (ph_data_root / "sprints" / "archive" / "SEQ" / sprint_id).exists()
